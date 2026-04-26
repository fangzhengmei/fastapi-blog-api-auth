from fastapi import APIRouter, Depends, status
from blog import database, schemas, models, oauth2
from sqlalchemy.orm import Session
from blog.repository import follow as follow_repository

router = APIRouter(
    prefix="/follow",
    tags=['Follow']
)

get_db = database.get_db


@router.post('/{user_id}/follow', response_model=schemas.FollowResponse, status_code=status.HTTP_201_CREATED)
def follow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return follow_repository.follow_user(
        follower_id=current_user.id,
        followed_id=user_id,
        db=db
    )


@router.post('/{user_id}/unfollow', response_model=schemas.FollowResponse, status_code=status.HTTP_200_OK)
def unfollow_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return follow_repository.unfollow_user(
        follower_id=current_user.id,
        followed_id=user_id,
        db=db
    )


@router.get('/followers/{user_id}', response_model=schemas.FollowersResponse)
def get_followers(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return follow_repository.get_followers(user_id, db)


@router.get('/following/{user_id}', response_model=schemas.FollowingResponse)
def get_following(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return follow_repository.get_following(user_id, db)


@router.get('/is-following/{user_id}')
def check_is_following(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    is_following = follow_repository.is_following(
        follower_id=current_user.id,
        followed_id=user_id,
        db=db
    )
    return {"is_following": is_following}