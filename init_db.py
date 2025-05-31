from app import app, db, User, Todo, Priority
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Drop all existing tables and create new ones
        db.drop_all()
        db.create_all()
        
        print("Creating default priorities...")
        # Add default priorities
        priorities = [
            Priority(name='Low', level=1),
            Priority(name='Medium', level=2),
            Priority(name='High', level=3)
        ]
        for priority in priorities:
            db.session.add(priority)
        
        print("Creating admin user...")
        # Create admin user
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123', method='pbkdf2:sha256')
        )
        db.session.add(admin)
        
        try:
            db.session.commit()
            print("Database initialized successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing database: {e}")

if __name__ == '__main__':
    init_db() 