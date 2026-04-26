from fastapi import APIRouter, Depends, status
from blog import schemas, database, models, oauth2
from sqlalchemy.orm import Session
from blog.repository import like

router = APIRouter(
    prefix="/like",
    tags=['Likes']
)

get_db = database.get_db


@router.post('/{blog_id}', status_code=status.HTTP_201_CREATED, response_model=schemas.LikeResponse)
def like_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return like.like_blog(blog_id, current_user.id, db)


@router.delete('/{blog_id}', status_code=status.HTTP_204_NO_CONTENT)
def unlike_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return like.unlike_blog(blog_id, current_user.id, db)


@router.get('/count/{blog_id}', status_code=status.HTTP_200_OK)
def get_like_count(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    count = like.get_like_count(blog_id, db)
    return {"blog_id": blog_id, "likes_count": count}


@router.get('/status/{blog_id}', status_code=status.HTTP_200_OK)
def get_like_status(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_liked = like.has_user_liked(blog_id, current_user.id, db)
    return {"blog_id": blog_id, "is_liked": is_liked}
