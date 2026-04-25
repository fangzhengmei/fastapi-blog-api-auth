import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCommentCreate:
    def test_create_comment_success(self, test_db, client, auth_header_user1):
        from blog import models
        blog = test_db.query(models.Blog).first()
        response = client.post(
            "/comment/",
            json={"content": "This is a test comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a test comment"
        assert data["blog_id"] == blog.id
        assert "id" in data
        assert "created_at" in data

    def test_create_comment_without_auth(self, test_db, client):
        from blog import models
        blog = test_db.query(models.Blog).first()
        response = client.post(
            "/comment/",
            json={"content": "This is a test comment", "blog_id": blog.id}
        )
        assert response.status_code == 401

    def test_create_comment_nonexistent_blog(self, test_db, client, auth_header_user1):
        response = client.post(
            "/comment/",
            json={"content": "This is a test comment", "blog_id": 9999},
            headers=auth_header_user1
        )
        assert response.status_code == 404

    def test_create_reply_comment(self, test_db, client, auth_header_user1, auth_header_user2):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        response1 = client.post(
            "/comment/",
            json={"content": "Parent comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        assert response1.status_code == 201
        parent_comment_id = response1.json()["id"]
        
        response2 = client.post(
            "/comment/",
            json={
                "content": "Reply comment", 
                "blog_id": blog.id, 
                "parent_id": parent_comment_id
            },
            headers=auth_header_user2
        )
        assert response2.status_code == 201
        data = response2.json()
        assert data["parent_id"] == parent_comment_id


class TestCommentRead:
    def test_get_comments_by_blog_success(self, test_db, client, auth_header_user1):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        for i in range(3):
            client.post(
                "/comment/",
                json={"content": f"Comment {i+1}", "blog_id": blog.id},
                headers=auth_header_user1
            )
        
        response = client.get(
            f"/comment/blog/{blog.id}",
            headers=auth_header_user1
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_comments_by_blog_nonexistent(self, test_db, client, auth_header_user1):
        response = client.get(
            "/comment/blog/9999",
            headers=auth_header_user1
        )
        assert response.status_code == 404

    def test_get_single_comment_success(self, test_db, client, auth_header_user1):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        create_response = client.post(
            "/comment/",
            json={"content": "Test comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.get(
            f"/comment/{comment_id}",
            headers=auth_header_user1
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == comment_id
        assert data["content"] == "Test comment"

    def test_get_single_comment_nonexistent(self, test_db, client, auth_header_user1):
        response = client.get(
            "/comment/9999",
            headers=auth_header_user1
        )
        assert response.status_code == 404


class TestCommentUpdate:
    def test_update_comment_success(self, test_db, client, auth_header_user1):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        create_response = client.post(
            "/comment/",
            json={"content": "Original content", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.put(
            f"/comment/{comment_id}",
            json={"content": "Updated content"},
            headers=auth_header_user1
        )
        assert response.status_code == 202
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["id"] == comment_id

    def test_update_comment_nonexistent(self, test_db, client, auth_header_user1):
        response = client.put(
            "/comment/9999",
            json={"content": "Updated content"},
            headers=auth_header_user1
        )
        assert response.status_code == 404

    def test_update_comment_without_auth(self, test_db, client, auth_header_user1):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        create_response = client.post(
            "/comment/",
            json={"content": "Original content", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.put(
            f"/comment/{comment_id}",
            json={"content": "Updated content"}
        )
        assert response.status_code == 401


class TestCommentDelete:
    def test_delete_comment_success(self, test_db, client, auth_header_user1):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        create_response = client.post(
            "/comment/",
            json={"content": "Comment to delete", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.delete(
            f"/comment/{comment_id}",
            headers=auth_header_user1
        )
        assert response.status_code == 204
        
        get_response = client.get(
            f"/comment/{comment_id}",
            headers=auth_header_user1
        )
        assert get_response.status_code == 404

    def test_delete_comment_nonexistent(self, test_db, client, auth_header_user1):
        response = client.delete(
            "/comment/9999",
            headers=auth_header_user1
        )
        assert response.status_code == 404

    def test_delete_comment_without_auth(self, test_db, client, auth_header_user1):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        create_response = client.post(
            "/comment/",
            json={"content": "Comment to delete", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.delete(
            f"/comment/{comment_id}"
        )
        assert response.status_code == 401


class TestCommentPermission:
    def test_update_other_user_comment_should_fail(self, test_db, client, auth_header_user1, auth_header_user2):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        create_response = client.post(
            "/comment/",
            json={"content": "User1's comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.put(
            f"/comment/{comment_id}",
            json={"content": "User2 trying to update"},
            headers=auth_header_user2
        )
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    def test_delete_other_user_comment_should_fail(self, test_db, client, auth_header_user1, auth_header_user2):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        create_response = client.post(
            "/comment/",
            json={"content": "User1's comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.delete(
            f"/comment/{comment_id}",
            headers=auth_header_user2
        )
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    def test_other_user_can_view_comment(self, test_db, client, auth_header_user1, auth_header_user2):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        create_response = client.post(
            "/comment/",
            json={"content": "User1's comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.get(
            f"/comment/{comment_id}",
            headers=auth_header_user2
        )
        assert response.status_code == 200
        assert response.json()["content"] == "User1's comment"

    def test_other_user_can_reply_to_comment(self, test_db, client, auth_header_user1, auth_header_user2):
        from blog import models
        blog = test_db.query(models.Blog).first()
        
        response1 = client.post(
            "/comment/",
            json={"content": "User1's comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        parent_comment_id = response1.json()["id"]
        
        response2 = client.post(
            "/comment/",
            json={
                "content": "User2's reply", 
                "blog_id": blog.id, 
                "parent_id": parent_comment_id
            },
            headers=auth_header_user2
        )
        assert response2.status_code == 201
        data = response2.json()
        assert data["parent_id"] == parent_comment_id
        assert data["content"] == "User2's reply"
