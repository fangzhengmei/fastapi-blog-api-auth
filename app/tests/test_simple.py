import pytest
from blog import models
import blog.database
from blog.hashing import Hash

TEST_PASSWORD = "password123"


def create_test_user(email, name, role=models.UserRole.USER):
    db = blog.database.SessionLocal()
    try:
        user = models.User(
            name=name,
            email=email,
            password=Hash.bcrypt(TEST_PASSWORD),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def get_auth_token(client, email, password=TEST_PASSWORD):
    response = client.post(
        "/login",
        data={
            "username": email,
            "password": password
        }
    )
    return response.json()["access_token"]


class TestSimpleSetup:
    def test_database_connection(self):
        db = blog.database.SessionLocal()
        try:
            user = models.User(
                name="Test User",
                email="test@test.com",
                password=Hash.bcrypt(TEST_PASSWORD)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            assert user.id is not None
            assert user.email == "test@test.com"
            
            queried = db.query(models.User).filter_by(email="test@test.com").first()
            assert queried is not None
            assert queried.name == "Test User"
        finally:
            db.close()

    def test_login_endpoint(self, client):
        create_test_user("login@test.com", "Login User")
        
        response = client.post(
            "/login",
            data={
                "username": "login@test.com",
                "password": TEST_PASSWORD
            }
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["role"] == "user"

    def test_user_roles_in_login(self, client):
        create_test_user("user_role@test.com", "User Role", models.UserRole.USER)
        create_test_user("mod_role@test.com", "Mod Role", models.UserRole.MODERATOR)
        create_test_user("admin_role@test.com", "Admin Role", models.UserRole.ADMIN)
        
        response = client.post(
            "/login",
            data={"username": "user_role@test.com", "password": TEST_PASSWORD}
        )
        assert response.json()["role"] == "user"
        
        response = client.post(
            "/login",
            data={"username": "mod_role@test.com", "password": TEST_PASSWORD}
        )
        assert response.json()["role"] == "moderator"
        
        response = client.post(
            "/login",
            data={"username": "admin_role@test.com", "password": TEST_PASSWORD}
        )
        assert response.json()["role"] == "admin"
