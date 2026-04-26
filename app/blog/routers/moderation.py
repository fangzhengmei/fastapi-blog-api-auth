from typing import List
from fastapi import APIRouter, Depends, status
from blog import schemas, database, models, oauth2
from sqlalchemy.orm import Session
from blog.repository import moderation, blog

router = APIRouter(
    prefix="/moderation",
    tags=['Moderation']
)

get_db = database.get_db


@router.get('/pending', response_model=List[schemas.ShowBlog])
def get_pending_blogs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.require_role(
        [models.UserRole.MODERATOR, models.UserRole.ADMIN]
    ))
):
    return blog.get_pending(db)


@router.post('/blog/{blog_id}', status_code=status.HTTP_200_OK, response_model=schemas.ModerationLogResponse)
def moderate_blog(
    blog_id: int,
    request: schemas.ModerationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.require_role(
        [models.UserRole.MODERATOR, models.UserRole.ADMIN]
    ))
):
    return moderation.moderate_blog(blog_id, request, db, current_user)


@router.get('/blog/{blog_id}/logs', response_model=List[schemas.ModerationLogResponse])
def get_blog_moderation_logs(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    blog_post = blog.show(blog_id, db, current_user)
    return moderation.get_moderation_logs(blog_id, db)


@router.get('/logs', response_model=List[schemas.ModerationLogResponse])
def get_all_moderation_logs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.require_role(
        [models.UserRole.MODERATOR, models.UserRole.ADMIN]
    ))
):
    return moderation.get_all_moderation_logs(db)