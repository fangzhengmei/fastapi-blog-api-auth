import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="function")
def test_db():
    from blog import models
    from blog.database import Base
    from blog.hashing import Hash
    
    db_file = tempfile.mktemp(suffix='.db')
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    
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
    session.add(user1)
    session.add(user2)
    session.commit()
    session.refresh(user1)
    session.refresh(user2)
    
    blog = models.Blog(
        title="Test Blog",
        body="This is a test blog post",
        user_id=user1.id
    )
    session.add(blog)
    session.commit()
    session.refresh(blog)
    
    session._test_engine = engine
    session._db_file = db_file
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
    try:
        os.remove(db_file)
    except:
        pass


@pytest.fixture(scope="function")
def app(test_db):
    from blog.database import get_db
    from main import app as fastapi_app
    from blog.database import Base
    
    engine = test_db._test_engine
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    yield fastapi_app
    
    fastapi_app.dependency_overrides.clear()


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
