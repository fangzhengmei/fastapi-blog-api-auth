def test_draft_visible_to_author(client, user1_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    response = client.get(
        f"/blog/{blog_id}",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == blog_id
    assert response.json()["is_published"] == False


def test_draft_not_visible_to_other_user(client, user2_token, user1_draft_blog):
    blog_id = user1_draft_blog["id"]
    response = client.get(
        f"/blog/{blog_id}",
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code == 404


def test_draft_in_list_for_author(client, user1_token, user1_draft_blog):
    response = client.get(
        "/blog/",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 1
    assert blogs[0]["id"] == user1_draft_blog["id"]
    assert blogs[0]["is_published"] == False


def test_draft_not_in_list_for_other_user(client, user2_token, user1_draft_blog):
    response = client.get(
        "/blog/",
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 0
