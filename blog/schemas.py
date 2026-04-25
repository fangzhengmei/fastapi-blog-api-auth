from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="标签名称")
    description: Optional[str] = Field(None, max_length=200, description="标签描述")


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)


class Tag(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TagWithBlogs(Tag):
    blogs: List['ShowBlog'] = []


class BlogBase(BaseModel):
    title: str
    body: str


class BlogCreate(BlogBase):
    tags: Optional[List[str]] = Field(None, description="标签名称列表")
    tag_ids: Optional[List[int]] = Field(None, description="标签ID列表")


class BlogUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = Field(None, description="标签名称列表（会替换现有标签）")
    tag_ids: Optional[List[int]] = Field(None, description="标签ID列表（会替换现有标签）")


class Blog(BlogBase):
    class Config:
        from_attributes = True


class User(BaseModel):
    name: str
    email: str
    password: str


class ShowUser(BaseModel):
    id: int
    name: str
    email: str
    blogs: List['ShowBlog'] = []

    class Config:
        from_attributes = True


class ShowBlog(BaseModel):
    id: int
    title: str
    body: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator: ShowUser
    tags: List[Tag] = []

    class Config:
        from_attributes = True


class BlogList(BaseModel):
    id: int
    title: str
    body: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator: ShowUser
    tags: List[Tag] = []

    class Config:
        from_attributes = True


class Login(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    per_page: int
    total_pages: int


class TagBlogsResponse(BaseModel):
    tag: Tag
    blogs: List[ShowBlog]
    total: int


TagWithBlogs.model_rebuild()
ShowUser.model_rebuild()