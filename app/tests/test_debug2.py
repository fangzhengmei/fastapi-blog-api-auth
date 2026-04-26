import os
import tempfile
import sys

TEST_DB_FILE = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

print(f"Test DB file: {TEST_DB_FILE}")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import blog.database

from blog import models
from blog.database import SessionLocal, engine, Base
from blog.hashing import Hash

Base.metadata.create_all(bind=engine)

from main import app

from fastapi.testclient import TestClient

client = TestClient(app)

TEST_PASSWORD = "password123"


def test_debug():
    print(f"\n=== Starting debug test with dynamic password hash ===")
    
    password_hash = Hash.bcrypt(TEST_PASSWORD)
    print(f"Generated password hash: {password_hash}")
    print(f"Verifying hash: {Hash.verify(password_hash, TEST_PASSWORD)}")
    
    db = SessionLocal()
    try:
        print(f"\nCreating user with generated hash...")
        user = models.User(
            name="Debug User",
            email="debug2@test.com",
            password=password_hash,
            role=models.UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"User created with id: {user.id}, email: {user.email}")
        
        print(f"\nVerifying stored password hash:")
        print(f"  Stored hash: {user.password}")
        print(f"  Verify result: {Hash.verify(user.password, TEST_PASSWORD)}")
        
        print(f"\nTrying login via API...")
        response = client.post(
            "/login",
            data={
                "username": "debug2@test.com",
                "password": TEST_PASSWORD
            }
        )
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.json()}")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_debug()
