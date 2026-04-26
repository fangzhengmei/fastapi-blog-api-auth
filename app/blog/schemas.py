from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class BlogStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ModerationDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class BlogBase(BaseModel):
    title: str
    body: str


class Blog(BlogBase):
    class Config():
        from_attributes = True


class User(BaseModel):
    name: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole

    class Config():
        from_attributes = True


class ShowUser(BaseModel):
    name: str
    email: str
    blogs: List[Blog] = []

    class Config():
        from_attributes = True


class ShowBlog(BaseModel):
    id: int
    title: str
    body: str
    status: BlogStatus
    created_at: datetime
    creator: UserResponse

    class Config():
        from_attributes = True


class BlogDetail(ShowBlog):
    updated_at: datetime


class ModerationLogResponse(BaseModel):
    id: int
    blog_id: int
    moderator_id: int
    moderator_name: Optional[str]
    decision: ModerationDecision
    comment: Optional[str]
    created_at: datetime

    class Config():
        from_attributes = True


class ModerationRequest(BaseModel):
    decision: ModerationDecision
    comment: Optional[str] = None


class Login(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
