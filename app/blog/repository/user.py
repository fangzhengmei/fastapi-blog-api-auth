from sqlalchemy.orm import Session
from blog import models, schemas
from fastapi import HTTPException, status
from blog.hashing import Hash


def create(request: schemas.User, db: Session, role: models.UserRole = models.UserRole.USER):
    new_user = models.User(
        name=request.name,
        email=request.email,
        password=Hash.bcrypt(request.password),
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def create_with_role(request: schemas.User, db: Session, role: str = "user"):
    role_enum = models.UserRole(role)
    return create(request, db, role_enum)


def show(id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with the id {id} is not available")
    return user


def get_by_email(email: str, db: Session):
    return db.query(models.User).filter(models.User.email == email).first()
