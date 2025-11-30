#!/usr/bin/env python
"""
Quick script to create a test user with fast password hashing
"""
from app import app, db, User
from werkzeug.security import generate_password_hash

def create_test_user():
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(email='test@test.com').first()
        if existing_user:
            print("Test user already exists!")
            print("Email: test@test.com")
            print("Password: test123")
            db.session.delete(existing_user)
            db.session.commit()
            print("Deleted old test user, creating new one...")
        
        # Create new test user with SIMPLE password hash (faster)
        # Using method='pbkdf2:sha256:1' for minimal iterations (faster login)
        password_hash = generate_password_hash('test123', method='pbkdf2:sha256:1')
        
        test_user = User(
            name='Test User',
            email='test@test.com',
            password_hash=password_hash
        )
        
        db.session.add(test_user)
        db.session.commit()
        
        print("✅ Test user created successfully!")
        print("=" * 50)
        print("LOGIN CREDENTIALS:")
        print("Email: test@test.com")
        print("Password: test123")
        print("=" * 50)
        print("\nYou can now login at http://127.0.0.1:5000")

if __name__ == '__main__':
    create_test_user()
