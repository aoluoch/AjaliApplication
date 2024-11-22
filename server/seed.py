from models.extensions import db
from models.user import User
from werkzeug.security import generate_password_hash

def seed_admins():
    admin1 = User(
        username="admin1",
        email="admin1@example.com",
        password_hash=generate_password_hash("password123"),
        is_admin=True
    )
    admin2 = User(
        username="admin2",
        email="admin2@example.com",
        password_hash=generate_password_hash("password123"),
        is_admin=True
    )

    # Add admins to the session
    db.session.add(admin1)
    db.session.add(admin2)

    # Commit the session
    db.session.commit()

    print("Admin users have been seeded.")

if __name__ == "__main__":
  
    from app import app

    with app.app_context():
        seed_admins()
