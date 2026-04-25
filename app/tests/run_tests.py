import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from blog import models, schemas
from blog.database import Base, get_db
from blog.hashing import Hash
from blog.token import create_access_token
from main import app


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    user1 = models.User(
        name="testuser1",
        email="test1@example.com",
        password=Hash.bcrypt("testpassword1")
    )
    user2 = models.User(
        name="testuser2",
        email="test2@example.com",
        password=Hash.bcrypt("testpassword2")
    )
    db.add(user1)
    db.add(user2)
    db.commit()
    db.refresh(user1)
    db.refresh(user2)
    
    blog = models.Blog(
        title="Test Blog",
        body="This is a test blog post",
        user_id=user1.id
    )
    db.add(blog)
    db.commit()
    db.refresh(blog)
    
    return db, user1, user2, blog


def teardown_test_db():
    Base.metadata.drop_all(bind=engine)


def get_auth_header(user_email):
    access_token = create_access_token(data={"sub": user_email})
    return {"Authorization": f"Bearer {access_token}"}


def test_create_comment_success():
    db, user1, user2, blog = setup_test_db()
    try:
        auth_header = get_auth_header(user1.email)
        response = client.post(
            "/comment/",
            json={"content": "This is a test comment", "blog_id": blog.id},
            headers=auth_header
        )
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
        data = response.json()
        assert data["content"] == "This is a test comment"
        assert data["blog_id"] == blog.id
        assert "id" in data
        assert "created_at" in data
        print("✅ test_create_comment_success PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_create_comment_success FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def test_create_comment_without_auth():
    db, user1, user2, blog = setup_test_db()
    try:
        response = client.post(
            "/comment/",
            json={"content": "This is a test comment", "blog_id": blog.id}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ test_create_comment_without_auth PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_create_comment_without_auth FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def test_create_comment_nonexistent_blog():
    db, user1, user2, blog = setup_test_db()
    try:
        auth_header = get_auth_header(user1.email)
        response = client.post(
            "/comment/",
            json={"content": "This is a test comment", "blog_id": 9999},
            headers=auth_header
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ test_create_comment_nonexistent_blog PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_create_comment_nonexistent_blog FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def test_get_comments_by_blog_success():
    db, user1, user2, blog = setup_test_db()
    try:
        auth_header = get_auth_header(user1.email)
        for i in range(3):
            client.post(
                "/comment/",
                json={"content": f"Comment {i+1}", "blog_id": blog.id},
                headers=auth_header
            )
        
        response = client.get(
            f"/comment/blog/{blog.id}",
            headers=auth_header
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert len(data) == 3, f"Expected 3 comments, got {len(data)}"
        print("✅ test_get_comments_by_blog_success PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_get_comments_by_blog_success FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def test_get_single_comment_success():
    db, user1, user2, blog = setup_test_db()
    try:
        auth_header = get_auth_header(user1.email)
        create_response = client.post(
            "/comment/",
            json={"content": "Test comment", "blog_id": blog.id},
            headers=auth_header
        )
        comment_id = create_response.json()["id"]
        
        response = client.get(
            f"/comment/{comment_id}",
            headers=auth_header
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["id"] == comment_id
        assert data["content"] == "Test comment"
        print("✅ test_get_single_comment_success PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_get_single_comment_success FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def test_update_comment_success():
    db, user1, user2, blog = setup_test_db()
    try:
        auth_header = get_auth_header(user1.email)
        create_response = client.post(
            "/comment/",
            json={"content": "Original content", "blog_id": blog.id},
            headers=auth_header
        )
        comment_id = create_response.json()["id"]
        
        response = client.put(
            f"/comment/{comment_id}",
            json={"content": "Updated content"},
            headers=auth_header
        )
        assert response.status_code == 202, f"Expected 202, got {response.status_code}"
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["id"] == comment_id
        print("✅ test_update_comment_success PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_update_comment_success FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def test_delete_comment_success():
    db, user1, user2, blog = setup_test_db()
    try:
        auth_header = get_auth_header(user1.email)
        create_response = client.post(
            "/comment/",
            json={"content": "Comment to delete", "blog_id": blog.id},
            headers=auth_header
        )
        comment_id = create_response.json()["id"]
        
        response = client.delete(
            f"/comment/{comment_id}",
            headers=auth_header
        )
        assert response.status_code == 204, f"Expected 204, got {response.status_code}"
        
        get_response = client.get(
            f"/comment/{comment_id}",
            headers=auth_header
        )
        assert get_response.status_code == 404, f"Expected 404 after deletion, got {get_response.status_code}"
        print("✅ test_delete_comment_success PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_delete_comment_success FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def test_update_other_user_comment_should_fail():
    db, user1, user2, blog = setup_test_db()
    try:
        auth_header_user1 = get_auth_header(user1.email)
        auth_header_user2 = get_auth_header(user2.email)
        
        create_response = client.post(
            "/comment/",
            json={"content": "User1's comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.put(
            f"/comment/{comment_id}",
            json={"content": "User2 trying to update"},
            headers=auth_header_user2
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        assert "Not authorized" in response.json()["detail"]
        print("✅ test_update_other_user_comment_should_fail PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_update_other_user_comment_should_fail FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def test_delete_other_user_comment_should_fail():
    db, user1, user2, blog = setup_test_db()
    try:
        auth_header_user1 = get_auth_header(user1.email)
        auth_header_user2 = get_auth_header(user2.email)
        
        create_response = client.post(
            "/comment/",
            json={"content": "User1's comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.delete(
            f"/comment/{comment_id}",
            headers=auth_header_user2
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        assert "Not authorized" in response.json()["detail"]
        print("✅ test_delete_other_user_comment_should_fail PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_delete_other_user_comment_should_fail FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def test_other_user_can_view_comment():
    db, user1, user2, blog = setup_test_db()
    try:
        auth_header_user1 = get_auth_header(user1.email)
        auth_header_user2 = get_auth_header(user2.email)
        
        create_response = client.post(
            "/comment/",
            json={"content": "User1's comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        comment_id = create_response.json()["id"]
        
        response = client.get(
            f"/comment/{comment_id}",
            headers=auth_header_user2
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()["content"] == "User1's comment"
        print("✅ test_other_user_can_view_comment PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_other_user_can_view_comment FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def test_create_reply_comment():
    db, user1, user2, blog = setup_test_db()
    try:
        auth_header_user1 = get_auth_header(user1.email)
        auth_header_user2 = get_auth_header(user2.email)
        
        response1 = client.post(
            "/comment/",
            json={"content": "Parent comment", "blog_id": blog.id},
            headers=auth_header_user1
        )
        assert response1.status_code == 201
        parent_comment_id = response1.json()["id"]
        
        response2 = client.post(
            "/comment/",
            json={
                "content": "Reply comment", 
                "blog_id": blog.id, 
                "parent_id": parent_comment_id
            },
            headers=auth_header_user2
        )
        assert response2.status_code == 201
        data = response2.json()
        assert data["parent_id"] == parent_comment_id
        print("✅ test_create_reply_comment PASSED")
        return True
    except AssertionError as e:
        print(f"❌ test_create_reply_comment FAILED: {e}")
        return False
    finally:
        teardown_test_db()


def run_all_tests():
    print("\n" + "="*60)
    print("Running Comment Module Tests")
    print("="*60 + "\n")
    
    tests = [
        test_create_comment_success,
        test_create_comment_without_auth,
        test_create_comment_nonexistent_blog,
        test_create_reply_comment,
        test_get_comments_by_blog_success,
        test_get_single_comment_success,
        test_update_comment_success,
        test_delete_comment_success,
        test_update_other_user_comment_should_fail,
        test_delete_other_user_comment_should_fail,
        test_other_user_can_view_comment,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
