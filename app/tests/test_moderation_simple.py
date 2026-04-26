import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import tempfile

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


TEST_PASSWORD = "testpassword123"
TEST_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjRQ/nKcHt2S"


db_file = tempfile.mktemp(suffix=".db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"

os.environ["TEST_DATABASE_URL"] = SQLALCHEMY_DATABASE_URL

original_database_url = None

import blog.database as db_module
original_database_url = db_module.SQLALCHAMY_DATABASE_URL
db_module.SQLALCHAMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL

db_module.engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_module.engine)

from blog import models
from blog.database import Base, get_db, SessionLocal, engine

Base.metadata.create_all(bind=engine)


from main import app

client = TestClient(app)


def create_test_user(email, name, role=models.UserRole.USER):
    db = SessionLocal()
    user = models.User(
        name=name,
        email=email,
        password=TEST_PASSWORD_HASH,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
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


def teardown_module():
    try:
        os.remove(db_file)
    except:
        pass


class TestModerationFlowSimple:
    def test_01_user_roles_work(self):
        create_test_user("user@test.com", "Regular User", models.UserRole.USER)
        create_test_user("mod@test.com", "Moderator", models.UserRole.MODERATOR)
        create_test_user("admin@test.com", "Admin", models.UserRole.ADMIN)

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

    def test_02_regular_user_creates_blog_goes_to_pending(self):
        create_test_user("user2@test.com", "User 2")
        token = get_auth_token("user2@test.com")

        response = client.post(
            "/blog/",
            json={"title": "Test Blog 2", "body": "This is a test blog post"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        assert response.json()["status"] == "pending"
        assert response.json()["title"] == "Test Blog 2"

    def test_03_moderator_can_see_pending_blogs(self):
        create_test_user("user3@test.com", "User 3")
        create_test_user("mod3@test.com", "Mod 3", models.UserRole.MODERATOR)

        user_token = get_auth_token("user3@test.com")
        client.post(
            "/blog/",
            json={"title": "Pending Blog 3", "body": "Waiting for moderation"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        mod_token = get_auth_token("mod3@test.com")
        response = client.get(
            "/moderation/pending",
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert response.status_code == 200
        blogs = response.json()
        assert len(blogs) >= 1
        for blog in blogs:
            assert blog["status"] == "pending"

    def test_04_regular_user_cannot_access_moderation_endpoints(self):
        create_test_user("user4@test.com", "User 4")
        token = get_auth_token("user4@test.com")

        response = client.get(
            "/moderation/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_05_moderator_can_approve_blog(self):
        create_test_user("user5@test.com", "User 5")
        create_test_user("mod5@test.com", "Mod 5", models.UserRole.MODERATOR)

        user_token = get_auth_token("user5@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog to Approve 5", "body": "Good content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token("mod5@test.com")
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Looks good!"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["decision"] == "approved"

        blog_response = client.get(
            f"/blog/{blog_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert blog_response.status_code == 200
        assert blog_response.json()["status"] == "approved"

    def test_06_moderator_can_reject_blog(self):
        create_test_user("user6@test.com", "User 6")
        create_test_user("mod6@test.com", "Mod 6", models.UserRole.MODERATOR)

        user_token = get_auth_token("user6@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog to Reject 6", "body": "Bad content"},
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

    def test_07_moderation_logs_are_recorded(self):
        create_test_user("user7@test.com", "User 7")
        create_test_user("mod7@test.com", "Mod 7", models.UserRole.MODERATOR)

        user_token = get_auth_token("user7@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog with Logs 7", "body": "Check logs"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token("mod7@test.com")
        client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Test comment 7"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )

        logs_response = client.get(
            "/moderation/logs",
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert logs_response.status_code == 200
        logs = logs_response.json()
        assert len(logs) >= 1

        my_logs = [l for l in logs if l["blog_id"] == blog_id]
        assert len(my_logs) >= 1
        assert my_logs[0]["decision"] == "approved"

    def test_08_rejected_blog_can_be_resubmitted(self):
        create_test_user("user8@test.com", "User 8")
        create_test_user("mod8@test.com", "Mod 8", models.UserRole.MODERATOR)

        user_token = get_auth_token("user8@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Bad Blog 8", "body": "Bad content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token("mod8@test.com")
        client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "rejected", "comment": "Please improve"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )

        update_response = client.put(
            f"/blog/{blog_id}",
            json={"title": "Improved Blog 8", "body": "Much better content"},
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