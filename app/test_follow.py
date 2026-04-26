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
    
    def test_unfollow_nonexistent_user_fails(self):
        response = client.post(
            "/follow/9999/unfollow",
            headers=self.headers_user1
        )
        assert response.status_code == 404
    
    def test_is_following_nonexistent_user_fails(self):
        response = client.get(
            "/follow/is-following/9999",
            headers=self.headers_user1
        )
        assert response.status_code == 404
    
    def test_get_followers_nonexistent_user_fails(self):
        response = client.get(
            "/follow/followers/9999",
            headers=self.headers_user1
        )
        assert response.status_code == 404
    
    def test_get_following_nonexistent_user_fails(self):
        response = client.get(
            "/follow/following/9999",
            headers=self.headers_user1
        )
        assert response.status_code == 404


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
    
    def test_get_following_blogs_skip_exceeds_count(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        client.post(
            f"/follow/{self.user3_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following?skip=100&limit=10",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_following_blogs_limit_exceeds_count(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        client.post(
            f"/follow/{self.user3_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following?limit=100",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        assert len(response.json()) == 3
    
    def test_get_following_blogs_invalid_skip_negative(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following?skip=-1",
            headers=self.headers_user1
        )
        assert response.status_code == 422
    
    def test_get_following_blogs_invalid_limit_zero(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following?limit=0",
            headers=self.headers_user1
        )
        assert response.status_code == 422
    
    def test_get_following_blogs_invalid_limit_too_large(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following?limit=101",
            headers=self.headers_user1
        )
        assert response.status_code == 422
    
    def test_get_following_blogs_skip_zero(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            "/blog/feed/following?skip=0&limit=10",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestUserProfileFollowCounts:
    
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
    
    def test_user_profile_has_followers_and_following_counts(self):
        response = client.get(
            f"/user/{self.user1_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "followers_count" in data
        assert "following_count" in data
        assert data["followers_count"] == 0
        assert data["following_count"] == 0
    
    def test_user_profile_followers_count_increments_when_followed(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user3
        )
        
        response = client.get(
            f"/user/{self.user2_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["followers_count"] == 2
        assert data["following_count"] == 0
    
    def test_user_profile_following_count_increments_when_following(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        client.post(
            f"/follow/{self.user3_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            f"/user/{self.user1_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["followers_count"] == 0
        assert data["following_count"] == 2
    
    def test_user_profile_followers_count_decrements_when_unfollowed(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user3
        )
        
        response = client.get(
            f"/user/{self.user2_id}",
            headers=self.headers_user1
        )
        assert response.json()["followers_count"] == 2
        
        client.post(
            f"/follow/{self.user2_id}/unfollow",
            headers=self.headers_user1
        )
        
        response = client.get(
            f"/user/{self.user2_id}",
            headers=self.headers_user1
        )
        assert response.json()["followers_count"] == 1
    
    def test_user_profile_following_count_decrements_when_unfollowing(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        client.post(
            f"/follow/{self.user3_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            f"/user/{self.user1_id}",
            headers=self.headers_user1
        )
        assert response.json()["following_count"] == 2
        
        client.post(
            f"/follow/{self.user2_id}/unfollow",
            headers=self.headers_user1
        )
        
        response = client.get(
            f"/user/{self.user1_id}",
            headers=self.headers_user1
        )
        assert response.json()["following_count"] == 1
    
    def test_user_profile_nonexistent_user_returns_404(self):
        response = client.get(
            "/user/9999",
            headers=self.headers_user1
        )
        assert response.status_code == 404
    
    def test_user_profile_contains_basic_info(self):
        response = client.get(
            f"/user/{self.user1_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.user1_id
        assert data["name"] == "User One"
        assert "blogs" in data
    
    def test_user_profile_email_visible_to_owner(self):
        response = client.get(
            f"/user/{self.user1_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == "user1@example.com"
    
    def test_user_profile_email_hidden_from_other_users(self):
        response = client.get(
            f"/user/{self.user2_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.user2_id
        assert data["name"] == "User Two"
        assert data["email"] is None
    
    def test_user_profile_email_hidden_from_guest(self):
        response = client.get(
            f"/user/{self.user1_id}"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.user1_id
        assert data["name"] == "User One"
        assert data["email"] is None
    
    def test_followers_list_does_not_show_email(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            f"/follow/followers/{self.user2_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 1
        assert len(data["followers"]) == 1
        
        follower = data["followers"][0]
        assert follower["id"] == self.user1_id
        assert follower["name"] == "User One"
        assert "email" not in follower
    
    def test_following_list_does_not_show_email(self):
        client.post(
            f"/follow/{self.user2_id}/follow",
            headers=self.headers_user1
        )
        
        response = client.get(
            f"/follow/following/{self.user1_id}",
            headers=self.headers_user1
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["count"] == 1
        assert len(data["following"]) == 1
        
        following = data["following"][0]
        assert following["id"] == self.user2_id
        assert following["name"] == "User Two"
        assert "email" not in following
    
    def test_guest_can_view_user_profile_without_auth(self):
        response = client.get(
            f"/user/{self.user2_id}"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.user2_id
        assert data["name"] == "User Two"
        assert data["email"] is None
        assert "followers_count" in data
        assert "following_count" in data
    
    def test_expired_token_treated_as_guest(self):
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMUBleGFtcGxlLmNvbSIsImV4cCI6MH0.invalid_signature"
        response = client.get(
            f"/user/{self.user2_id}",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.user2_id
        assert data["name"] == "User Two"
        assert data["email"] is None
    
    def test_invalid_token_format_treated_as_guest(self):
        invalid_token = "this-is-not-a-valid-jwt-token"
        response = client.get(
            f"/user/{self.user2_id}",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.user2_id
        assert data["name"] == "User Two"
        assert data["email"] is None
    
    def test_malformed_authorization_header_treated_as_guest(self):
        response = client.get(
            f"/user/{self.user2_id}",
            headers={"Authorization": "Basic some_token"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.user2_id
        assert data["name"] == "User Two"
        assert data["email"] is None
    
    def test_invalid_signature_token_treated_as_guest(self):
        invalid_sig_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMUBleGFtcGxlLmNvbSJ9.wrong_signature"
        response = client.get(
            f"/user/{self.user2_id}",
            headers={"Authorization": f"Bearer {invalid_sig_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.user2_id
        assert data["name"] == "User Two"
        assert data["email"] is None
    
    def test_empty_bearer_token_treated_as_guest(self):
        response = client.get(
            f"/user/{self.user2_id}",
            headers={"Authorization": "Bearer "}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == self.user2_id
        assert data["name"] == "User Two"
        assert data["email"] is None