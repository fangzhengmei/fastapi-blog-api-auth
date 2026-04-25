from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from .. import schemas, database, models, oauth2
from sqlalchemy.orm import Session
from ..repository import tag as tag_repository

router = APIRouter(
    prefix="/tags",
    tags=['Tags']
)

get_db = database.get_db


@router.get('/', response_model=dict)
def get_all_tags(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(10, ge=1, le=100, description="每页数量"),
    sort_by: str = Query('name', description="排序字段: name, created_at, updated_at"),
    order: str = Query('asc', description="排序方式: asc, desc"),
    db: Session = Depends(get_db)
):
    return tag_repository.get_all(db, page, per_page, sort_by, order)


@router.get('/popular', response_model=List[dict])
def get_popular_tags(
    limit: int = Query(10, ge=1, le=50, description="返回热门标签数量"),
    db: Session = Depends(get_db)
):
    return tag_repository.get_popular(db, limit)


@router.get('/search', response_model=List[schemas.Tag])
def search_tags(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    return tag_repository.search_tags(keyword, db, limit)


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.Tag)
def create_tag(
    request: schemas.TagCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return tag_repository.create(request, db)


@router.get('/{tag_id}', response_model=schemas.Tag)
def get_tag_by_id(
    tag_id: int,
    db: Session = Depends(get_db)
):
    return tag_repository.get_by_id(tag_id, db)


@router.get('/slug/{slug}', response_model=schemas.Tag)
def get_tag_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    return tag_repository.get_by_slug(slug, db)


@router.put('/{tag_id}', response_model=schemas.Tag)
def update_tag(
    tag_id: int,
    request: schemas.TagUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return tag_repository.update(tag_id, request, db)


@router.delete('/{tag_id}', status_code=status.HTTP_200_OK)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return tag_repository.destroy(tag_id, db)


@router.get('/{tag_id}/blogs', response_model=dict)
def get_blogs_by_tag_id(
    tag_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return tag_repository.get_blogs_by_tag(
        tag_id=tag_id,
        db=db,
        page=page,
        per_page=per_page
    )


@router.get('/slug/{slug}/blogs', response_model=dict)
def get_blogs_by_tag_slug(
    slug: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return tag_repository.get_blogs_by_tag(
        tag_slug=slug,
        db=db,
        page=page,
        per_page=per_page
    )