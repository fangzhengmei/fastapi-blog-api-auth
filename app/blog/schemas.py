from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class BlogBase(BaseModel):
    title: str
    body: str

class Blog(BlogBase):
    class Config():
        orm_mode = True

class User(BaseModel):
    name:str
    email:str
    password:str

class ShowUser(BaseModel):
    name:str
    email:str
    blogs : List[Blog] =[]
    class Config():
        orm_mode = True

class Commenter(BaseModel):
    id: int
    name: str
    class Config():
        orm_mode = True

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
    
    class Config():
        orm_mode = True

ShowComment.model_rebuild()

class ShowBlog(BaseModel):
    title: str
    body:str
    creator: ShowUser
    comments: List[ShowComment] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config():
        orm_mode = True


class Login(BaseModel):
    username: str
    password:str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
