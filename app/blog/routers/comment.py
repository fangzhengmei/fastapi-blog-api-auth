from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from blog import schemas, database, models, oauth2
from sqlalchemy.orm import Session
from blog.repository import comment

router = APIRouter(
    prefix="/comment",
    tags=['Comments']
)

get_db = database.get_db


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowComment)
def create_comment(
    request: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    user = db.query(models.User).filter(models.User.email == current_user.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return comment.create_comment(request, db, user.id)


@router.get('/blog/{blog_id}', response_model=List[schemas.ShowComment])
def get_comments_by_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return comment.get_comments_by_blog(blog_id, db)


@router.get('/{comment_id}', response_model=schemas.ShowComment)
def get_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    return comment.get_comment_by_id(comment_id, db)


@router.put('/{comment_id}', status_code=status.HTTP_202_ACCEPTED, response_model=schemas.ShowComment)
def update_comment(
    comment_id: int,
    request: schemas.CommentUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    user = db.query(models.User).filter(models.User.email == current_user.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return comment.update_comment(comment_id, request, db, user.id)


@router.delete('/{comment_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.TokenData = Depends(oauth2.get_current_user)
):
    user = db.query(models.User).filter(models.User.email == current_user.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return comment.delete_comment(comment_id, db, user.id)
