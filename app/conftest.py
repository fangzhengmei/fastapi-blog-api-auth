import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="function")
def db_engine():
    from blog.database import Base
    
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    from blog.database import Base
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    
    db = TestingSessionLocal()
    
    from blog import models
    from blog.hashing import Hash
    
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
    
    yield db
    
    db.close()


@pytest.fixture(scope="function")
def test_db(db_session):
    yield db_session


@pytest.fixture(scope="function")
def app(db_engine):
    from blog.database import get_db
    from main import app
    from blog.database import Base
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield app
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="function")
def auth_header_user1(test_db):
    from blog import models
    from blog.token import create_access_token
    
    user = test_db.query(models.User).filter(models.User.email == "test1@example.com").first()
    access_token = create_access_token(data={"sub": user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def auth_header_user2(test_db):
    from blog import models
    from blog.token import create_access_token
    
    user = test_db.query(models.User).filter(models.User.email == "test2@example.com").first()
    access_token = create_access_token(data={"sub": user.email})
    return {"Authorization": f"Bearer {access_token}"}
