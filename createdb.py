import os
from app import db, app, Priority, Category

def create_database():
    # Get the absolute path to the database file
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    db_path = os.path.join(instance_dir, 'task_db.db')
    
    # Create instance directory if it doesn't exist
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"Created instance directory at: {instance_dir}")

    print(f"Attempting to create database at: {db_path}")

    try:
        # Create all database tables
        with app.app_context():
            db.create_all()
            
            # Add default priorities if they don't exist
            priorities = [
                {'name': 'Low', 'level': 1},
                {'name': 'Medium', 'level': 2},
                {'name': 'High', 'level': 3}
            ]
            
            for p in priorities:
                if not Priority.query.filter_by(name=p['name']).first():
                    priority = Priority(name=p['name'], level=p['level'])
                    db.session.add(priority)

            # Add default categories if they don't exist
            categories = ['Work', 'Personal', 'Shopping', 'Study']
            for cat_name in categories:
                if not Category.query.filter_by(name=cat_name).first():
                    category = Category(name=cat_name)
                    db.session.add(category)

            # Commit the changes
            db.session.commit()
            print("Successfully created and initialized database!")
            return True
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        return False

if __name__ == "__main__":
    create_database() 
