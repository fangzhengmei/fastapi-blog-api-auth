from typing import Optional
from sqlalchemy.orm import Session
from blog import models, schemas
from fastapi import HTTPException, status


def get_all(db: Session, current_user: Optional[models.User]):
    if current_user is None:
        blogs = db.query(models.Blog).filter(models.Blog.is_published == 1).all()
    else:
        blogs = db.query(models.Blog).filter(
            (models.Blog.is_published == 1) | (models.Blog.user_id == current_user.id)
        ).all()
    return blogs


def create(request: schemas.Blog, db: Session, current_user: models.User):
    is_published = 1 if request.is_published else 0
    new_blog = models.Blog(
        title=request.title, 
        body=request.body, 
        user_id=current_user.id,
        is_published=is_published
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog


def destroy(id: int, db: Session, current_user: models.User):
    blog = db.query(models.Blog).filter(models.Blog.id == id)

    if not blog.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {id} not found")
    
    if blog.first().user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not authorized to delete this blog")

    blog.delete(synchronize_session=False)
    db.commit()
    return 'done'


def update(id: int, request: schemas.Blog, db: Session, current_user: models.User):
    blog_query = db.query(models.Blog).filter(models.Blog.id == id)
    blog = blog_query.first()

    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {id} not found")
    
    if blog.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not authorized to update this blog")
    
    update_data = {
        "title": request.title,
        "body": request.body,
        "is_published": 1 if request.is_published else 0
    }
    blog_query.update(update_data)
    db.commit()
    return 'updated'


def show(id: int, db: Session, current_user: Optional[models.User]):
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with the id {id} is not available")
    
    if not blog.is_published:
        if current_user is None or blog.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Blog with the id {id} is not available")
    return blog


def publish(id: int, db: Session, current_user: models.User):
    blog_query = db.query(models.Blog).filter(models.Blog.id == id)
    blog = blog_query.first()

    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {id} not found")
    
    if blog.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not authorized to publish this blog")
    
    blog_query.update({"is_published": 1})
    db.commit()
    return blog_query.first()


def unpublish(id: int, db: Session, current_user: models.User):
    blog_query = db.query(models.Blog).filter(models.Blog.id == id)
    blog = blog_query.first()

    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {id} not found")
    
    if blog.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not authorized to unpublish this blog")
    
    blog_query.update({"is_published": 0})
    db.commit()
    return blog_query.first()
