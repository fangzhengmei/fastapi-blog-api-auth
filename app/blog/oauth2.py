from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from blog import token, models, database
from sqlalchemy.orm import Session
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
http_bearer = HTTPBearer(auto_error=False)

get_db = database.get_db


def get_current_user(data: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = token.verify_token(data, credentials_exception)
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise credentials_exception
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    if not credentials:
        return None
    
    email = token.verify_token(credentials.credentials, None)
    if not email:
        return None
    user = db.query(models.User).filter(models.User.email == email).first()
    return user
