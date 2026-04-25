import pytest


class TestTagValidation:
    def test_create_tag_name_too_long(self, client, auth_headers):
        long_name = "a" * 51
        response = client.post(
            "/tags/",
            json={"name": long_name},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_tag_name_too_short(self, client, auth_headers):
        response = client.post(
            "/tags/",
            json={"name": ""},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_tag_description_too_long(self, client, auth_headers):
        long_description = "a" * 201
        response = client.post(
            "/tags/",
            json={"name": "ValidTag", "description": long_description},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_tag_name_too_long(self, client, auth_headers, test_tag):
        long_name = "a" * 51
        response = client.put(
            f"/tags/{test_tag.id}",
            json={"name": long_name},
            headers=auth_headers
        )
        assert response.status_code == 422


class TestTagSlugGeneration:
    def test_slug_generation_lowercase(self, client, auth_headers):
        response = client.post(
            "/tags/",
            json={"name": "PYTHON PROGRAMMING"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "python-programming"

    def test_slug_generation_special_chars(self, client, auth_headers):
        response = client.post(
            "/tags/",
            json={"name": "C# & .NET Programming!"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert "c" in data["slug"]
        assert "net" in data["slug"]
        assert "programming" in data["slug"]

    def test_slug_generation_spaces(self, client, auth_headers):
        response = client.post(
            "/tags/",
            json={"name": "   Machine   Learning   "},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "machine-learning"

    def test_slug_generation_duplicate_names_different_cases(self, client, auth_headers):
        response1 = client.post(
            "/tags/",
            json={"name": "Python"},
            headers=auth_headers
        )
        assert response1.status_code == 201

        response2 = client.post(
            "/tags/",
            json={"name": "python"},
            headers=auth_headers
        )
        assert response2.status_code == 409

    def test_update_tag_updates_slug(self, client, auth_headers, test_tag):
        original_slug = test_tag.slug
        
        response = client.put(
            f"/tags/{test_tag.id}",
            json={"name": "New Updated Name"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "new-updated-name"
        assert data["slug"] != original_slug


class TestEdgeCases:
    def test_pagination_page_less_than_1(self, client, auth_headers):
        response = client.get(
            "/blog/?page=0",
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_pagination_per_page_less_than_1(self, client, auth_headers):
        response = client.get(
            "/blog/?per_page=0",
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_pagination_per_page_too_large(self, client, auth_headers):
        response = client.get(
            "/blog/?per_page=101",
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_invalid_sort_by_parameter(self, client, auth_headers):
        response = client.get(
            "/tags/?sort_by=invalid_field",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_invalid_order_parameter(self, client, auth_headers):
        response = client.get(
            "/tags/?order=invalid",
            headers=auth_headers
        )
        assert response.status_code == 200

    def test_create_blog_with_same_tag_multiple_times(self, client, auth_headers):
        response = client.post(
            "/blog/",
            json={
                "title": "Test Blog",
                "body": "Content",
                "tags": ["DuplicateTag", "DuplicateTag", "DuplicateTag"]
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["tags"]) == 1
        assert data["tags"][0]["name"] == "DuplicateTag"

    def test_create_blog_with_whitespace_tags(self, client, auth_headers):
        response = client.post(
            "/blog/",
            json={
                "title": "Test Blog",
                "body": "Content",
                "tags": ["   ", "  Tag1  ", "", "Tag2"]
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["tags"]) == 2
        tag_names = {t["name"] for t in data["tags"]}
        assert "Tag1" in tag_names
        assert "Tag2" in tag_names

    def test_remove_nonexistent_tags_from_blog(self, client, auth_headers, blog_with_tags):
        response = client.delete(
            f"/blog/{blog_with_tags.id}/tags",
            params={"tag_ids": [99999, 88888]},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        original_tag_count = len(blog_with_tags.tags)
        assert len(data["tags"]) == original_tag_count


class TestAuthorization:
    def test_access_protected_endpoint_without_token(self, client):
        endpoints = [
            ("POST", "/tags/", {"name": "Test"}),
            ("PUT", "/tags/1", {"name": "Test"}),
            ("DELETE", "/tags/1", None),
            ("POST", "/blog/", {"title": "Test", "body": "Test"}),
            ("PUT", "/blog/1", {"title": "Test"}),
            ("DELETE", "/blog/1", None),
        ]
        
        for method, path, json_data in endpoints:
            if method == "POST":
                response = client.post(path, json=json_data)
            elif method == "PUT":
                response = client.put(path, json=json_data)
            elif method == "DELETE":
                response = client.delete(path)
            else:
                continue
            
            assert response.status_code == 401

    def test_access_protected_endpoint_with_invalid_token(self, client):
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
        
        response = client.post(
            "/tags/",
            json={"name": "Test"},
            headers=invalid_headers
        )
        assert response.status_code == 401

    def test_access_protected_endpoint_with_malformed_token(self, client):
        malformed_headers = {"Authorization": "NotBearer token"}
        
        response = client.post(
            "/tags/",
            json={"name": "Test"},
            headers=malformed_headers
        )
        assert response.status_code == 401


class TestBlogOperations:
    def test_get_nonexistent_blog(self, client, auth_headers):
        response = client.get(
            "/blog/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_nonexistent_blog(self, client, auth_headers):
        response = client.put(
            "/blog/99999",
            json={"title": "Test"},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_delete_nonexistent_blog(self, client, auth_headers):
        response = client.delete(
            "/blog/99999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_blog_without_title(self, client, auth_headers):
        response = client.post(
            "/blog/",
            json={"body": "Content without title"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_blog_without_body(self, client, auth_headers):
        response = client.post(
            "/blog/",
            json={"title": "Title without body"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_blog_with_empty_title(self, client, auth_headers, test_blog):
        response = client.put(
            f"/blog/{test_blog.id}",
            json={"title": ""},
            headers=auth_headers
        )
        assert response.status_code == 422


class TestTagOperations:
    def test_tag_creates_only_once(self, client, auth_headers, test_db):
        from blog import models
        
        response1 = client.post(
            "/blog/",
            json={"title": "Blog 1", "body": "Content", "tags": ["ReusableTag"]},
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        response2 = client.post(
            "/blog/",
            json={"title": "Blog 2", "body": "Content", "tags": ["ReusableTag"]},
            headers=auth_headers
        )
        assert response2.status_code == 201
        
        tag_count = test_db.query(models.Tag).filter(models.Tag.name == "ReusableTag").count()
        assert tag_count == 1

    def test_tag_deletion_cascades(self, client, auth_headers, blog_with_tags):
        tag_ids = [t.id for t in blog_with_tags.tags]
        
        for tag_id in tag_ids:
            response = client.delete(f"/tags/{tag_id}", headers=auth_headers)
            assert response.status_code == 200

        blog_response = client.get(
            f"/blog/{blog_with_tags.id}",
            headers=auth_headers
        )
        assert blog_response.status_code == 200
        data = blog_response.json()
        assert len(data["tags"]) == 0

    def test_blog_deletion_doesnt_delete_tags(self, client, auth_headers, blog_with_tags, test_db):
        from blog import models
        
        tag_ids = [t.id for t in blog_with_tags.tags]
        
        client.delete(f"/blog/{blog_with_tags.id}", headers=auth_headers)
        
        for tag_id in tag_ids:
            tag = test_db.query(models.Tag).filter(models.Tag.id == tag_id).first()
            assert tag is not None


class TestPaginationEdgeCases:
    def test_page_exceeds_total_pages(self, client, auth_headers, test_db, test_user, test_tag):
        from blog import models
        
        for i in range(5):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            blog.tags = [test_tag]
            test_db.add(blog)
        test_db.commit()

        response = client.get(
            f"/blog/?tag_id={test_tag.id}&page=10&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 10
        assert data["total"] == 5
        assert data["total_pages"] == 1
        assert len(data["items"]) == 0

    def test_per_page_equal_to_total(self, client, auth_headers, test_db, test_user):
        from blog import models
        
        for i in range(10):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            test_db.add(blog)
        test_db.commit()

        response = client.get(
            "/blog/?per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["total"] == 10
        assert data["total_pages"] == 1
        assert len(data["items"]) == 10