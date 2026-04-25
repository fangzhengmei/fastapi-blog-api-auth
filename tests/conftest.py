import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blog.database import Base, get_db
from blog.main import app
from blog import models, schemas, token
from blog.hashing import Hash
from blog.repository import tag as tag_repository

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


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def test_user(test_db):
    user = models.User(
        name="testuser",
        email="test@example.com",
        password=Hash.bcrypt("testpassword123")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user2(test_db):
    user = models.User(
        name="testuser2",
        email="test2@example.com",
        password=Hash.bcrypt("testpassword123")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    access_token = token.create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def auth_headers_user2(test_user2):
    access_token = token.create_access_token(data={"sub": test_user2.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def test_blog(test_db, test_user):
    blog = models.Blog(
        title="Test Blog",
        body="This is a test blog post",
        user_id=test_user.id
    )
    test_db.add(blog)
    test_db.commit()
    test_db.refresh(blog)
    return blog


@pytest.fixture(scope="function")
def test_blog2(test_db, test_user):
    blog = models.Blog(
        title="Test Blog 2",
        body="This is another test blog post",
        user_id=test_user.id
    )
    test_db.add(blog)
    test_db.commit()
    test_db.refresh(blog)
    return blog


@pytest.fixture(scope="function")
def test_tag(test_db):
    tag = models.Tag(
        name="Python",
        slug="python",
        description="Python programming language"
    )
    test_db.add(tag)
    test_db.commit()
    test_db.refresh(tag)
    return tag


@pytest.fixture(scope="function")
def test_tag2(test_db):
    tag = models.Tag(
        name="FastAPI",
        slug="fastapi",
        description="FastAPI framework"
    )
    test_db.add(tag)
    test_db.commit()
    test_db.refresh(tag)
    return tag


@pytest.fixture(scope="function")
def test_tag3(test_db):
    tag = models.Tag(
        name="JavaScript",
        slug="javascript",
        description="JavaScript programming language"
    )
    test_db.add(tag)
    test_db.commit()
    test_db.refresh(tag)
    return tag


@pytest.fixture(scope="function")
def blog_with_tags(test_db, test_user, test_tag, test_tag2):
    blog = models.Blog(
        title="Blog with tags",
        body="This blog has tags",
        user_id=test_user.id
    )
    blog.tags = [test_tag, test_tag2]
    test_db.add(blog)
    test_db.commit()
    test_db.refresh(blog)
    return blog


@pytest.fixture(scope="function")
def multiple_blogs_with_tags(test_db, test_user, test_tag, test_tag2, test_tag3):
    blogs = []
    for i in range(5):
        blog = models.Blog(
            title=f"Blog {i+1}",
            body=f"Content for blog {i+1}",
            user_id=test_user.id
        )
        if i < 3:
            blog.tags = [test_tag]
        if i >= 2:
            blog.tags.append(test_tag2)
        if i == 4:
            blog.tags.append(test_tag3)
        test_db.add(blog)
        blogs.append(blog)
    test_db.commit()
    for blog in blogs:
        test_db.refresh(blog)
    return blogs