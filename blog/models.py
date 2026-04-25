from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime
from .database import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Blog(Base):
    __tablename__ = 'blogs'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    body = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


blog_tag = Table(
    'blog_tag',
    Base.metadata,
    Column('blog_id', Integer, ForeignKey('blogs.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


Tag.blogs = relationship('Blog', secondary=blog_tag, back_populates='tags')
Blog.tags = relationship('Tag', secondary=blog_tag, back_populates='blogs')
Blog.creator = relationship("User", back_populates="blogs")
User.blogs = relationship('Blog', back_populates="creator")
