import os

# Test configuration
TESTING = True
WTF_CSRF_ENABLED = False  # Disable CSRF tokens in tests
SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory database for testing
SECRET_KEY = 'test_secret_key' 