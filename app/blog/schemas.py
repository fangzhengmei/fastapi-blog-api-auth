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


class UserProfile(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    blogs: List[Blog] = []
    
    class Config():
        orm_mode = True

class ShowBlog(BaseModel):
    title: str
    body:str
    creator: ShowUser

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


class UserSummary(BaseModel):
    id: int
    name: str
    
    class Config():
        orm_mode = True


class FollowResponse(BaseModel):
    message: str
    is_following: bool


class FollowersResponse(BaseModel):
    user: UserSummary
    count: int
    followers: List[UserSummary]


class FollowingResponse(BaseModel):
    user: UserSummary
    count: int
    following: List[UserSummary]
