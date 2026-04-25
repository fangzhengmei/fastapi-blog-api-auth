from sqlalchemy.orm import Session
from blog import models, schemas
from fastapi import HTTPException, status
from typing import List


def create_comment(request: schemas.CommentCreate, db: Session, current_user_id: int):
    blog = db.query(models.Blog).filter(models.Blog.id == request.blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {request.blog_id} not found")
    
    if request.parent_id:
        parent_comment = db.query(models.Comment).filter(models.Comment.id == request.parent_id).first()
        if not parent_comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Parent comment with id {request.parent_id} not found")
    
    new_comment = models.Comment(
        content=request.content,
        blog_id=request.blog_id,
        user_id=current_user_id,
        parent_id=request.parent_id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


def get_comments_by_blog(blog_id: int, db: Session) -> List[models.Comment]:
    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {blog_id} not found")
    
    comments = db.query(models.Comment).filter(
        models.Comment.blog_id == blog_id,
        models.Comment.parent_id == None
    ).all()
    return comments


def get_comment_by_id(comment_id: int, db: Session) -> models.Comment:
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Comment with id {comment_id} not found")
    return comment


def update_comment(comment_id: int, request: schemas.CommentUpdate, db: Session, current_user_id: int):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Comment with id {comment_id} not found")
    
    if comment.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to update this comment")
    
    comment.content = request.content
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(comment_id: int, db: Session, current_user_id: int):
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Comment with id {comment_id} not found")
    
    if comment.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to delete this comment")
    
    db.query(models.Comment).filter(models.Comment.parent_id == comment_id).update(
        {"parent_id": None}, synchronize_session=False
    )
    
    db.delete(comment)
    db.commit()
    return 'done'
