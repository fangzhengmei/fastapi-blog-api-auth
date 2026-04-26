from sqlalchemy.orm import Session
from blog import models, schemas
from fastapi import HTTPException, status
from blog.repository import like as like_repo


def get_all(db: Session, current_user: models.User = None):
    blogs = db.query(models.Blog).all()
    result = []
    for blog in blogs:
        likes_count = like_repo.get_like_count(blog.id, db)
        is_liked = like_repo.has_user_liked(blog.id, current_user.id, db) if current_user else False
        blog_data = schemas.ShowBlog(
            id=blog.id,
            title=blog.title,
            body=blog.body,
            creator=schemas.ShowUser(
                name=blog.creator.name,
                email=blog.creator.email,
                blogs=[schemas.Blog(title=b.title, body=b.body) for b in blog.creator.blogs]
            ),
            likes_count=likes_count,
            is_liked=is_liked
        )
        result.append(blog_data)
    return result


def create(request: schemas.Blog, db: Session, current_user: models.User):
    new_blog = models.Blog(title=request.title, body=request.body, user_id=current_user.id)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog


def destroy(id: int, db: Session):
    blog = db.query(models.Blog).filter(models.Blog.id == id)

    if not blog.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {id} not found")

    blog.delete(synchronize_session=False)
    db.commit()
    return 'done'


def update(id: int, request: schemas.Blog, db: Session):
    blog = db.query(models.Blog).filter(models.Blog.id == id)

    if not blog.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with id {id} not found")

    blog.update(request)
    db.commit()
    return 'updated'


def show(id: int, db: Session, current_user: models.User = None):
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Blog with the id {id} is not available")
    
    likes_count = like_repo.get_like_count(id, db)
    is_liked = like_repo.has_user_liked(id, current_user.id, db) if current_user else False
    
    return schemas.ShowBlog(
        id=blog.id,
        title=blog.title,
        body=blog.body,
        creator=schemas.ShowUser(
            name=blog.creator.name,
            email=blog.creator.email,
            blogs=[schemas.Blog(title=b.title, body=b.body) for b in blog.creator.blogs]
        ),
        likes_count=likes_count,
        is_liked=is_liked
    )
