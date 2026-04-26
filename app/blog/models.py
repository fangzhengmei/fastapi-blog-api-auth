from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from blog.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

MAX_COMMENT_LENGTH = 500


class UserRole(str, enum.Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class BlogStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ModerationDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class Blog(Base):
    __tablename__ = 'blogs'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    body = Column(String)
    status = Column(Enum(BlogStatus), default=BlogStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))

    creator = relationship("User", back_populates="blogs")
    moderation_logs = relationship("ModerationLog", back_populates="blog")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.USER)
    created_at = Column(DateTime, default=datetime.utcnow)

    blogs = relationship('Blog', back_populates="creator")
    moderation_actions = relationship("ModerationLog", back_populates="moderator")


class ModerationLog(Base):
    __tablename__ = 'moderation_logs'

    id = Column(Integer, primary_key=True, index=True)
    blog_id = Column(Integer, ForeignKey('blogs.id'))
    moderator_id = Column(Integer, ForeignKey('users.id'))
    decision = Column(Enum(ModerationDecision))
    comment = Column(String(MAX_COMMENT_LENGTH), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    blog = relationship("Blog", back_populates="moderation_logs")
    moderator = relationship("User", back_populates="moderation_actions")
