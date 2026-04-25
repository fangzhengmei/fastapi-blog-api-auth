from typing import List, Optional
from pydantic import BaseModel, field_validator
from datetime import datetime


class BlogBase(BaseModel):
    title: str
    body: str

class Blog(BlogBase):
    model_config = {"from_attributes": True}

class User(BaseModel):
    name:str
    email:str
    password:str

class ShowUser(BaseModel):
    name:str
    email:str
    blogs : List[Blog] =[]
    model_config = {"from_attributes": True}

class Commenter(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}

class CommentBase(BaseModel):
    content: str
    parent_id: Optional[int] = None

class CommentCreate(CommentBase):
    blog_id: int

class CommentUpdate(BaseModel):
    content: str

class ShowComment(BaseModel):
    id: int
    content: str
    blog_id: int
    user_id: int
    parent_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    commenter: Commenter
    replies: List['ShowComment'] = []
    
    model_config = {"from_attributes": True}
    
    @field_validator('replies', mode='before')
    @classmethod
    def empty_replies_if_none(cls, v):
        return v if v is not None else []

ShowComment.model_rebuild()

class ShowBlog(BaseModel):
    title: str
    body:str
    creator: ShowUser
    comments: List[ShowComment] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
    
    @field_validator('comments', mode='before')
    @classmethod
    def empty_comments_if_none(cls, v):
        return v if v is not None else []


class Login(BaseModel):
    username: str
    password:str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
