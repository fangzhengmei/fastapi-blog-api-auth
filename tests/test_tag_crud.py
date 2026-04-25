import pytest


class TestTagCreate:
    def test_create_tag_success(self, client, auth_headers):
        response = client.post(
            "/tags/",
            json={"name": "Python", "description": "Python programming"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Python"
        assert data["slug"] == "python"
        assert data["description"] == "Python programming"
        assert "id" in data

    def test_create_tag_with_special_chars(self, client, auth_headers):
        response = client.post(
            "/tags/",
            json={"name": "C++ Programming!", "description": "C++ language"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "C++ Programming!"
        assert data["slug"] == "c-programming"

    def test_create_tag_duplicate_name(self, client, auth_headers, test_tag):
        response = client.post(
            "/tags/",
            json={"name": test_tag.name, "description": "Duplicate"},
            headers=auth_headers
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_tag_without_description(self, client, auth_headers):
        response = client.post(
            "/tags/",
            json={"name": "NoDescription"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "NoDescription"
        assert data["description"] is None

    def test_create_tag_unauthorized(self, client):
        response = client.post(
            "/tags/",
            json={"name": "UnauthorizedTag"}
        )
        assert response.status_code == 401


class TestTagRead:
    def test_get_all_tags(self, client, test_tag, test_tag2):
        response = client.get("/tags/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_all_tags_pagination(self, client, test_db):
        from blog import models
        for i in range(15):
            tag = models.Tag(name=f"Tag{i}", slug=f"tag{i}")
            test_db.add(tag)
        test_db.commit()

        response = client.get("/tags/?page=2&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 10
        assert data["total"] == 15
        assert data["total_pages"] == 2
        assert len(data["items"]) == 5

    def test_get_all_tags_sort_by_name_asc(self, client, test_db):
        from blog import models
        tags = ["Zebra", "Apple", "Banana"]
        for name in tags:
            test_db.add(models.Tag(name=name, slug=name.lower()))
        test_db.commit()

        response = client.get("/tags/?sort_by=name&order=asc")
        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert names == ["Apple", "Banana", "Zebra"]

    def test_get_all_tags_sort_by_name_desc(self, client, test_db):
        from blog import models
        tags = ["Zebra", "Apple", "Banana"]
        for name in tags:
            test_db.add(models.Tag(name=name, slug=name.lower()))
        test_db.commit()

        response = client.get("/tags/?sort_by=name&order=desc")
        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert names == ["Zebra", "Banana", "Apple"]

    def test_get_tag_by_id_success(self, client, test_tag):
        response = client.get(f"/tags/{test_tag.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_tag.id
        assert data["name"] == test_tag.name

    def test_get_tag_by_id_not_found(self, client):
        response = client.get("/tags/99999")
        assert response.status_code == 404

    def test_get_tag_by_slug_success(self, client, test_tag):
        response = client.get(f"/tags/slug/{test_tag.slug}")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == test_tag.slug
        assert data["name"] == test_tag.name

    def test_get_tag_by_slug_not_found(self, client):
        response = client.get("/tags/slug/nonexistent-slug")
        assert response.status_code == 404


class TestTagUpdate:
    def test_update_tag_success(self, client, auth_headers, test_tag):
        response = client.put(
            f"/tags/{test_tag.id}",
            json={"name": "Updated Python", "description": "Updated description"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Python"
        assert data["slug"] == "updated-python"
        assert data["description"] == "Updated description"

    def test_update_tag_name_only(self, client, auth_headers, test_tag):
        original_description = test_tag.description
        response = client.put(
            f"/tags/{test_tag.id}",
            json={"name": "NewName"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NewName"
        assert data["description"] == original_description

    def test_update_tag_description_only(self, client, auth_headers, test_tag):
        original_name = test_tag.name
        response = client.put(
            f"/tags/{test_tag.id}",
            json={"description": "New description"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == original_name
        assert data["description"] == "New description"

    def test_update_tag_duplicate_name(self, client, auth_headers, test_tag, test_tag2):
        response = client.put(
            f"/tags/{test_tag.id}",
            json={"name": test_tag2.name},
            headers=auth_headers
        )
        assert response.status_code == 409

    def test_update_tag_not_found(self, client, auth_headers):
        response = client.put(
            "/tags/99999",
            json={"name": "Nonexistent"},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_tag_unauthorized(self, client, test_tag):
        response = client.put(
            f"/tags/{test_tag.id}",
            json={"name": "Unauthorized Update"}
        )
        assert response.status_code == 401


class TestTagDelete:
    def test_delete_tag_success(self, client, auth_headers, test_tag):
        response = client.delete(f"/tags/{test_tag.id}", headers=auth_headers)
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        get_response = client.get(f"/tags/{test_tag.id}")
        assert get_response.status_code == 404

    def test_delete_tag_not_found(self, client, auth_headers):
        response = client.delete("/tags/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_tag_unauthorized(self, client, test_tag):
        response = client.delete(f"/tags/{test_tag.id}")
        assert response.status_code == 401