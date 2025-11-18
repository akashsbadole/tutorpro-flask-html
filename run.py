from app import create_app
from app.models.user import User, UserProfile
from app import db

app = create_app()

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        
        # Create an admin user if it doesn't exist
        admin_user = User.query.filter_by(email='admin@tutorpro.com').first()
        if not admin_user:
            admin_user = User(
                email='admin@tutorpro.com',
                password='Admin123!',
                role='Admin'
            )
            db.session.add(admin_user)
            
            admin_profile = UserProfile(
                user=admin_user,
                first_name='System',
                last_name='Administrator'
            )
            db.session.add(admin_profile)
            db.session.commit()
            print("Admin user created with email: admin@tutorpro.com and password: Admin123!")
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)