from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from database import get_db
from models import AuditLog, Account
from schemas import AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_log(
    account_id: Optional[int] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.account))
        .order_by(desc(AuditLog.recorded_at))
    )
    if account_id:
        query = query.filter(AuditLog.account_id == account_id)

    logs = query.offset(offset).limit(limit).all()

    return [
        AuditLogResponse(
            id=log.id,
            account_id=log.account_id,
            account_name=log.account.name if log.account else None,
            previous_value=log.previous_value,
            new_value=log.new_value,
            change_amount=log.change_amount,
            change_percent=log.change_percent,
            note=log.note,
            recorded_at=log.recorded_at,
        )
        for log in logs
    ]


@router.get("/{account_id}/history", response_model=List[AuditLogResponse])
def get_account_history(
    account_id: int,
    db: Session = Depends(get_db),
):
    """Returns the full chronological history for a specific account (oldest first, for charts)."""
    logs = (
        db.query(AuditLog)
        .options(joinedload(AuditLog.account))
        .filter(AuditLog.account_id == account_id)
        .order_by(AuditLog.recorded_at)
        .all()
    )
    return [
        AuditLogResponse(
            id=log.id,
            account_id=log.account_id,
            account_name=log.account.name if log.account else None,
            previous_value=log.previous_value,
            new_value=log.new_value,
            change_amount=log.change_amount,
            change_percent=log.change_percent,
            note=log.note,
            recorded_at=log.recorded_at,
        )
        for log in logs
    ]
