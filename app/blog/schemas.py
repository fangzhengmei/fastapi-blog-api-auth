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

class ShowBlog(BaseModel):
    id: int
    title: str
    body: str
    creator: ShowUser
    likes_count: int = 0
    is_liked: bool = False

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


class LikeBase(BaseModel):
    pass


class LikeCreate(LikeBase):
    blog_id: int


class LikeResponse(BaseModel):
    id: int
    user_id: int
    blog_id: int
    created_at: datetime

    class Config():
        orm_mode = True
