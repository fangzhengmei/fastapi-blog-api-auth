from sqlalchemy.orm import Session
from blog import models
from fastapi import HTTPException, status


def like_blog(blog_id: int, user_id: int, db: Session):
    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {blog_id} not found")
    
    existing_like = db.query(models.Like).filter(
        models.Like.user_id == user_id,
        models.Like.blog_id == blog_id
    ).first()
    
    if existing_like:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You have already liked this blog")
    
    new_like = models.Like(user_id=user_id, blog_id=blog_id)
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    return new_like


def unlike_blog(blog_id: int, user_id: int, db: Session):
    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {blog_id} not found")
    
    existing_like = db.query(models.Like).filter(
        models.Like.user_id == user_id,
        models.Like.blog_id == blog_id
    ).first()
    
    if not existing_like:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You have not liked this blog")
    
    db.delete(existing_like)
    db.commit()


def get_like_count(blog_id: int, db: Session):
    count = db.query(models.Like).filter(models.Like.blog_id == blog_id).count()
    return count


def has_user_liked(blog_id: int, user_id: int, db: Session):
    like = db.query(models.Like).filter(
        models.Like.user_id == user_id,
        models.Like.blog_id == blog_id
    ).first()
    return like is not None
