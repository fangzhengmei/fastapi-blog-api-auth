import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from blog.database import Base, get_db
from blog import models, schemas
from blog.hashing import Hash

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def create_test_user(db, name: str, email: str, password: str):
    user = models.User(
        name=name,
        email=email,
        password=Hash.bcrypt(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id


def get_auth_headers(email: str, password: str):
    response = client.post(
        "/login",
        data={"username": email, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestFollowSystem:
    
    def setup_method(self):
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()
        
        self.user1_id = create_test_user(db, "User One", "user1@example.com", "password1")
        self.user2_id = create_test_user(db, "User Two", "user2@example.com", "password2")
        self.user3_id = create_test_user(db, "User Three", "user3@example.com", "password3")
        
        db.close()
        
        self.headers_user1 = get_auth_headers("user1@example.com", "password1")
        self.headers_user2 = get_auth_headers("user2@example.com", "password2")
        self.headers_user3 = get_auth_headers("user3@example.com", "password3")
    
    def teardown_method(self):
        Base.metadata.drop_all(bind=engine)
    
    def test_follow_user_success(self):
        response = client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_following"] == True
        assert "Successfully followed" in data["message"]
    
    def test_follow_yourself_fails(self):
        response = client.post(
            f"/follow/{self.user1_id}/follow",
            headers=self.headers_user1
        )
        assert response.status_code == 400
        assert "cannot follow yourself" in response.json()["detail"]
    
    def test_follow_nonexistent_user_fails(self):
        response = client.post(
            "/follow/9999/follow",
            headers=self.headers_user1
        )
        assert response.status_code == 404
    
    def test_duplicate_follow_fails(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        assert response.status_code == 400
        assert "already following" in response.json()["detail"]
    
    def test_unfollow_user_success(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.post(
            f"/follow/{self.user2_id}/unfollow",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_following"] == False
        assert "Successfully unfollowed" in data["message"]
    
    def test_unfollow_not_following_user_fails(self):
        response = client.post(
            f"/follow/{self.user2_id}/unfollow",
            headers=self.headers_user1
        )
        assert response.status_code == 400
        assert "not following" in response.json()["detail"]
    
    def test_check_is_following(self):
        response = client.get(
            f"/follow/is-following/{self.user2_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        assert response.json()["is_following"] == False
        
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            f"/follow/is-following/{self.user2_id}",
            headers=self.headers_user1
        )
        assert response.json()["is_following"] == True
    
    def test_get_followers(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user3
        )
        
        response = client.get(
            f"/follow/followers/{self.user2_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["followers"]) == 2
        
        follower_names = [f["name"] for f in data["followers"]]
        assert "User One" in follower_names
        assert "User Three" in follower_names
    
    def test_get_following(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        client.post(
            f"/follow/{self.user3_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            f"/follow/following/{self.user1_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["following"]) == 2
        
        following_names = [f["name"] for f in data["following"]]
        assert "User Two" in following_names
        assert "User Three" in following_names


class TestFollowingBlogsFeed:
    
    def setup_method(self):
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()
        
        self.user1_id = create_test_user(db, "User One", "user1@example.com", "password1")
        self.user2_id = create_test_user(db, "User Two", "user2@example.com", "password2")
        self.user3_id = create_test_user(db, "User Three", "user3@example.com", "password3")
        
        blog1 = models.Blog(title="Blog 1 by User 2", body="Body 1", user_id=self.user2_id)
        blog2 = models.Blog(title="Blog 2 by User 2", body="Body 2", user_id=self.user2_id)
        blog3 = models.Blog(title="Blog 1 by User 3", body="Body 3", user_id=self.user3_id)
        
        db.add(blog1)
        db.add(blog2)
        db.add(blog3)
        db.commit()
        
        db.close()
        
        self.headers_user1 = get_auth_headers("user1@example.com", "password1")
        self.headers_user2 = get_auth_headers("user2@example.com", "password2")
    
    def teardown_method(self):
        Base.metadata.drop_all(bind=engine)
    
    def test_get_following_blogs_empty_when_not_following(self):
        response = client.get(
            "/blog/feed/following",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_following_blogs_shows_following_authors_blogs(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        blogs = response.json()
        
        assert len(blogs) == 2
        
        for blog in blogs:
            assert blog["creator"]["name"] == "User Two"
    
    def test_get_following_blogs_multiple_authors(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        client.post(
            f"/follow/{self.user3_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        blogs = response.json()
        
        assert len(blogs) == 3
        
        author_names = [blog["creator"]["name"] for blog in blogs]
        assert "User Two" in author_names
        assert "User Three" in author_names
    
    def test_get_following_blogs_pagination(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        client.post(
            f"/follow/{self.user3_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following?limit=2",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        response = client.get(
            "/blog/feed/following?skip=2&limit=10",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
    
    def test_get_following_blogs_unfollow_stops_showing_blogs(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following",
            headers=self.headers_user1
        )
        assert len(response.json()) == 2
        
        client.post(
            f"/follow/{self.user2_id}/unfollow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following",
            headers=self.headers_user1
        )
        assert len(response.json()) == 0