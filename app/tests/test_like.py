import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blog import models
from blog.database import Base, get_db
from blog.hashing import Hash
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    test_user = models.User(
        name="testuser",
        email="test@example.com",
        password=Hash.bcrypt("testpassword")
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    test_blog = models.Blog(
        title="Test Blog",
        body="This is a test blog",
        user_id=test_user.id
    )
    db.add(test_blog)
    db.commit()
    db.refresh(test_blog)
    
    test_blog2 = models.Blog(
        title="Test Blog 2",
        body="This is another test blog",
        user_id=test_user.id
    )
    db.add(test_blog2)
    db.commit()
    db.refresh(test_blog2)
    
    db.close()
    
    with TestClient(app) as c:
        yield c
    
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture(scope="module")
def auth_token(client):
    response = client.post(
        "/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]


def test_login(client):
    response = client.post(
        "/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_like_blog(client, auth_token):
    response = client.post(
        "/like/1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["blog_id"] == 1
    assert data["user_id"] == 1


def test_like_nonexistent_blog(client, auth_token):
    response = client.post(
        "/like/999",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_like_count(client, auth_token):
    response = client.get(
        "/like/count/1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["blog_id"] == 1
    assert data["likes_count"] == 1


def test_get_like_status_liked(client, auth_token):
    response = client.get(
        "/like/status/1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_liked"] == True


def test_get_like_status_not_liked(client, auth_token):
    response = client.get(
        "/like/status/2",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_liked"] == False


def test_like_blog_already_liked(client, auth_token):
    response = client.post(
        "/like/1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "already liked" in response.json()["detail"]


def test_unlike_blog(client, auth_token):
    client.post(
        "/like/2",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    response = client.delete(
        "/like/2",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 204


def test_unlike_not_liked_blog(client, auth_token):
    response = client.delete(
        "/like/2",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "not liked" in response.json()["detail"]


def test_blog_show_with_likes(client, auth_token):
    response = client.get(
        "/blog/1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["likes_count"] == 1
    assert data["is_liked"] == True


def test_blog_list_with_likes(client, auth_token):
    response = client.get(
        "/blog/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "likes_count" in data[0]
    assert "is_liked" in data[0]


def test_create_blog_with_current_user(client, auth_token):
    response = client.post(
        "/blog/",
        json={"title": "New Test Blog", "body": "New test body"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
