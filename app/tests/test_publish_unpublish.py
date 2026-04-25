def test_author_can_publish_draft(client, user1_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    
    assert user1_draft_blog["is_published"] == False
    
    response = client.post(
        f"/blog/{blog_id}/publish",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_published"] == True


def test_author_can_unpublish_published_blog(client, user1_token, user1_published_blog):
    blog_id = user1_published_blog["id"]
    
    assert user1_published_blog["is_published"] == True
    
    response = client.post(
        f"/blog/{blog_id}/unpublish",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_published"] == False


def test_other_user_cannot_publish_blog(client, user2_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    
    response = client.post(
        f"/blog/{blog_id}/publish",
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code == 403


def test_other_user_cannot_unpublish_blog(client, user2_token, user1_published_blog):
    blog_id = user1_published_blog["id"]
    
    response = client.post(
        f"/blog/{blog_id}/unpublish",
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code == 403


def test_create_draft_by_default(client, user1_token):
    response = client.post(
        "/blog/",
        json={"title": "Test Blog", "body": "Test body"},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 201
    assert response.json()["is_published"] == False


def test_create_published_blog(client, user1_token):
    response = client.post(
        "/blog/",
        json={"title": "Published Blog", "body": "Published body", "is_published": True},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 201
    assert response.json()["is_published"] == True
