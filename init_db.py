from backend import models, database, auth
import os

def init_db():
    print("Initializing Database...")
    models.Base.metadata.create_all(bind=database.engine)
    
    db = next(database.get_db())
    
    # Check if admin already exists
    admin_email = "admin@college.edu"
    existing_admin = db.query(models.User).filter(models.User.email == admin_email).first()
    
    if not existing_admin:
        print(f"Creating administrator account: {admin_email}")
        hashed_pw = auth.get_password_hash("admin123")
        admin_user = models.User(
            email=admin_email,
            full_name="System Administrator",
            hashed_password=hashed_pw,
            role="admin"
        )
        db.add(admin_user)
        db.commit()
        print("Admin account created successfully! Password: admin123")
    else:
        print("Admin account already exists.")
    
    db.close()

if __name__ == "__main__":
    init_db()
