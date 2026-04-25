def test_anonymous_user_cannot_access_drafts(client):
    response = client.get("/blog/drafts")
    assert response.status_code == 401


def test_user_can_get_own_drafts(client, test_db, user1_token):
    client.post(
        "/blog/",
        json={"title": "Draft 1", "body": "Draft 1 content", "is_published": False},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    client.post(
        "/blog/",
        json={"title": "Draft 2", "body": "Draft 2 content", "is_published": False},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    
    response = client.get(
        "/blog/drafts",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 200
    drafts = response.json()
    assert len(drafts) == 2
    for draft in drafts:
        assert draft["is_published"] == False


def test_drafts_does_not_include_published(client, test_db, user1_token):
    client.post(
        "/blog/",
        json={"title": "Draft", "body": "Draft content", "is_published": False},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    client.post(
        "/blog/",
        json={"title": "Published", "body": "Published content", "is_published": True},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    
    response = client.get(
        "/blog/drafts",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 200
    drafts = response.json()
    assert len(drafts) == 1
    assert drafts[0]["title"] == "Draft"
    assert drafts[0]["is_published"] == False


def test_user_cannot_see_other_users_drafts(client, test_db, user1_token, user2_token):
    client.post(
        "/blog/",
        json={"title": "User1 Draft", "body": "User1 draft content", "is_published": False},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    
    response = client.get(
        "/blog/drafts",
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code == 200
    drafts = response.json()
    assert len(drafts) == 0


def test_compare_drafts_vs_all(client, test_db, user1_token):
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
    
    drafts_response = client.get(
        "/blog/drafts",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    all_response = client.get(
        "/blog/",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    
    assert drafts_response.status_code == 200
    assert all_response.status_code == 200
    
    drafts = drafts_response.json()
    all_blogs = all_response.json()
    
    assert len(drafts) == 2
    assert len(all_blogs) == 4
    
    for draft in drafts:
        assert draft["is_published"] == False
