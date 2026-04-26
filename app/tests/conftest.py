import os
import tempfile
import sys

TEST_DB_FILE = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import blog.database

from blog.database import Base, engine
from blog import models
from main import app

from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import pytest

TestingSessionLocal = blog.database.SessionLocal


@pytest.fixture(scope="function", autouse=True)
def setup_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    return TestClient(app)
