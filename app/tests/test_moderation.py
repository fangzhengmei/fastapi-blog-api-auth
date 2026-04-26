import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


from blog.database import Base, get_db as original_get_db
from blog import models


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


from main import app

app.dependency_overrides[original_get_db] = override_get_db

client = TestClient(app)

TEST_PASSWORD = "testpassword123"
TEST_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjRQ/nKcHt2S"


def create_test_user(db, email, name, role=models.UserRole.USER):
    user = models.User(
        name=name,
        email=email,
        password=TEST_PASSWORD_HASH,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_token(email, password=TEST_PASSWORD):
    response = client.post(
        "/login",
        data={
            "username": email,
            "password": password
        }
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


class TestModerationFlow:
    def test_01_user_roles_work(self, db_session):
        create_test_user(db_session, "user@test.com", "Regular User", models.UserRole.USER)
        create_test_user(db_session, "mod@test.com", "Moderator", models.UserRole.MODERATOR)
        create_test_user(db_session, "admin@test.com", "Admin", models.UserRole.ADMIN)

        response = client.post(
            "/login",
            data={"username": "user@test.com", "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "user"

        response = client.post(
            "/login",
            data={"username": "mod@test.com", "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "moderator"

        response = client.post(
            "/login",
            data={"username": "admin@test.com", "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"

    def test_02_regular_user_creates_blog_goes_to_pending(self, db_session):
        user = create_test_user(db_session, "user1@test.com", "User 1")
        token = get_auth_token("user1@test.com")

        response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "This is a test blog post"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        assert response.json()["status"] == "pending"
        assert response.json()["title"] == "Test Blog"

    def test_03_moderator_can_see_pending_blogs(self, db_session):
        user = create_test_user(db_session, "user2@test.com", "User 2")
        mod = create_test_user(db_session, "mod2@test.com", "Mod 2", models.UserRole.MODERATOR)

        user_token = get_auth_token("user2@test.com")
        client.post(
            "/blog/",
            json={"title": "Pending Blog", "body": "Waiting for moderation"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        mod_token = get_auth_token("mod2@test.com")
        response = client.get(
            "/moderation/pending",
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert response.status_code == 200
        blogs = response.json()
        assert len(blogs) >= 1
        for blog in blogs:
            assert blog["status"] == "pending"

    def test_04_regular_user_cannot_access_moderation_endpoints(self, db_session):
        user = create_test_user(db_session, "user3@test.com", "User 3")
        token = get_auth_token("user3@test.com")

        response = client.get(
            "/moderation/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_05_moderator_can_approve_blog(self, db_session):
        user = create_test_user(db_session, "user4@test.com", "User 4")
        mod = create_test_user(db_session, "mod4@test.com", "Mod 4", models.UserRole.MODERATOR)

        user_token = get_auth_token("user4@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog to Approve", "body": "Good content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token("mod4@test.com")
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Looks good!"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["decision"] == "approved"
        assert moderate_response.json()["comment"] == "Looks good!"

        blog_response = client.get(
            f"/blog/{blog_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert blog_response.status_code == 200
        assert blog_response.json()["status"] == "approved"

    def test_06_approved_blog_visible_to_other_users(self, db_session):
        user1 = create_test_user(db_session, "user5a@test.com", "User 5A")
        user2 = create_test_user(db_session, "user5b@test.com", "User 5B")
        mod = create_test_user(db_session, "mod5@test.com", "Mod 5", models.UserRole.MODERATOR)

        user1_token = get_auth_token("user5a@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Approved Blog", "body": "Everyone should see this"},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token("mod5@test.com")
        client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Great!"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )

        user2_token = get_auth_token("user5b@test.com")
        response = client.get(
            "/blog/",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 200
        blogs = response.json()
        approved_titles = [b["title"] for b in blogs if b["status"] == "approved"]
        assert "Approved Blog" in approved_titles

    def test_07_moderator_can_reject_blog(self, db_session):
        user = create_test_user(db_session, "user6@test.com", "User 6")
        mod = create_test_user(db_session, "mod6@test.com", "Mod 6", models.UserRole.MODERATOR)

        user_token = get_auth_token("user6@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog to Reject", "body": "Bad content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token("mod6@test.com")
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "rejected", "comment": "Content not appropriate"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["decision"] == "rejected"

        blog_response = client.get(
            f"/blog/{blog_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert blog_response.status_code == 200
        assert blog_response.json()["status"] == "rejected"

    def test_08_moderation_logs_are_recorded(self, db_session):
        user = create_test_user(db_session, "user7@test.com", "User 7")
        mod = create_test_user(db_session, "mod7@test.com", "Mod 7", models.UserRole.MODERATOR)

        user_token = get_auth_token("user7@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog with Logs", "body": "Check logs"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token("mod7@test.com")
        client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Test comment"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )

        logs_response = client.get(
            "/moderation/logs",
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert logs_response.status_code == 200
        logs = logs_response.json()
        assert len(logs) >= 1
        assert logs[0]["decision"] == "approved"
        assert logs[0]["comment"] == "Test comment"

    def test_09_user_can_view_own_blog_moderation_logs(self, db_session):
        user = create_test_user(db_session, "user8@test.com", "User 8")
        mod = create_test_user(db_session, "mod8@test.com", "Mod 8", models.UserRole.MODERATOR)

        user_token = get_auth_token("user8@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "My Blog", "body": "My content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token("mod8@test.com")
        client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Good work!"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )

        logs_response = client.get(
            f"/moderation/blog/{blog_id}/logs",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert logs_response.status_code == 200
        logs = logs_response.json()
        assert len(logs) >= 1
        assert logs[0]["decision"] == "approved"

    def test_10_rejected_blog_can_be_resubmitted(self, db_session):
        user = create_test_user(db_session, "user9@test.com", "User 9")
        mod = create_test_user(db_session, "mod9@test.com", "Mod 9", models.UserRole.MODERATOR)

        user_token = get_auth_token("user9@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Bad Blog", "body": "Bad content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token("mod9@test.com")
        client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "rejected", "comment": "Please improve"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )

        update_response = client.put(
            f"/blog/{blog_id}",
            json={"title": "Improved Blog", "body": "Much better content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert update_response.status_code == 202

        pending_response = client.get(
            "/moderation/pending",
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        pending_blogs = pending_response.json()
        resubmitted = [b for b in pending_blogs if b["id"] == blog_id]
        assert len(resubmitted) == 1
        assert resubmitted[0]["status"] == "pending"

    def test_11_only_owner_can_update_blog(self, db_session):
        hacker = create_test_user(db_session, "hacker@test.com", "Hacker")
        owner = create_test_user(db_session, "owner@test.com", "Owner")

        owner_blog = models.Blog(
            title="Owner's Blog",
            body="This is mine",
            user_id=owner.id,
            status=models.BlogStatus.PENDING
        )
        db_session.add(owner_blog)
        db_session.commit()
        db_session.refresh(owner_blog)
        blog_id = owner_blog.id

        hacker_token = get_auth_token("hacker@test.com")
        update_response = client.put(
            f"/blog/{blog_id}",
            json={"title": "Hacked!", "body": "Got it!"},
            headers={"Authorization": f"Bearer {hacker_token}"}
        )
        assert update_response.status_code == 403