from sqlalchemy.orm import Session
from blog import models, schemas
from fastapi import HTTPException, status
from datetime import datetime


def get_all(db: Session, current_user: models.User):
    if current_user.role in [models.UserRole.MODERATOR, models.UserRole.ADMIN]:
        blogs = db.query(models.Blog).all()
    else:
        blogs = db.query(models.Blog).filter(
            models.Blog.status == models.BlogStatus.APPROVED
        ).all()
    return blogs


def get_pending(db: Session):
    blogs = db.query(models.Blog).filter(
        models.Blog.status == models.BlogStatus.PENDING
    ).all()
    return blogs


def create(request: schemas.Blog, db: Session, current_user: models.User):
    new_blog = models.Blog(
        title=request.title,
        body=request.body,
        user_id=current_user.id,
        status=models.BlogStatus.PENDING
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog


def destroy(id: int, db: Session, current_user: models.User):
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    blog_instance = blog.first()

    if not blog_instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {id} not found")

    if current_user.role not in [models.UserRole.MODERATOR, models.UserRole.ADMIN]:
        if blog_instance.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Not authorized to delete this blog")

    blog.delete(synchronize_session=False)
    db.commit()
    return 'done'


def update(id: int, request: schemas.Blog, db: Session, current_user: models.User):
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    blog_instance = blog.first()

    if not blog_instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {id} not found")

    if current_user.role not in [models.UserRole.MODERATOR, models.UserRole.ADMIN]:
        if blog_instance.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Not authorized to update this blog")

    update_data = {
        "title": request.title,
        "body": request.body,
        "updated_at": datetime.utcnow()
    }

    if blog_instance.status == models.BlogStatus.REJECTED:
        update_data["status"] = models.BlogStatus.PENDING

    blog.update(update_data)
    db.commit()
    return 'updated'


def show(id: int, db: Session, current_user: models.User):
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with the id {id} is not available")

    if current_user.role not in [models.UserRole.MODERATOR, models.UserRole.ADMIN]:
        if blog.status != models.BlogStatus.APPROVED and blog.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Not authorized to view this blog")

    return blog
