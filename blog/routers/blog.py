from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query
from .. import schemas, database, models, oauth2
from sqlalchemy.orm import Session
from ..repository import blog

router = APIRouter(
    prefix="/blog",
    tags=['Blogs']
)

get_db = database.get_db


@router.get('/', response_model=dict)
def all(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(10, ge=1, le=100, description="每页数量"),
    tag_id: Optional[int] = Query(None, description="按标签ID筛选"),
    tag_slug: Optional[str] = Query(None, description="按标签slug筛选"),
    tag_name: Optional[str] = Query(None, description="按标签名称筛选"),
    sort_by: str = Query('created_at', description="排序字段: created_at, updated_at, title"),
    order: str = Query('desc', description="排序方式: asc, desc"),
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return blog.get_all(db, page, per_page, tag_id, tag_slug, tag_name, sort_by, order)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowBlog)
def create(
    request: schemas.BlogCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return blog.create(request, db, current_user.email)


@router.delete('/{id}', status_code=status.HTTP_200_OK)
def destroy(
    id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return blog.destroy(id, db, current_user.email)


@router.put('/{id}', status_code=status.HTTP_202_ACCEPTED, response_model=schemas.ShowBlog)
def update(
    id: int,
    request: schemas.BlogUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return blog.update(id, request, db, current_user.email)


@router.get('/{id}', status_code=200, response_model=schemas.ShowBlog)
def show(
    id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return blog.show(id, db)


@router.post('/{blog_id}/tags', response_model=schemas.ShowBlog)
def add_tags(
    blog_id: int,
    tag_names: List[str],
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return blog.add_tags_to_blog(blog_id, tag_names, db, current_user.email)


@router.delete('/{blog_id}/tags', response_model=schemas.ShowBlog)
def remove_tags(
    blog_id: int,
    tag_ids: List[int],
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return blog.remove_tags_from_blog(blog_id, tag_ids, db, current_user.email)