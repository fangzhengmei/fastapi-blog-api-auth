import pytest


class TestBlogCreateWithTags:
    def test_create_blog_with_existing_tags_by_id(self, client, auth_headers, test_tag, test_tag2):
        response = client.post(
            "/blog/",
            json={
                "title": "Test Blog with Tags",
                "body": "Blog content",
                "tag_ids": [test_tag.id, test_tag2.id]
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["tags"]) == 2
        tag_names = {t["name"] for t in data["tags"]}
        assert test_tag.name in tag_names
        assert test_tag2.name in tag_names

    def test_create_blog_with_new_tags_by_name(self, client, auth_headers):
        response = client.post(
            "/blog/",
            json={
                "title": "Test Blog with New Tags",
                "body": "Blog content",
                "tags": ["NewTag1", "NewTag2"]
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["tags"]) == 2
        tag_names = {t["name"] for t in data["tags"]}
        assert "NewTag1" in tag_names
        assert "NewTag2" in tag_names

        tag_response = client.get("/tags/")
        assert tag_response.status_code == 200
        tag_items = {t["name"] for t in tag_response.json()["items"]}
        assert "NewTag1" in tag_items
        assert "NewTag2" in tag_items

    def test_create_blog_with_mixed_tags(self, client, auth_headers, test_tag):
        response = client.post(
            "/blog/",
            json={
                "title": "Test Blog with Mixed Tags",
                "body": "Blog content",
                "tag_ids": [test_tag.id],
                "tags": ["NewTag"]
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["tags"]) == 2
        tag_names = {t["name"] for t in data["tags"]}
        assert test_tag.name in tag_names
        assert "NewTag" in tag_names

    def test_create_blog_without_tags(self, client, auth_headers):
        response = client.post(
            "/blog/",
            json={
                "title": "Test Blog without Tags",
                "body": "Blog content"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["tags"]) == 0

    def test_create_blog_with_empty_tags_list(self, client, auth_headers):
        response = client.post(
            "/blog/",
            json={
                "title": "Test Blog with Empty Tags",
                "body": "Blog content",
                "tags": []
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["tags"]) == 0

    def test_create_blog_with_nonexistent_tag_ids(self, client, auth_headers):
        response = client.post(
            "/blog/",
            json={
                "title": "Test Blog",
                "body": "Blog content",
                "tag_ids": [99999, 88888]
            },
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestBlogUpdateWithTags:
    def test_update_blog_add_tags(self, client, auth_headers, test_blog, test_tag, test_tag2):
        response = client.put(
            f"/blog/{test_blog.id}",
            json={
                "tag_ids": [test_tag.id, test_tag2.id]
            },
            headers=auth_headers
        )
        assert response.status_code == 202
        data = response.json()
        assert len(data["tags"]) == 2

    def test_update_blog_replace_tags(self, client, auth_headers, blog_with_tags, test_tag3):
        original_tags = {t.name for t in blog_with_tags.tags}
        
        response = client.put(
            f"/blog/{blog_with_tags.id}",
            json={
                "tag_ids": [test_tag3.id]
            },
            headers=auth_headers
        )
        assert response.status_code == 202
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == test_tag3.name

    def test_update_blog_remove_all_tags(self, client, auth_headers, blog_with_tags):
        response = client.put(
            f"/blog/{blog_with_tags.id}",
            json={
                "tags": []
            },
            headers=auth_headers
        )
        assert response.status_code == 202
        data = response.json()
        assert len(data["tags"]) == 0

    def test_update_blog_with_tags_by_name(self, client, auth_headers, test_blog):
        response = client.put(
            f"/blog/{test_blog.id}",
            json={
                "tags": ["UpdateTag1", "UpdateTag2"]
            },
            headers=auth_headers
        )
        assert response.status_code == 202
        data = response.json()
        assert len(data["tags"]) == 2
        tag_names = {t["name"] for t in data["tags"]}
        assert "UpdateTag1" in tag_names
        assert "UpdateTag2" in tag_names

    def test_update_blog_title_and_tags(self, client, auth_headers, test_blog, test_tag):
        response = client.put(
            f"/blog/{test_blog.id}",
            json={
                "title": "Updated Title",
                "tag_ids": [test_tag.id]
            },
            headers=auth_headers
        )
        assert response.status_code == 202
        data = response.json()
        assert data["title"] == "Updated Title"
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == test_tag.name


class TestBlogTagManagement:
    def test_add_tags_to_blog(self, client, auth_headers, test_blog):
        response = client.post(
            f"/blog/{test_blog.id}/tags",
            params={"tag_names": ["Tag1", "Tag2"]},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 2

    def test_add_duplicate_tags(self, client, auth_headers, blog_with_tags):
        original_tag_count = len(blog_with_tags.tags)
        existing_tag = blog_with_tags.tags[0].name
        
        response = client.post(
            f"/blog/{blog_with_tags.id}/tags",
            params={"tag_names": [existing_tag]},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == original_tag_count

    def test_remove_tags_from_blog(self, client, auth_headers, blog_with_tags):
        tag_ids = [t.id for t in blog_with_tags.tags]
        
        response = client.delete(
            f"/blog/{blog_with_tags.id}/tags",
            params={"tag_ids": [tag_ids[0]]},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == len(tag_ids) - 1

    def test_remove_all_tags_from_blog(self, client, auth_headers, blog_with_tags):
        tag_ids = [t.id for t in blog_with_tags.tags]
        
        response = client.delete(
            f"/blog/{blog_with_tags.id}/tags",
            params={"tag_ids": tag_ids},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tags"]) == 0

    def test_add_tags_to_other_user_blog_forbidden(self, client, auth_headers_user2, test_blog):
        response = client.post(
            f"/blog/{test_blog.id}/tags",
            params={"tag_names": ["ForbiddenTag"]},
            headers=auth_headers_user2
        )
        assert response.status_code == 403

    def test_remove_tags_from_other_user_blog_forbidden(self, client, auth_headers_user2, blog_with_tags):
        tag_ids = [t.id for t in blog_with_tags.tags]
        
        response = client.delete(
            f"/blog/{blog_with_tags.id}/tags",
            params={"tag_ids": tag_ids},
            headers=auth_headers_user2
        )
        assert response.status_code == 403


class TestBlogTagsAuthorization:
    def test_create_blog_with_tags_unauthorized(self, client):
        response = client.post(
            "/blog/",
            json={
                "title": "Unauthorized Blog",
                "body": "Content",
                "tags": ["Tag"]
            }
        )
        assert response.status_code == 401

    def test_update_blog_tags_unauthorized(self, client, test_blog):
        response = client.put(
            f"/blog/{test_blog.id}",
            json={
                "tags": ["UnauthorizedTag"]
            }
        )
        assert response.status_code == 401

    def test_update_other_user_blog_forbidden(self, client, auth_headers_user2, test_blog):
        response = client.put(
            f"/blog/{test_blog.id}",
            json={
                "title": "Hacked Title",
                "tags": ["HackedTag"]
            },
            headers=auth_headers_user2
        )
        assert response.status_code == 403

    def test_delete_other_user_blog_forbidden(self, client, auth_headers_user2, test_blog):
        response = client.delete(
            f"/blog/{test_blog.id}",
            headers=auth_headers_user2
        )
        assert response.status_code == 403