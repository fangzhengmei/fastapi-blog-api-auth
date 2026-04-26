import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog import models
from blog.database import SessionLocal, engine, Base
from blog.hashing import Hash


def init_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        regular_user = db.query(models.User).filter(
            models.User.email == "user@example.com"
        ).first()
        if not regular_user:
            regular_user = models.User(
                name="Regular User",
                email="user@example.com",
                password=Hash.bcrypt("password123"),
                role=models.UserRole.USER
            )
            db.add(regular_user)
            print("Created regular user: user@example.com / password123")

        moderator = db.query(models.User).filter(
            models.User.email == "moderator@example.com"
        ).first()
        if not moderator:
            moderator = models.User(
                name="Moderator User",
                email="moderator@example.com",
                password=Hash.bcrypt("password123"),
                role=models.UserRole.MODERATOR
            )
            db.add(moderator)
            print("Created moderator: moderator@example.com / password123")

        admin = db.query(models.User).filter(
            models.User.email == "admin@example.com"
        ).first()
        if not admin:
            admin = models.User(
                name="Admin User",
                email="admin@example.com",
                password=Hash.bcrypt("password123"),
                role=models.UserRole.ADMIN
            )
            db.add(admin)
            print("Created admin: admin@example.com / password123")

        db.commit()
        print("\nDatabase initialized successfully!")
        print("\nAvailable users:")
        print("  - Regular User: user@example.com / password123")
        print("  - Moderator: moderator@example.com / password123")
        print("  - Admin: admin@example.com / password123")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if os.path.exists("blog.db"):
        os.remove("blog.db")
        print("Removed old database.")
    
    init_database()