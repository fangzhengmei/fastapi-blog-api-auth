from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from blog.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class Blog(Base):
    __tablename__ = 'blogs'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    body = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User", back_populates="blogs")
    comments = relationship("Comment", back_populates="blog")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    blogs = relationship('Blog', back_populates="creator")
    comments = relationship("Comment", back_populates="commenter")


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    blog_id = Column(Integer, ForeignKey('blogs.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('comments.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blog = relationship("Blog", back_populates="comments")
    commenter = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")
