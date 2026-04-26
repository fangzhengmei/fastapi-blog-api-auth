from sqlalchemy.orm import Session
from sqlalchemy import func
from blog import models, schemas
from fastapi import HTTPException, status
from blog.hashing import Hash


def create(request: schemas.User, db: Session):
    new_user = models.User(
        name=request.name, email=request.email, password=Hash.bcrypt(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def show(id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with the id {id} is not available")
    
    followers_count = db.query(func.count(models.Follow.id)).filter(
        models.Follow.followed_id == id
    ).scalar()
    
    following_count = db.query(func.count(models.Follow.id)).filter(
        models.Follow.follower_id == id
    ).scalar()
    
    return schemas.UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        followers_count=followers_count or 0,
        following_count=following_count or 0,
        blogs=user.blogs
    )
