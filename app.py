from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages, jsonify, abort, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps # Used for the login_required decorator
import os
from flask_login import login_user, login_required, logout_user, current_user, LoginManager, UserMixin
from flask_wtf.csrf import CSRFProtect
from flask_wtf import FlaskForm

# Initialize the Flask application
app = Flask(__name__)

# Create instance directory if it doesn't exist
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Configure the database URI for SQLite with absolute path
db_path = os.path.join(instance_path, 'task_db.db')
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

# Set a secret key for flashing messages and session management
app.config["SECRET_KEY"] = "your_super_secret_key_here_a_much_longer_and_random_string_for_security"

# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "You need to log in"
login_manager.login_message_category = "error"

# Create a basic form for CSRF token
class BaseForm(FlaskForm):
    pass

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

# Priority Model
class Priority(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    level = db.Column(db.Integer, nullable=False, unique=True)

    def __repr__(self):
        return f"<Priority {self.name} (Level: {self.level})>"

# Todo Model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(
        db.DateTime, default=lambda: datetime.now(pytz.timezone("Asia/Manila"))
    )
    due_date = db.Column(db.Date, nullable=True)

    # Foreign key for Priority
    priority_id = db.Column(db.Integer, db.ForeignKey('priority.id'), nullable=True)
    priority = db.relationship('Priority', backref='todos')

    # Foreign key for User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('todos', lazy=True))

    def __repr__(self):
        return f"<Task {self.id}>"

def parse_date_from_form(date_string):
    if date_string:
        try:
            return datetime.strptime(date_string, '%Y-%m-%d').date()
        except ValueError:
            return None
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = BaseForm()  # Create form instance for CSRF token
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()

        if not username or not password or not confirm_password:
            flash("All fields are required.", "error")
            return render_template('register.html', form=form)
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('register.html', form=form)
        
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose a different one.", "error")
            return render_template('register.html', form=form)
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred during registration: {e}", "error")
            return render_template('register.html', form=form)
            
    return render_template('register.html', form=form, messages=get_flashed_messages(with_categories=True))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = BaseForm()  # Create form instance for CSRF token
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "error")
            return render_template('login.html', form=form)
    
    return render_template('login.html', form=form, messages=get_flashed_messages(with_categories=True))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = BaseForm()  # Create form instance for CSRF token
    if request.method == "POST":
        task_content = request.form["content"].strip()
        due_date_str = request.form.get("due_date")
        priority_id = request.form.get("priority_id")

        if not task_content:
            flash("Task content cannot be empty!", "error")
            return redirect("/")
        if due_date_str and not parse_date_from_form(due_date_str):
            flash("Invalid due date format. Please use YYYY-MM-DD format.", "error")
            return redirect("/")

        # Create new task
        new_task = Todo(
            content=task_content,
            due_date=parse_date_from_form(due_date_str),
            user_id=current_user.id
        )

        # Add priority if provided
        if priority_id:
            priority = Priority.query.get(priority_id)
            if priority:
                new_task.priority = priority

        try:
            db.session.add(new_task)
            db.session.commit()
            flash("Task added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding task: {str(e)}", "error")

        return redirect(url_for('index'))

    # GET request - display tasks with filter
    filter_type = request.args.get('filter', '')
    tasks_query = Todo.query.filter_by(user_id=current_user.id)
    
    if filter_type == 'completed':
        tasks_query = tasks_query.filter_by(completed=1)
    elif filter_type == 'incomplete':
        tasks_query = tasks_query.filter_by(completed=0)
    
    tasks = tasks_query.order_by(Todo.date_created.desc()).all()
    priorities = Priority.query.order_by(Priority.level).all()
    
    return render_template(
        'index.html',
        tasks=tasks,
        priorities=priorities,
        current_filter=filter_type,
        form=form  # Pass form to template
    )

@app.route("/toggle_task/<int:id>", methods=["POST"])
@login_required
def toggle_task(id):
    task = Todo.query.get_or_404(id)
    
    # Ensure user owns this task
    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        task.completed = 1 if task.completed == 0 else 0
        db.session.commit()
        return jsonify({
            "success": True,
            "completed": task.completed == 1
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/init-db')
def init_db():
    try:
        # Create all tables
        db.create_all()

        # First, clear existing priorities and categories to avoid conflicts
        Priority.query.delete()
        db.session.commit()

        # Add default priorities
        priorities = [
            {'name': 'Low', 'level': 1},
            {'name': 'Medium', 'level': 2},
            {'name': 'High', 'level': 3}
        ]
        
        for p in priorities:
            priority = Priority(name=p['name'], level=p['level'])
            db.session.add(priority)

        # Add default admin user if it doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256')
            )
            db.session.add(admin_user)

        db.session.commit()
        return "Database initialized successfully! Default admin credentials: username='admin', password='admin123'"
    except Exception as e:
        db.session.rollback()
        return f"Error initializing database: {str(e)}"

@app.route("/update_task/<int:id>", methods=["GET", "POST"])
@login_required
def update_task(id):
    form = BaseForm()  # Create form instance for CSRF token
    task = Todo.query.get_or_404(id)
    
    # Ensure user owns this task
    if task.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        task_content = request.form["content"].strip()
        due_date_str = request.form.get("due_date")
        priority_id = request.form.get("priority_id")

        if not task_content:
            flash("Task content cannot be empty!", "error")
            return redirect(url_for('index'))

        try:
            task.content = task_content
            task.due_date = parse_date_from_form(due_date_str)
            
            if priority_id:
                priority = Priority.query.get(priority_id)
                if priority:
                    task.priority = priority
                else:
                    task.priority = None
            else:
                task.priority = None

            db.session.commit()
            flash("Task updated successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating task: {str(e)}", "error")
            return redirect(url_for('index'))

    priorities = Priority.query.order_by(Priority.level).all()
    return render_template(
        'update_task.html',
        task=task,
        priorities=priorities,
        form=form  # Pass form to template
    )

@app.route("/delete_task/<int:id>", methods=["POST"])
@login_required
def delete_task(id):
    task = Todo.query.get_or_404(id)
    
    # Ensure user owns this task
    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully!", "success")
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Add this route to handle AJAX requests for task details
@app.route("/get_task/<int:id>")
@login_required
def get_task(id):
    task = Todo.query.get_or_404(id)
    
    # Ensure user owns this task
    if task.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "id": task.id,
        "content": task.content,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "priority_id": task.priority_id
    })

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = BaseForm()
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            new_username = request.form.get('username').strip()
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Verify current password
            if not check_password_hash(current_user.password_hash, current_password):
                flash("Current password is incorrect.", "error")
                return redirect(url_for('settings'))

            try:
                # Update username if changed
                if new_username != current_user.username:
                    if User.query.filter_by(username=new_username).first():
                        flash("Username already exists.", "error")
                        return redirect(url_for('settings'))
                    current_user.username = new_username

                # Update password if provided
                if new_password:
                    if new_password != confirm_password:
                        flash("New passwords do not match.", "error")
                        return redirect(url_for('settings'))
                    current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')

                db.session.commit()
                flash("Profile updated successfully!", "success")
                return redirect(url_for('settings'))

            except Exception as e:
                db.session.rollback()
                flash(f"Error updating profile: {str(e)}", "error")
                return redirect(url_for('settings'))

        elif action == 'delete_account':
            password = request.form.get('confirm_delete_password')
            
            if not check_password_hash(current_user.password_hash, password):
                flash("Incorrect password. Account not deleted.", "error")
                return redirect(url_for('settings'))

            try:
                # Delete all user's tasks
                Todo.query.filter_by(user_id=current_user.id).delete()
                
                # Delete the user
                db.session.delete(current_user)
                db.session.commit()
                
                logout_user()
                flash("Your account has been deleted successfully.", "success")
                return redirect(url_for('login'))

            except Exception as e:
                db.session.rollback()
                flash(f"Error deleting account: {str(e)}", "error")
                return redirect(url_for('settings'))

    return render_template('settings.html', form=form)

if __name__ == "__main__":
    app.run(debug=True)
    