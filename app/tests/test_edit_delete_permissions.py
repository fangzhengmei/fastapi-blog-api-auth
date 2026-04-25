def test_author_can_edit_own_blog(client, user1_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    response = client.put(
        f"/blog/{blog_id}",
        json={"title": "Updated Title", "body": "Updated body", "is_published": False},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 202
    
    response = client.get(
        f"/blog/{blog_id}",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


def test_other_user_cannot_edit_blog(client, user2_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    response = client.put(
        f"/blog/{blog_id}",
        json={"title": "Hacked Title", "body": "Hacked body", "is_published": False},
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code == 403


def test_author_can_delete_own_blog(client, user1_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    response = client.delete(
        f"/blog/{blog_id}",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 204
    
    response = client.get(
        f"/blog/{blog_id}",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 404


def test_other_user_cannot_delete_blog(client, user2_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    response = client.delete(
        f"/blog/{blog_id}",
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code == 403
