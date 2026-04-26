from sqlalchemy.orm import Session
from blog import models, schemas
from fastapi import HTTPException, status
from datetime import datetime


def moderate_blog(
    blog_id: int,
    request: schemas.ModerationRequest,
    db: Session,
    current_user: models.User
):
    blog = db.query(models.Blog).filter(models.Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blog with id {blog_id} not found"
        )

    if blog.status != models.BlogStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Blog is not pending moderation. Current status: {blog.status.value}"
        )

    if request.decision == schemas.ModerationDecision.APPROVED:
        blog.status = models.BlogStatus.APPROVED
    else:
        blog.status = models.BlogStatus.REJECTED

    blog.updated_at = datetime.utcnow()

    moderation_log = models.ModerationLog(
        blog_id=blog.id,
        moderator_id=current_user.id,
        decision=models.ModerationDecision(request.decision.value),
        comment=request.comment
    )
    db.add(moderation_log)
    db.commit()
    db.refresh(moderation_log)
    db.refresh(blog)

    return moderation_log


def get_moderation_logs(
    blog_id: int,
    db: Session
):
    logs = db.query(models.ModerationLog).filter(
        models.ModerationLog.blog_id == blog_id
    ).order_by(models.ModerationLog.created_at.desc()).all()

    result = []
    for log in logs:
        moderator = db.query(models.User).filter(
            models.User.id == log.moderator_id
        ).first()
        result.append(schemas.ModerationLogResponse(
            id=log.id,
            blog_id=log.blog_id,
            moderator_id=log.moderator_id,
            moderator_name=moderator.name if moderator else None,
            decision=log.decision.value,
            comment=log.comment,
            created_at=log.created_at
        ))
    return result


def get_all_moderation_logs(db: Session):
    logs = db.query(models.ModerationLog).order_by(
        models.ModerationLog.created_at.desc()
    ).all()

    result = []
    for log in logs:
        moderator = db.query(models.User).filter(
            models.User.id == log.moderator_id
        ).first()
        result.append(schemas.ModerationLogResponse(
            id=log.id,
            blog_id=log.blog_id,
            moderator_id=log.moderator_id,
            moderator_name=moderator.name if moderator else None,
            decision=log.decision.value,
            comment=log.comment,
            created_at=log.created_at
        ))
    return result