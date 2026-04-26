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

    creator = relationship("User", back_populates="blogs")
    likes = relationship("Like", back_populates="blog")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)

    blogs = relationship('Blog', back_populates="creator")
    likes = relationship("Like", back_populates="user")


class Like(Base):
    __tablename__ = 'likes'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    blog_id = Column(Integer, ForeignKey('blogs.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="likes")
    blog = relationship("Blog", back_populates="likes")
