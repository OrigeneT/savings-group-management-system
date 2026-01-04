"""
Initialize database and create admin user with email
"""
from savings_group.app import app, db
from savings_group.models import User

with app.app_context():
    # Create all tables
    db.create_all()
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        # Create admin user
        admin = User(
            username='admin',
            email='itsindaubumwe@gmail.com',
            role='admin'
        )
        admin.set_password('admin123')  # Default password
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin user created")
        print("  Username: admin")
        print("  Email: itsindaubumwe@gmail.com")
        print("  Password: admin123")
    else:
        # Update existing admin with email if not set
        if not admin.email:
            admin.email = 'itsindaubumwe@gmail.com'
            db.session.commit()
            print("✓ Email added to existing admin user")
        print("✓ Admin user already exists")
        print("  Username:", admin.username)
        print("  Email:", admin.email)
