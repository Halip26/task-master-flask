import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, db, User, Todo
from werkzeug.security import generate_password_hash, check_password_hash

@pytest.fixture
def client():
    app.config.from_object('config_test')
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def auth_client(client):
    # Create and login a test user
    user = User(
        username='testuser',
        password_hash=generate_password_hash('testpass123')
    )
    db.session.add(user)
    db.session.commit()
    
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    }, follow_redirects=True)
    
    return client

def test_register_success(client):
    """Test successful user registration"""
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Registration successful!" in response.data
    
    # Verify user was created in database
    user = User.query.filter_by(username='newuser').first()
    assert user is not None
    assert check_password_hash(user.password_hash, 'password123')

def test_register_existing_username(client):
    """Test registration with existing username"""
    # Create initial user
    user = User(
        username='existinguser',
        password_hash=generate_password_hash('password123')
    )
    db.session.add(user)
    db.session.commit()
    
    # Try to register with same username
    response = client.post('/register', data={
        'username': 'existinguser',
        'password': 'newpass123',
        'confirm_password': 'newpass123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Username already exists" in response.data

def test_register_password_mismatch(client):
    """Test registration with mismatched passwords"""
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'password123',
        'confirm_password': 'password456'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Passwords do not match" in response.data

def test_login_success(client):
    """Test successful login"""
    # Create user
    user = User(
        username='loginuser',
        password_hash=generate_password_hash('password123')
    )
    db.session.add(user)
    db.session.commit()
    
    response = client.post('/login', data={
        'username': 'loginuser',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Welcome back" in response.data

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/login', data={
        'username': 'nonexistent',
        'password': 'wrongpass'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data

def test_update_profile_success(auth_client):
    """Test successful profile update"""
    response = auth_client.post('/settings', data={
        'action': 'update_profile',
        'username': 'updateduser',
        'current_password': 'testpass123',
        'new_password': 'newpass123',
        'confirm_password': 'newpass123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Profile updated successfully" in response.data
    
    # Verify changes in database
    user = User.query.filter_by(username='updateduser').first()
    assert user is not None
    assert check_password_hash(user.password_hash, 'newpass123')

def test_update_profile_wrong_password(auth_client):
    """Test profile update with wrong current password"""
    response = auth_client.post('/settings', data={
        'action': 'update_profile',
        'username': 'updateduser',
        'current_password': 'wrongpass',
        'new_password': 'newpass123',
        'confirm_password': 'newpass123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Current password is incorrect" in response.data

def test_update_profile_existing_username(auth_client):
    """Test profile update with existing username"""
    # Create another user
    other_user = User(
        username='otheruser',
        password_hash=generate_password_hash('password123')
    )
    db.session.add(other_user)
    db.session.commit()
    
    response = auth_client.post('/settings', data={
        'action': 'update_profile',
        'username': 'otheruser',
        'current_password': 'testpass123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Username already exists" in response.data

def test_delete_account_success(auth_client):
    """Test successful account deletion"""
    # Create some tasks for the user
    user = User.query.filter_by(username='testuser').first()
    task = Todo(content='Test task', user_id=user.id)
    db.session.add(task)
    db.session.commit()
    
    response = auth_client.post('/settings', data={
        'action': 'delete_account',
        'confirm_delete_password': 'testpass123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Your account has been deleted successfully" in response.data
    
    # Verify user and tasks were deleted
    user = User.query.filter_by(username='testuser').first()
    tasks = Todo.query.filter_by(user_id=user.id if user else None).all()
    assert user is None
    assert len(tasks) == 0

def test_delete_account_wrong_password(auth_client):
    """Test account deletion with wrong password"""
    response = auth_client.post('/settings', data={
        'action': 'delete_account',
        'confirm_delete_password': 'wrongpass'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Incorrect password. Account not deleted" in response.data
    
    # Verify user still exists
    user = User.query.filter_by(username='testuser').first()
    assert user is not None

def test_protected_routes_unauthorized(client):
    """Test accessing protected routes without authentication"""
    routes = ['/settings', '/']
    for route in routes:
        response = client.get(route, follow_redirects=True)
        assert response.status_code == 200
        assert b"You need to log in" in response.data

def test_logout(auth_client):
    """Test logout functionality"""
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been logged out" in response.data
    
    # Verify can't access protected route after logout
    response = auth_client.get('/settings', follow_redirects=True)
    assert b"You need to log in" in response.data 