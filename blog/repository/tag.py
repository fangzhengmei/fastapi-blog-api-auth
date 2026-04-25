from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from .. import models, schemas
from fastapi import HTTPException, status
import re
from typing import List, Optional


def slugify(name: str) -> str:
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug.strip('-')


def get_all(db: Session, page: int = 1, per_page: int = 10, sort_by: str = 'name', order: str = 'asc'):
    valid_sort_fields = ['name', 'created_at', 'updated_at']
    sort_field = sort_by if sort_by in valid_sort_fields else 'name'
    
    if sort_field == 'name':
        sort_column = models.Tag.name
    elif sort_field == 'created_at':
        sort_column = models.Tag.created_at
    else:
        sort_column = models.Tag.updated_at
    
    sort_column = sort_column.asc() if order == 'asc' else sort_column.desc()
    
    total = db.query(models.Tag).count()
    tags = db.query(models.Tag).order_by(sort_column).offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        'items': tags,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }


def get_popular(db: Session, limit: int = 10):
    from sqlalchemy.orm import aliased
    
    blog_tag_alias = aliased(models.blog_tag)
    
    popular_tags = db.query(
        models.Tag,
        func.count(blog_tag_alias.c.blog_id).label('blog_count')
    ).outerjoin(
        blog_tag_alias, models.Tag.id == blog_tag_alias.c.tag_id
    ).group_by(
        models.Tag.id
    ).order_by(
        func.count(blog_tag_alias.c.blog_id).desc(),
        models.Tag.name.asc()
    ).limit(limit).all()
    
    result = []
    for tag, count in popular_tags:
        tag_dict = {
            'id': tag.id,
            'name': tag.name,
            'slug': tag.slug,
            'description': tag.description,
            'created_at': tag.created_at,
            'updated_at': tag.updated_at,
            'blog_count': count
        }
        result.append(tag_dict)
    
    return result


def create(request: schemas.TagCreate, db: Session):
    slug = slugify(request.name)
    
    existing_tag = db.query(models.Tag).filter(
        (models.Tag.name == request.name) | (models.Tag.slug == slug)
    ).first()
    
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag '{request.name}' already exists"
        )
    
    new_tag = models.Tag(
        name=request.name,
        slug=slug,
        description=request.description
    )
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag


def get_by_id(id: int, db: Session):
    tag = db.query(models.Tag).filter(models.Tag.id == id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {id} not found"
        )
    return tag


def get_by_slug(slug: str, db: Session):
    tag = db.query(models.Tag).filter(models.Tag.slug == slug).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with slug '{slug}' not found"
        )
    return tag


def get_by_name(name: str, db: Session):
    tag = db.query(models.Tag).filter(models.Tag.name == name).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with name '{name}' not found"
        )
    return tag


def update(id: int, request: schemas.TagUpdate, db: Session):
    tag = db.query(models.Tag).filter(models.Tag.id == id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {id} not found"
        )
    
    update_data = request.model_dump(exclude_unset=True)
    
    if 'name' in update_data:
        new_slug = slugify(update_data['name'])
        
        existing_tag = db.query(models.Tag).filter(
            (models.Tag.name == update_data['name']) & (models.Tag.id != id)
        ).first()
        
        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{update_data['name']}' already exists"
            )
        
        update_data['slug'] = new_slug
    
    db.query(models.Tag).filter(models.Tag.id == id).update(update_data)
    db.commit()
    
    updated_tag = db.query(models.Tag).filter(models.Tag.id == id).first()
    return updated_tag


def destroy(id: int, db: Session):
    tag = db.query(models.Tag).filter(models.Tag.id == id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {id} not found"
        )
    
    db.delete(tag)
    db.commit()
    return {'message': 'Tag deleted successfully'}


def get_blogs_by_tag(
    tag_id: Optional[int] = None,
    tag_slug: Optional[str] = None,
    tag_name: Optional[str] = None,
    db: Session = None,
    page: int = 1,
    per_page: int = 10
):
    tag = None
    
    if tag_id:
        tag = get_by_id(tag_id, db)
    elif tag_slug:
        tag = get_by_slug(tag_slug, db)
    elif tag_name:
        tag = get_by_name(tag_name, db)
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    total_query = db.query(models.Blog).join(models.Blog.tags).filter(models.Tag.id == tag.id)
    total = total_query.count()
    
    blogs_query = db.query(models.Blog).options(
        selectinload(models.Blog.tags),
        selectinload(models.Blog.creator)
    ).join(models.Blog.tags).filter(models.Tag.id == tag.id)
    
    start = (page - 1) * per_page
    blogs = blogs_query.order_by(models.Blog.created_at.desc()).offset(start).limit(per_page).all()
    
    return {
        'tag': tag,
        'blogs': blogs,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }


def search_tags(keyword: str, db: Session, limit: int = 10):
    tags = db.query(models.Tag).filter(
        models.Tag.name.ilike(f'%{keyword}%')
    ).limit(limit).all()
    return tags


def get_or_create_tags(tag_names: List[str], db: Session) -> List[models.Tag]:
    tags = []
    for name in tag_names:
        name = name.strip()
        if not name:
            continue
            
        slug = slugify(name)
        tag = db.query(models.Tag).filter(
            (models.Tag.name == name) | (models.Tag.slug == slug)
        ).first()
        
        if not tag:
            tag = models.Tag(name=name, slug=slug)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        
        if tag not in tags:
            tags.append(tag)
    
    return tags


def get_tags_by_ids(tag_ids: List[int], db: Session) -> List[models.Tag]:
    tags = db.query(models.Tag).filter(models.Tag.id.in_(tag_ids)).all()
    
    if len(tags) != len(tag_ids):
        found_ids = {tag.id for tag in tags}
        missing_ids = [tag_id for tag_id in tag_ids if tag_id not in found_ids]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tags with ids {missing_ids} not found"
        )
    
    return tags