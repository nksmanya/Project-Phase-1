# reset_db.py
from app import db, app

with app.app_context():
    confirm = input("⚠️ This will DELETE ALL DATA. Type 'YES' to continue: ")
    if confirm == 'YES':
        print("Dropping all tables...")
        db.drop_all()
        print("Creating tables...")
        db.create_all()
        print("✅ Database reset completed successfully!")
    else:
        print("❌ Operation cancelled.")
