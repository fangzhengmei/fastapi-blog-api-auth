from fastapi import APIRouter, Query
from blog import database, schemas, models, oauth2
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status
from blog.repository import user

router = APIRouter(
    prefix="/user",
    tags=['Users']
)

get_db = database.get_db


@router.post('/', response_model=schemas.UserResponse)
def create_user(
    request: schemas.User,
    db: Session = Depends(get_db)
):
    return user.create(request, db)


@router.post('/create-with-role', response_model=schemas.UserResponse)
def create_user_with_role(
    request: schemas.User,
    role: str = Query("user", enum=["user", "moderator", "admin"]),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.require_role([models.UserRole.ADMIN]))
):
    return user.create_with_role(request, db, role)


@router.get('/{id}', response_model=schemas.UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    return user.show(id, db)
