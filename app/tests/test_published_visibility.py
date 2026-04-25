def test_published_visible_to_author(client, user1_token, user1_published_blog):
    blog_id = user1_published_blog["id"]
    response = client.get(
        f"/blog/{blog_id}",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == blog_id
    assert response.json()["is_published"] == True


def test_published_visible_to_other_user(client, user2_token, user1_published_blog):
    blog_id = user1_published_blog["id"]
    response = client.get(
        f"/blog/{blog_id}",
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == blog_id
    assert response.json()["is_published"] == True


def test_published_in_list_for_author(client, user1_token, user1_published_blog):
    response = client.get(
        "/blog/",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 1
    assert blogs[0]["id"] == user1_published_blog["id"]
    assert blogs[0]["is_published"] == True


def test_published_in_list_for_other_user(client, user2_token, user1_published_blog):
    response = client.get(
        "/blog/",
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code == 200
    blogs = response.json()
    assert len(blogs) == 1
    assert blogs[0]["id"] == user1_published_blog["id"]
    assert blogs[0]["is_published"] == True
