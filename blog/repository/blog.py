from sqlalchemy.orm import Session
from sqlalchemy import and_
from .. import models, schemas
from ..repository import tag as tag_repository
from fastapi import HTTPException, status
from typing import Optional, List


def get_all(
    db: Session,
    page: int = 1,
    per_page: int = 10,
    tag_id: Optional[int] = None,
    tag_slug: Optional[str] = None,
    tag_name: Optional[str] = None,
    sort_by: str = 'created_at',
    order: str = 'desc'
):
    query = db.query(models.Blog)
    
    if tag_id:
        query = query.join(models.Blog.tags).filter(models.Tag.id == tag_id)
    elif tag_slug:
        query = query.join(models.Blog.tags).filter(models.Tag.slug == tag_slug)
    elif tag_name:
        query = query.join(models.Blog.tags).filter(models.Tag.name == tag_name)
    
    valid_sort_fields = ['created_at', 'updated_at', 'title']
    sort_field = sort_by if sort_by in valid_sort_fields else 'created_at'
    
    if sort_field == 'created_at':
        sort_column = models.Blog.created_at
    elif sort_field == 'updated_at':
        sort_column = models.Blog.updated_at
    else:
        sort_column = models.Blog.title
    
    sort_column = sort_column.asc() if order == 'asc' else sort_column.desc()
    
    total = query.count()
    blogs = query.order_by(sort_column).offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': blogs,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }


def _get_user_by_email(email: str, db: Session) -> models.User:
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found"
        )
    return user


def create(
    request: schemas.BlogCreate,
    db: Session,
    current_user_email: str
):
    user = _get_user_by_email(current_user_email, db)
    
    new_blog = models.Blog(
        title=request.title,
        body=request.body,
        user_id=user.id
    )
    
    tags = []
    
    if request.tag_ids:
        tags.extend(tag_repository.get_tags_by_ids(request.tag_ids, db))
    
    if request.tags:
        tags.extend(tag_repository.get_or_create_tags(request.tags, db))
    
    if tags:
        new_blog.tags = tags
    
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog


def destroy(id: int, db: Session, current_user_email: str):
    user = _get_user_by_email(current_user_email, db)
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()

    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog with id {id} not found"
        )
    
    if blog.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this blog"
        )

    db.delete(blog)
    db.commit()
    return {'message': 'Blog deleted successfully'}


def update(
    id: int,
    request: schemas.BlogUpdate,
    db: Session,
    current_user_email: str
):
    user = _get_user_by_email(current_user_email, db)
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()

    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog with id {id} not found"
        )
    
    if blog.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this blog"
        )

    update_data = request.model_dump(exclude_unset=True, exclude={'tags', 'tag_ids'})
    
    if update_data:
        db.query(models.Blog).filter(models.Blog.id == id).update(update_data)
    
    if request.tag_ids is not None or request.tags is not None:
        new_tags = []
        
        if request.tag_ids:
            new_tags.extend(tag_repository.get_tags_by_ids(request.tag_ids, db))
        
        if request.tags:
            new_tags.extend(tag_repository.get_or_create_tags(request.tags, db))
        
        blog.tags = new_tags
    
    db.commit()
    
    updated_blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    return updated_blog


def show(id: int, db: Session):
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog with the id {id} is not available"
        )
    return blog


def add_tags_to_blog(
    blog_id: int,
    tag_names: List[str],
    db: Session,
    current_user_email: str
):
    user = _get_user_by_email(current_user_email, db)
    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog with id {blog_id} not found"
        )
    
    if blog.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this blog"
        )
    
    new_tags = tag_repository.get_or_create_tags(tag_names, db)
    
    for tag in new_tags:
        if tag not in blog.tags:
            blog.tags.append(tag)
    
    db.commit()
    db.refresh(blog)
    return blog


def remove_tags_from_blog(
    blog_id: int,
    tag_ids: List[int],
    db: Session,
    current_user_email: str
):
    user = _get_user_by_email(current_user_email, db)
    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog with id {blog_id} not found"
        )
    
    if blog.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this blog"
        )
    
    tags_to_remove = db.query(models.Tag).filter(models.Tag.id.in_(tag_ids)).all()
    
    for tag in tags_to_remove:
        if tag in blog.tags:
            blog.tags.remove(tag)
    
    db.commit()
    db.refresh(blog)
    return blog