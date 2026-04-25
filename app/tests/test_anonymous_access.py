def test_anonymous_user_cannot_see_draft_in_list(client, test_db, user1_token, user1_draft_blog):
    response = client.get("/blog/")
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 0


def test_anonymous_user_cannot_access_draft_detail(client, test_db, user1_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    response = client.get(f"/blog/{blog_id}")
    assert response.status_code == 404


def test_anonymous_user_can_see_published_in_list(client, test_db, user1_token, user1_published_blog):
    response = client.get("/blog/")
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 1
    assert blogs[0]["id"] == user1_published_blog["id"]
    assert blogs[0]["is_published"] == True


def test_anonymous_user_can_access_published_detail(client, test_db, user1_token, user1_published_blog):
    blog_id = user1_published_blog["id"]
    response = client.get(f"/blog/{blog_id}")
    assert response.status_code == 200
    assert response.json()["id"] == blog_id
    assert response.json()["is_published"] == True


def test_anonymous_user_sees_only_published_in_list(client, test_db, user1_token):
    client.post(
        "/blog/",
        json={"title": "Draft 1", "body": "Draft content", "is_published": False},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    client.post(
        "/blog/",
        json={"title": "Published 1", "body": "Published content", "is_published": True},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    client.post(
        "/blog/",
        json={"title": "Draft 2", "body": "Another draft", "is_published": False},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    client.post(
        "/blog/",
        json={"title": "Published 2", "body": "Another published", "is_published": True},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    
    response = client.get("/blog/")
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 2
    for blog in blogs:
        assert blog["is_published"] == True


def test_anonymous_user_cannot_create_blog(client):
    response = client.post(
        "/blog/",
        json={"title": "Test", "body": "Test body", "is_published": True}
    )
    assert response.status_code == 401


def test_anonymous_user_cannot_update_blog(client, test_db, user1_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    response = client.put(
        f"/blog/{blog_id}",
        json={"title": "Hacked", "body": "Hacked body", "is_published": True}
    )
    assert response.status_code == 401


def test_anonymous_user_cannot_delete_blog(client, test_db, user1_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    response = client.delete(f"/blog/{blog_id}")
    assert response.status_code == 401


def test_anonymous_user_cannot_publish_blog(client, test_db, user1_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    response = client.post(f"/blog/{blog_id}/publish")
    assert response.status_code == 401


def test_anonymous_user_cannot_unpublish_blog(client, test_db, user1_token, user1_published_blog):
    blog_id = user1_published_blog["id"]
    response = client.post(f"/blog/{blog_id}/unpublish")
    assert response.status_code == 401
