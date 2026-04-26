import os
import tempfile
import sys

TEST_DB_FILE = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

print(f"Test DB file: {TEST_DB_FILE}")
print(f"DATABASE_URL env: {os.environ.get('DATABASE_URL')}")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import blog.database

print(f"blog.database.DATABASE_URL: {blog.database.DATABASE_URL}")

from blog import models
from blog.database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

from main import app

from fastapi.testclient import TestClient

client = TestClient(app)

PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjRQ/nKcHt2S"
TEST_PASSWORD = "password123"


def test_debug():
    print(f"\n=== Starting debug test ===")
    print(f"Test DB file: {TEST_DB_FILE}")
    
    db = SessionLocal()
    try:
        print(f"Creating user...")
        user = models.User(
            name="Debug User",
            email="debug@test.com",
            password=PASSWORD_HASH,
            role=models.UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"User created with id: {user.id}, email: {user.email}")
        
        queried = db.query(models.User).filter_by(email="debug@test.com").first()
        print(f"Queried user in same session: {queried}")
        if queried:
            print(f"  id: {queried.id}, email: {queried.email}")
        
        db2 = SessionLocal()
        try:
            queried2 = db2.query(models.User).filter_by(email="debug@test.com").first()
            print(f"Queried user in new session: {queried2}")
            if queried2:
                print(f"  id: {queried2.id}, email: {queried2.email}")
        finally:
            db2.close()
        
        print(f"\nTrying login via API...")
        response = client.post(
            "/login",
            data={
                "username": "debug@test.com",
                "password": TEST_PASSWORD
            }
        )
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.json()}")
        
        print(f"\nChecking app.dependency_overrides: {app.dependency_overrides}")
        
    finally:
        db.close()
    
    assert True


if __name__ == "__main__":
    test_debug()
