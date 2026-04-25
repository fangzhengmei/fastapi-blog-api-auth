import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from blog.database import Base, get_db
from blog import models
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def user1_token(client, test_db):
    client.post(
        "/user/",
        json={"name": "User One", "email": "user1@example.com", "password": "password123"}
    )
    response = client.post(
        "/login",
        data={"username": "user1@example.com", "password": "password123"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def user2_token(client, test_db):
    client.post(
        "/user/",
        json={"name": "User Two", "email": "user2@example.com", "password": "password123"}
    )
    response = client.post(
        "/login",
        data={"username": "user2@example.com", "password": "password123"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def user1_draft_blog(client, user1_token):
    response = client.post(
        "/blog/",
        json={"title": "Draft Blog", "body": "This is a draft", "is_published": False},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    return response.json()


@pytest.fixture(scope="function")
def user1_published_blog(client, user1_token):
    response = client.post(
        "/blog/",
        json={"title": "Published Blog", "body": "This is published", "is_published": True},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    return response.json()
