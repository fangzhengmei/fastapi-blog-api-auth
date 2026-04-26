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


class TestUserRoles:
    def test_user_can_login_with_role(self, client):
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


class TestBlogCreation:
    def test_regular_user_creates_blog_goes_to_pending(self, client):
        create_test_user("user1@test.com", "User 1")
        token = get_auth_token(client, "user1@test.com")

        response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "This is a test blog post"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        assert response.json()["status"] == "pending"
        assert response.json()["title"] == "Test Blog"


class TestModeratorAccess:
    def test_moderator_can_see_pending_blogs(self, client):
        create_test_user("user2@test.com", "User 2")
        create_test_user("mod2@test.com", "Mod 2", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user2@test.com")
        client.post(
            "/blog/",
            json={"title": "Pending Blog", "body": "Waiting for moderation"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        mod_token = get_auth_token(client, "mod2@test.com")
        response = client.get(
            "/moderation/pending",
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert response.status_code == 200
        blogs = response.json()
        assert len(blogs) >= 1
        for blog in blogs:
            assert blog["status"] == "pending"

    def test_regular_user_cannot_access_moderation_endpoints(self, client):
        create_test_user("user3@test.com", "User 3")
        token = get_auth_token(client, "user3@test.com")

        response = client.get(
            "/moderation/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403


class TestBlogApproval:
    def test_moderator_can_approve_blog(self, client):
        create_test_user("user4@test.com", "User 4")
        create_test_user("mod4@test.com", "Mod 4", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user4@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog to Approve", "body": "Good content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod4@test.com")
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

    def test_approved_blog_visible_to_other_users(self, client):
        create_test_user("user5a@test.com", "User 5A")
        create_test_user("user5b@test.com", "User 5B")
        create_test_user("mod5@test.com", "Mod 5", models.UserRole.MODERATOR)

        user1_token = get_auth_token(client, "user5a@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Approved Blog", "body": "Everyone should see this"},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod5@test.com")
        client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Great!"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )

        user2_token = get_auth_token(client, "user5b@test.com")
        response = client.get(
            "/blog/",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 200
        blogs = response.json()
        approved_titles = [b["title"] for b in blogs if b["status"] == "approved"]
        assert "Approved Blog" in approved_titles


class TestBlogRejection:
    def test_moderator_can_reject_blog(self, client):
        create_test_user("user6@test.com", "User 6")
        create_test_user("mod6@test.com", "Mod 6", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user6@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog to Reject", "body": "Bad content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod6@test.com")
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


class TestModerationLogs:
    def test_moderation_logs_are_recorded(self, client):
        create_test_user("user7@test.com", "User 7")
        create_test_user("mod7@test.com", "Mod 7", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user7@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog with Logs", "body": "Check logs"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod7@test.com")
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

        my_logs = [l for l in logs if l["blog_id"] == blog_id]
        assert len(my_logs) >= 1
        assert my_logs[0]["decision"] == "approved"

    def test_user_can_view_own_blog_moderation_logs(self, client):
        create_test_user("user8@test.com", "User 8")
        create_test_user("mod8@test.com", "Mod 8", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user8@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "My Blog", "body": "My content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod8@test.com")
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


class TestBlogResubmission:
    def test_rejected_blog_can_be_resubmitted(self, client):
        create_test_user("user9@test.com", "User 9")
        create_test_user("mod9@test.com", "Mod 9", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user9@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Bad Blog", "body": "Bad content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod9@test.com")
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


class TestBlogOwnership:
    def test_only_owner_can_update_blog(self, client):
        create_test_user("hacker@test.com", "Hacker")
        create_test_user("owner@test.com", "Owner")

        db = blog.database.SessionLocal()
        try:
            owner = db.query(models.User).filter_by(email="owner@test.com").first()
            owner_blog = models.Blog(
                title="Owner's Blog",
                body="This is mine",
                user_id=owner.id,
                status=models.BlogStatus.PENDING
            )
            db.add(owner_blog)
            db.commit()
            db.refresh(owner_blog)
            blog_id = owner_blog.id
        finally:
            db.close()

        hacker_token = get_auth_token(client, "hacker@test.com")
        update_response = client.put(
            f"/blog/{blog_id}",
            json={"title": "Hacked!", "body": "Got it!"},
            headers={"Authorization": f"Bearer {hacker_token}"}
        )
        assert update_response.status_code == 403

    def test_only_owner_can_delete_blog(self, client):
        create_test_user("hacker2@test.com", "Hacker 2")
        create_test_user("owner2@test.com", "Owner 2")

        db = blog.database.SessionLocal()
        try:
            owner = db.query(models.User).filter_by(email="owner2@test.com").first()
            owner_blog = models.Blog(
                title="Owner's Blog 2",
                body="This is mine too",
                user_id=owner.id,
                status=models.BlogStatus.PENDING
            )
            db.add(owner_blog)
            db.commit()
            db.refresh(owner_blog)
            blog_id = owner_blog.id
        finally:
            db.close()

        hacker_token = get_auth_token(client, "hacker2@test.com")
        delete_response = client.delete(
            f"/blog/{blog_id}",
            headers={"Authorization": f"Bearer {hacker_token}"}
        )
        assert delete_response.status_code == 403


class TestModerationEdgeCases:
    def test_cannot_moderate_already_approved_blog(self, client):
        create_test_user("user_edge1@test.com", "User Edge 1")
        create_test_user("mod_edge1@test.com", "Mod Edge 1", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_edge1@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog to Approve Twice", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_edge1@test.com")
        first_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "First approval"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert first_response.status_code == 200
        assert first_response.json()["decision"] == "approved"

        second_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "rejected", "comment": "Trying to reject"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert second_response.status_code == 400
        assert "not pending" in second_response.json()["detail"].lower()

    def test_cannot_moderate_already_rejected_blog(self, client):
        create_test_user("user_edge2@test.com", "User Edge 2")
        create_test_user("mod_edge2@test.com", "Mod Edge 2", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_edge2@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Blog to Reject Twice", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_edge2@test.com")
        first_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "rejected", "comment": "First rejection"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert first_response.status_code == 200
        assert first_response.json()["decision"] == "rejected"

        second_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Trying to approve"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert second_response.status_code == 400
        assert "not pending" in second_response.json()["detail"].lower()

    def test_moderator_cannot_moderate_own_blog(self, client):
        create_test_user("mod_edge3@test.com", "Mod Edge 3", models.UserRole.MODERATOR)

        mod_token = get_auth_token(client, "mod_edge3@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Moderator's Own Blog", "body": "My own post"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        blog_id = create_response.json()["id"]
        assert create_response.status_code == 201
        assert create_response.json()["status"] == "pending"

        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Trying to approve my own post"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 403
        assert "cannot moderate your own" in moderate_response.json()["detail"].lower()

        blog_response = client.get(
            f"/blog/{blog_id}",
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert blog_response.json()["status"] == "pending"

    def test_another_moderator_can_moderate_moderator_s_blog(self, client):
        create_test_user("mod_edge4a@test.com", "Mod Edge 4A", models.UserRole.MODERATOR)
        create_test_user("mod_edge4b@test.com", "Mod Edge 4B", models.UserRole.MODERATOR)

        mod_a_token = get_auth_token(client, "mod_edge4a@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Mod A's Blog", "body": "Created by Mod A"},
            headers={"Authorization": f"Bearer {mod_a_token}"}
        )
        blog_id = create_response.json()["id"]
        assert create_response.json()["status"] == "pending"

        mod_b_token = get_auth_token(client, "mod_edge4b@test.com")
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Approved by Mod B"},
            headers={"Authorization": f"Bearer {mod_b_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["decision"] == "approved"

        blog_response = client.get(
            f"/blog/{blog_id}",
            headers={"Authorization": f"Bearer {mod_a_token}"}
        )
        assert blog_response.json()["status"] == "approved"

    def test_rejected_blog_updated_resets_to_pending_and_can_be_moderated_again(self, client):
        create_test_user("user_edge5@test.com", "User Edge 5")
        create_test_user("mod_edge5@test.com", "Mod Edge 5", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_edge5@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Bad Blog", "body": "Original bad content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_edge5@test.com")
        client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "rejected", "comment": "Need improvement"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )

        client.put(
            f"/blog/{blog_id}",
            json={"title": "Improved Blog", "body": "Much better content now"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "Now it's good"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["decision"] == "approved"

        blog_response = client.get(
            f"/blog/{blog_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert blog_response.json()["status"] == "approved"


class TestModerationCommentValidation:
    MAX_COMMENT_LENGTH = 500

    def test_comment_with_max_length_accepted(self, client):
        create_test_user("user_comment1@test.com", "User Comment 1")
        create_test_user("mod_comment1@test.com", "Mod Comment 1", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_comment1@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_comment1@test.com")
        max_comment = "A" * self.MAX_COMMENT_LENGTH
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": max_comment},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["comment"] == max_comment

    def test_comment_exceeding_max_length_rejected(self, client):
        create_test_user("user_comment2@test.com", "User Comment 2")
        create_test_user("mod_comment2@test.com", "Mod Comment 2", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_comment2@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_comment2@test.com")
        too_long_comment = "A" * (self.MAX_COMMENT_LENGTH + 1)
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": too_long_comment},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 422
        assert "500" in moderate_response.text or "length" in moderate_response.text.lower()

    def test_empty_comment_treated_as_none(self, client):
        create_test_user("user_comment3@test.com", "User Comment 3")
        create_test_user("mod_comment3@test.com", "Mod Comment 3", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_comment3@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_comment3@test.com")
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": ""},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["comment"] is None

    def test_whitespace_only_comment_treated_as_none(self, client):
        create_test_user("user_comment4@test.com", "User Comment 4")
        create_test_user("mod_comment4@test.com", "Mod Comment 4", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_comment4@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_comment4@test.com")
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "   \t\n  "},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["comment"] is None

    def test_comment_with_leading_trailing_whitespace_is_stripped(self, client):
        create_test_user("user_comment5@test.com", "User Comment 5")
        create_test_user("mod_comment5@test.com", "Mod Comment 5", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_comment5@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_comment5@test.com")
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": "  Good content!  "},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["comment"] == "Good content!"

    def test_no_comment_field_accepted(self, client):
        create_test_user("user_comment6@test.com", "User Comment 6")
        create_test_user("mod_comment6@test.com", "Mod Comment 6", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_comment6@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_comment6@test.com")
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved"},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["comment"] is None

    def test_null_comment_accepted(self, client):
        create_test_user("user_comment7@test.com", "User Comment 7")
        create_test_user("mod_comment7@test.com", "Mod Comment 7", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_comment7@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_comment7@test.com")
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": None},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["comment"] is None

    def test_special_characters_in_comment_accepted(self, client):
        create_test_user("user_comment8@test.com", "User Comment 8")
        create_test_user("mod_comment8@test.com", "Mod Comment 8", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_comment8@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_comment8@test.com")
        special_comment = "Great post! 👍 Contains: @#$%^&*()_+{}[]|\\:;'\"<>,.?/~`"
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "approved", "comment": special_comment},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["comment"] == special_comment

    def test_normal_comment_with_rejection(self, client):
        create_test_user("user_comment9@test.com", "User Comment 9")
        create_test_user("mod_comment9@test.com", "Mod Comment 9", models.UserRole.MODERATOR)

        user_token = get_auth_token(client, "user_comment9@test.com")
        create_response = client.post(
            "/blog/",
            json={"title": "Test Blog", "body": "Content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        blog_id = create_response.json()["id"]

        mod_token = get_auth_token(client, "mod_comment9@test.com")
        moderate_response = client.post(
            f"/moderation/blog/{blog_id}",
            json={"decision": "rejected", "comment": "Please improve the content quality."},
            headers={"Authorization": f"Bearer {mod_token}"}
        )
        assert moderate_response.status_code == 200
        assert moderate_response.json()["decision"] == "rejected"
        assert moderate_response.json()["comment"] == "Please improve the content quality."
