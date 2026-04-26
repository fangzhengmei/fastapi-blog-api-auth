
from sqlalchemy.orm import Session
from blog import models, schemas
from fastapi import HTTPException, status
from typing import List


def follow_user(follower_id: int, followed_id: int, db: Session):
    if follower_id == followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself"
        )
    
    user_to_follow = db.query(models.User).filter(models.User.id == followed_id).first()
    if not user_to_follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {followed_id} not found"
        )
    
    existing_follow = db.query(models.Follow).filter(
        models.Follow.follower_id == follower_id,
        models.Follow.followed_id == followed_id
    ).first()
    
    if existing_follow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already following this user"
        )
    
    new_follow = models.Follow(
        follower_id=follower_id,
        followed_id=followed_id
    )
    db.add(new_follow)
    db.commit()
    db.refresh(new_follow)
    
    return schemas.FollowResponse(
        message=f"Successfully followed user {user_to_follow.name}",
        is_following=True
    )


def unfollow_user(follower_id: int, followed_id: int, db: Session):
    if follower_id == followed_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot unfollow yourself"
        )
    
    user_to_unfollow = db.query(models.User).filter(models.User.id == followed_id).first()
    if not user_to_unfollow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {followed_id} not found"
        )
    
    existing_follow = db.query(models.Follow).filter(
        models.Follow.follower_id == follower_id,
        models.Follow.followed_id == followed_id
    ).first()
    
    if not existing_follow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not following this user"
        )
    
    db.delete(existing_follow)
    db.commit()
    
    return schemas.FollowResponse(
        message=f"Successfully unfollowed user {user_to_unfollow.name}",
        is_following=False
    )


def get_followers(user_id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    followers = db.query(models.User).join(
        models.Follow, models.Follow.follower_id == models.User.id
    ).filter(
        models.Follow.followed_id == user_id
    ).all()
    
    follower_summaries = [
        schemas.UserSummary(id=f.id, name=f.name, email=f.email)
        for f in followers
    ]
    
    return schemas.FollowersResponse(
        user=schemas.UserSummary(id=user.id, name=user.name, email=user.email),
        count=len(follower_summaries),
        followers=follower_summaries
    )


def get_following(user_id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    following = db.query(models.User).join(
        models.Follow, models.Follow.followed_id == models.User.id
    ).filter(
        models.Follow.follower_id == user_id
    ).all()
    
    following_summaries = [
        schemas.UserSummary(id=f.id, name=f.name, email=f.email)
        for f in following
    ]
    
    return schemas.FollowingResponse(
        user=schemas.UserSummary(id=user.id, name=user.name, email=user.email),
        count=len(following_summaries),
        following=following_summaries
    )


def is_following(follower_id: int, followed_id: int, db: Session) -> bool:
    follow = db.query(models.Follow).filter(
        models.Follow.follower_id == follower_id,
        models.Follow.followed_id == followed_id
    ).first()
    return follow is not None


def get_following_blogs(user_id: int, db: Session, skip: int = 0, limit: int = 10):
    following_ids = db.query(models.Follow.followed_id).filter(
        models.Follow.follower_id == user_id
    ).all()
    
    following_ids = [f_id for (f_id,) in following_ids]
    
    if not following_ids:
        return []
    
    blogs = db.query(models.Blog).filter(
        models.Blog.user_id.in_(following_ids)
    ).order_by(
        models.Blog.id.desc()
    ).offset(skip).limit(limit).all()
    
    return blogs