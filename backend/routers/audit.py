from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from database import get_db
from models import AuditLog, Account, PropertyValueAuditLog, MortgagePartAuditLog
from schemas import AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_log(
    account_id: Optional[int] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if account_id is not None:
        query = (
            db.query(AuditLog)
            .options(joinedload(AuditLog.account))
            .filter(AuditLog.account_id == account_id)
            .order_by(desc(AuditLog.recorded_at))
        )
        logs = query.offset(offset).limit(limit).all()
        return [
            AuditLogResponse(
                id=log.id,
                account_id=log.account_id,
                account_name=log.account.name if log.account else f"Account #{log.account_id}",
                previous_value=log.previous_value,
                new_value=log.new_value,
                change_amount=log.change_amount,
                change_percent=log.change_percent,
                note=log.note,
                recorded_at=log.recorded_at,
            )
            for log in logs
        ]

    # Fetch all logs from all three tables
    acc_logs = db.query(AuditLog).options(joinedload(AuditLog.account)).all()
    prop_logs = db.query(PropertyValueAuditLog).options(joinedload(PropertyValueAuditLog.property)).all()
    part_logs = db.query(MortgagePartAuditLog).options(joinedload(MortgagePartAuditLog.part)).all()

    merged_logs = []

    # 1. Account Logs
    for l in acc_logs:
        merged_logs.append({
            "id": l.id,
            "account_id": l.account_id,
            "account_name": l.account.name if l.account else f"Account #{l.account_id}",
            "previous_value": l.previous_value,
            "new_value": l.new_value,
            "change_amount": l.change_amount,
            "change_percent": l.change_percent,
            "note": l.note,
            "recorded_at": l.recorded_at,
        })

    # 2. Property Value Logs
    for l in prop_logs:
        merged_logs.append({
            "id": l.id,
            "account_id": None,
            "account_name": f"🏠 [Property] {l.property.name if l.property else 'Property'}",
            "previous_value": l.previous_value,
            "new_value": l.new_value,
            "change_amount": l.change_amount,
            "change_percent": (l.change_amount / l.previous_value * 100) if l.previous_value != 0 else None,
            "note": l.note,
            "recorded_at": l.recorded_at,
        })

    # 3. Mortgage Part Logs
    for l in part_logs:
        prop_name = l.part.property.name if (l.part and l.part.property) else 'Property'
        part_name = l.part.name if l.part else 'Part'
        merged_logs.append({
            "id": l.id,
            "account_id": None,
            "account_name": f"📉 [Mortgage] {prop_name} - {part_name}",
            "previous_value": l.previous_value,
            "new_value": l.new_value,
            "change_amount": l.change_amount,
            "change_percent": (l.change_amount / l.previous_value * 100) if l.previous_value != 0 else None,
            "note": l.note,
            "recorded_at": l.recorded_at,
        })

    # Sort all chronologically descending
    merged_logs.sort(key=lambda x: x["recorded_at"], reverse=True)

    # Slice for pagination
    sliced_logs = merged_logs[offset : offset + limit]

    return [
        AuditLogResponse(
            id=log["id"],
            account_id=log["account_id"],
            account_name=log["account_name"],
            previous_value=log["previous_value"],
            new_value=log["new_value"],
            change_amount=log["change_amount"],
            change_percent=log["change_percent"],
            note=log["note"],
            recorded_at=log["recorded_at"],
        )
        for log in sliced_logs
    ]


@router.get("/{account_id}/history", response_model=List[AuditLogResponse])
def get_account_history(
    account_id: int,
    db: Session = Depends(get_db),
):
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
            account_name=log.account.name if log.account else f"Account #{log.account_id}",
            previous_value=log.previous_value,
            new_value=log.new_value,
            change_amount=log.change_amount,
            change_percent=log.change_percent,
            note=log.note,
            recorded_at=log.recorded_at,
        )
        for log in logs
    ]
