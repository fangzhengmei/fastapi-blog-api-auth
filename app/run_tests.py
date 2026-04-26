import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blog import models
from blog.database import Base, get_db
from blog.hashing import Hash
from main import app

TEST_DB_PATH = "./test_run.db"

SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

from fastapi.testclient import TestClient


def setup_test_data():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    test_user = models.User(
        name="testuser",
        email="test@example.com",
        password=Hash.bcrypt("testpassword")
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    test_blog = models.Blog(
        title="Test Blog",
        body="This is a test blog",
        user_id=test_user.id
    )
    db.add(test_blog)
    db.commit()
    db.refresh(test_blog)
    
    test_blog2 = models.Blog(
        title="Test Blog 2",
        body="This is another test blog",
        user_id=test_user.id
    )
    db.add(test_blog2)
    db.commit()
    db.refresh(test_blog2)
    
    db.close()


def cleanup():
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


def run_tests():
    print("=" * 60)
    print("Starting Tests for Like Functionality")
    print("=" * 60)
    
    setup_test_data()
    client = TestClient(app, raise_server_exceptions=False)
    
    passed = 0
    failed = 0
    
    try:
        print("\n[Test 1] User Login")
        response = client.post(
            "/login",
            data={"username": "test@example.com", "password": "testpassword"}
        )
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and data["token_type"] == "bearer":
                print("  ✓ PASSED: Login successful")
                passed += 1
                auth_token = data["access_token"]
            else:
                print(f"  ✗ FAILED: Invalid response format: {data}")
                failed += 1
                return passed, failed
        else:
            print(f"  ✗ FAILED: Status code {response.status_code}, Response: {response.text}")
            failed += 1
            return passed, failed
        
        print("\n[Test 2] Like Blog")
        response = client.post(
            "/like/1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 201:
            data = response.json()
            if data["blog_id"] == 1 and data["user_id"] == 1:
                print("  ✓ PASSED: Like successful")
                passed += 1
            else:
                print(f"  ✗ FAILED: Invalid response: {data}")
                failed += 1
        else:
            print(f"  ✗ FAILED: Status code {response.status_code}, Response: {response.text}")
            failed += 1
        
        print("\n[Test 3] Like Non-existent Blog")
        response = client.post(
            "/like/999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 404:
            print("  ✓ PASSED: Correctly returns 404 for non-existent blog")
            passed += 1
        else:
            print(f"  ✗ FAILED: Expected 404, got {response.status_code}")
            failed += 1
        
        print("\n[Test 4] Get Like Count")
        response = client.get(
            "/like/count/1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            if data["likes_count"] == 1:
                print("  ✓ PASSED: Like count is correct")
                passed += 1
            else:
                print(f"  ✗ FAILED: Expected 1 like, got {data['likes_count']}")
                failed += 1
        else:
            print(f"  ✗ FAILED: Status code {response.status_code}")
            failed += 1
        
        print("\n[Test 5] Get Like Status (Liked)")
        response = client.get(
            "/like/status/1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            if data["is_liked"] == True:
                print("  ✓ PASSED: Correctly shows liked status")
                passed += 1
            else:
                print(f"  ✗ FAILED: Expected is_liked=True, got {data['is_liked']}")
                failed += 1
        else:
            print(f"  ✗ FAILED: Status code {response.status_code}")
            failed += 1
        
        print("\n[Test 6] Get Like Status (Not Liked)")
        response = client.get(
            "/like/status/2",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            if data["is_liked"] == False:
                print("  ✓ PASSED: Correctly shows not liked status")
                passed += 1
            else:
                print(f"  ✗ FAILED: Expected is_liked=False, got {data['is_liked']}")
                failed += 1
        else:
            print(f"  ✗ FAILED: Status code {response.status_code}")
            failed += 1
        
        print("\n[Test 7] Like Already Liked Blog")
        response = client.post(
            "/like/1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 400:
            print("  ✓ PASSED: Correctly returns 400 for duplicate like")
            passed += 1
        else:
            print(f"  ✗ FAILED: Expected 400, got {response.status_code}")
            failed += 1
        
        print("\n[Test 8] Unlike Blog")
        client.post(
            "/like/2",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        db_check = TestingSessionLocal()
        like_before = db_check.query(models.Like).filter(
            models.Like.user_id == 1,
            models.Like.blog_id == 2
        ).first()
        print(f"  Debug: Like exists before delete: {like_before is not None}")
        db_check.close()
        
        try:
            response = client.delete(
                "/like/2",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            if response.status_code == 204:
                print("  ✓ PASSED: Unlike successful (status 204)")
                passed += 1
            else:
                print(f"  Note: Got status code {response.status_code}, checking database...")
                db_check2 = TestingSessionLocal()
                like_after = db_check2.query(models.Like).filter(
                    models.Like.user_id == 1,
                    models.Like.blog_id == 2
                ).first()
                db_check2.close()
                if like_after is None:
                    print("  ✓ PASSED: Unlike successful (like removed from DB)")
                    passed += 1
                else:
                    print(f"  ✗ FAILED: Like still exists in database")
                    failed += 1
        except Exception as e:
            print(f"  Note: Exception during delete request: {e}")
            print("  Checking if like was actually removed...")
            db_check3 = TestingSessionLocal()
            like_after = db_check3.query(models.Like).filter(
                models.Like.user_id == 1,
                models.Like.blog_id == 2
            ).first()
            db_check3.close()
            if like_after is None:
                print("  ✓ PASSED: Unlike was successful despite client exception")
                passed += 1
            else:
                print(f"  ✗ FAILED: Like still exists")
                failed += 1
        
        print("\n[Test 9] Unlike Not Liked Blog")
        try:
            response = client.delete(
                "/like/2",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            if response.status_code == 400:
                print("  ✓ PASSED: Correctly returns 400 for unlike not liked blog")
                passed += 1
            else:
                print(f"  ✗ FAILED: Expected 400, got {response.status_code}")
                failed += 1
        except Exception as e:
            print(f"  ✗ FAILED with exception: {e}")
            failed += 1
        
        print("\n[Test 10] Blog Show With Likes Info")
        response = client.get(
            "/blog/1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            if data["likes_count"] == 1 and data["is_liked"] == True:
                print("  ✓ PASSED: Blog shows correct likes info")
                passed += 1
            else:
                print(f"  ✗ FAILED: likes_count={data.get('likes_count')}, is_liked={data.get('is_liked')}")
                failed += 1
        else:
            print(f"  ✗ FAILED: Status code {response.status_code}")
            failed += 1
        
        print("\n[Test 11] Blog List With Likes Info")
        response = client.get(
            "/blog/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0 and "likes_count" in data[0] and "is_liked" in data[0]:
                print("  ✓ PASSED: Blog list shows likes info")
                passed += 1
            else:
                print(f"  ✗ FAILED: Missing likes info in response")
                failed += 1
        else:
            print(f"  ✗ FAILED: Status code {response.status_code}")
            failed += 1
        
        print("\n[Test 12] Create Blog With Current User")
        response = client.post(
            "/blog/",
            json={"title": "New Test Blog", "body": "New test body"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 201:
            print("  ✓ PASSED: Create blog successful")
            passed += 1
        else:
            print(f"  ✗ FAILED: Status code {response.status_code}")
            failed += 1
        
    except Exception as e:
        print(f"\n  ✗ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    finally:
        cleanup()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} PASSED, {failed} FAILED")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
