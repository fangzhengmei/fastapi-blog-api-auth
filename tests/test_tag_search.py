import pytest


class TestBlogFilterByTag:
    def test_filter_blogs_by_tag_id(self, client, auth_headers, multiple_blogs_with_tags, test_tag):
        response = client.get(
            f"/blog/?tag_id={test_tag.id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 3
        for blog in data["items"]:
            tag_names = {t["name"] for t in blog["tags"]}
            assert test_tag.name in tag_names

    def test_filter_blogs_by_tag_slug(self, client, auth_headers, multiple_blogs_with_tags, test_tag2):
        response = client.get(
            f"/blog/?tag_slug={test_tag2.slug}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 3
        for blog in data["items"]:
            tag_names = {t["slug"] for t in blog["tags"]}
            assert test_tag2.slug in tag_names

    def test_filter_blogs_by_tag_name(self, client, auth_headers, multiple_blogs_with_tags, test_tag3):
        response = client.get(
            f"/blog/?tag_name={test_tag3.name}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 1
        tag_names = {t["name"] for t in data["items"][0]["tags"]}
        assert test_tag3.name in tag_names

    def test_filter_blogs_by_nonexistent_tag(self, client, auth_headers):
        response = client.get(
            "/blog/?tag_id=99999",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_filter_blogs_by_tag_with_pagination(self, client, auth_headers, test_db, test_user, test_tag):
        from blog import models
        for i in range(15):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            blog.tags = [test_tag]
            test_db.add(blog)
        test_db.commit()

        response = client.get(
            f"/blog/?tag_id={test_tag.id}&page=2&per_page=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["total"] == 15
        assert data["total_pages"] == 2
        assert len(data["items"]) == 5


class TestTagBlogsEndpoint:
    def test_get_blogs_by_tag_id_endpoint(self, client, multiple_blogs_with_tags, test_tag):
        response = client.get(f"/tags/{test_tag.id}/blogs")
        assert response.status_code == 200
        data = response.json()
        
        assert "tag" in data
        assert "blogs" in data
        assert data["total"] == 3
        assert len(data["blogs"]) == 3
        assert data["tag"]["id"] == test_tag.id

    def test_get_blogs_by_tag_slug_endpoint(self, client, multiple_blogs_with_tags, test_tag2):
        response = client.get(f"/tags/slug/{test_tag2.slug}/blogs")
        assert response.status_code == 200
        data = response.json()
        
        assert data["tag"]["slug"] == test_tag2.slug
        assert data["total"] == 3

    def test_get_blogs_by_tag_id_pagination(self, client, test_db, test_user, test_tag):
        from blog import models
        for i in range(15):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            blog.tags = [test_tag]
            test_db.add(blog)
        test_db.commit()

        response = client.get(f"/tags/{test_tag.id}/blogs?page=2&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["total"] == 15
        assert data["total_pages"] == 2
        assert len(data["blogs"]) == 5

    def test_get_blogs_by_nonexistent_tag_id(self, client):
        response = client.get("/tags/99999/blogs")
        assert response.status_code == 404

    def test_get_blogs_by_nonexistent_tag_slug(self, client):
        response = client.get("/tags/slug/nonexistent/blogs")
        assert response.status_code == 404

    def test_tag_with_no_blogs(self, client, test_tag):
        response = client.get(f"/tags/{test_tag.id}/blogs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["blogs"]) == 0


class TestTagSearchAndPopular:
    def test_search_tags_exact_match(self, client, test_tag, test_tag2, test_tag3):
        response = client.get("/tags/search?keyword=Python")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["name"] == "Python"

    def test_search_tags_partial_match(self, client, test_db):
        from blog import models
        tags = ["JavaScript", "Java", "Python", "TypeScript"]
        for name in tags:
            test_db.add(models.Tag(name=name, slug=name.lower()))
        test_db.commit()

        response = client.get("/tags/search?keyword=Java")
        assert response.status_code == 200
        data = response.json()
        
        names = {t["name"] for t in data}
        assert "Java" in names
        assert "JavaScript" in names

    def test_search_tags_case_insensitive(self, client, test_tag):
        response = client.get("/tags/search?keyword=python")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["name"] == "Python"

    def test_search_tags_no_results(self, client):
        response = client.get("/tags/search?keyword=NonexistentTag12345")
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_search_tags_limit(self, client, test_db):
        from blog import models
        for i in range(20):
            test_db.add(models.Tag(name=f"Tag{i}", slug=f"tag{i}"))
        test_db.commit()

        response = client.get("/tags/search?keyword=Tag&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_get_popular_tags(self, client, multiple_blogs_with_tags, test_tag, test_tag2, test_tag3):
        response = client.get("/tags/popular")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) >= 3
        
        blog_counts = {t["name"]: t["blog_count"] for t in data}
        assert blog_counts[test_tag.name] == 3
        assert blog_counts[test_tag2.name] == 3
        assert blog_counts[test_tag3.name] == 1

    def test_get_popular_tags_sorted_by_count(self, client, multiple_blogs_with_tags, test_tag, test_tag2, test_tag3):
        response = client.get("/tags/popular")
        assert response.status_code == 200
        data = response.json()
        
        for i in range(len(data) - 1):
            assert data[i]["blog_count"] >= data[i + 1]["blog_count"]

    def test_get_popular_tags_limit(self, client, test_db, test_user):
        from blog import models
        for i in range(10):
            tag = models.Tag(name=f"PopTag{i}", slug=f"poptag{i}")
            test_db.add(tag)
            test_db.commit()
            test_db.refresh(tag)
            
            for j in range(i):
                blog = models.Blog(
                    title=f"Blog for {tag.name}",
                    body=f"Content {j}",
                    user_id=test_user.id
                )
                blog.tags = [tag]
                test_db.add(blog)
        test_db.commit()

        response = client.get("/tags/popular?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_get_popular_tags_no_blogs(self, client, test_tag, test_tag2):
        response = client.get("/tags/popular")
        assert response.status_code == 200
        data = response.json()
        
        for tag in data:
            assert tag["blog_count"] == 0


class TestBlogSorting:
    def test_get_blogs_sorted_by_created_at_desc(self, client, auth_headers, test_db, test_user):
        from blog import models
        for i in range(5):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            test_db.add(blog)
        test_db.commit()

        response = client.get(
            "/blog/?sort_by=created_at&order=desc",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for i in range(len(data["items"]) - 1):
            current = data["items"][i]
            next_item = data["items"][i + 1]
            assert current["created_at"] >= next_item["created_at"]

    def test_get_blogs_sorted_by_created_at_asc(self, client, auth_headers, test_db, test_user):
        from blog import models
        for i in range(5):
            blog = models.Blog(
                title=f"Blog {i}",
                body=f"Content {i}",
                user_id=test_user.id
            )
            test_db.add(blog)
        test_db.commit()

        response = client.get(
            "/blog/?sort_by=created_at&order=asc",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for i in range(len(data["items"]) - 1):
            current = data["items"][i]
            next_item = data["items"][i + 1]
            assert current["created_at"] <= next_item["created_at"]

    def test_get_blogs_sorted_by_title_asc(self, client, auth_headers, test_db, test_user):
        from blog import models
        titles = ["Zebra", "Apple", "Banana", "Cherry"]
        for title in titles:
            blog = models.Blog(
                title=title,
                body=f"Content for {title}",
                user_id=test_user.id
            )
            test_db.add(blog)
        test_db.commit()

        response = client.get(
            "/blog/?sort_by=title&order=asc",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        returned_titles = [item["title"] for item in data["items"]]
        assert returned_titles == ["Apple", "Banana", "Cherry", "Zebra"]

    def test_get_blogs_sorted_by_title_desc(self, client, auth_headers, test_db, test_user):
        from blog import models
        titles = ["Zebra", "Apple", "Banana", "Cherry"]
        for title in titles:
            blog = models.Blog(
                title=title,
                body=f"Content for {title}",
                user_id=test_user.id
            )
            test_db.add(blog)
        test_db.commit()

        response = client.get(
            "/blog/?sort_by=title&order=desc",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        returned_titles = [item["title"] for item in data["items"]]
        assert returned_titles == ["Zebra", "Cherry", "Banana", "Apple"]