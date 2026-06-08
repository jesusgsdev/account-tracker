from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Account, AuditLog
from schemas import (
    AccountCreate, AccountUpdate, AccountValueUpdate,
    AccountResponse, AuditLogResponse
)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=List[AccountResponse])
def list_accounts(
    category: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Account).filter(Account.is_active == is_active)
    if category:
        query = query.filter(Account.category == category.upper())
    accounts = query.order_by(Account.category, Account.name).all()
    return [AccountResponse.from_orm_account(a) for a in accounts]


@router.post("", response_model=AccountResponse, status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db)):
    # Only store initial_investment for eligible categories
    initial = None
    if payload.category in ("INVESTMENTS", "RETIREMENT"):
        initial = payload.initial_investment

    account = Account(
        name=payload.name,
        account_type=payload.account_type,
        category=payload.category,
        provider=payload.provider,
        current_value=payload.current_value,
        initial_investment=initial,
        notes=payload.notes,
    )
    db.add(account)
    db.flush()

    # Create initial audit entry if value > 0
    if payload.current_value > 0:
        log = AuditLog(
            account_id=account.id,
            previous_value=0.0,
            new_value=payload.current_value,
            change_amount=payload.current_value,
            change_percent=None,
            note="Initial value",
            recorded_at=datetime.utcnow(),
        )
        db.add(log)

    db.commit()
    db.refresh(account)
    return AccountResponse.from_orm_account(account)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse.from_orm_account(account)


@router.patch("/{account_id}/value", response_model=AuditLogResponse)
def update_account_value(
    account_id: int,
    payload: AccountValueUpdate,
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    previous = account.current_value
    new = payload.new_value
    change = new - previous
    percent = ((change / previous) * 100) if previous != 0 else None

    log = AuditLog(
        account_id=account.id,
        previous_value=previous,
        new_value=new,
        change_amount=change,
        change_percent=percent,
        note=payload.note,
        recorded_at=datetime.utcnow(),
    )
    db.add(log)

    account.current_value = new
    account.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(log)

    return AuditLogResponse(
        id=log.id,
        account_id=log.account_id,
        account_name=account.name,
        previous_value=log.previous_value,
        new_value=log.new_value,
        change_amount=log.change_amount,
        change_percent=log.change_percent,
        note=log.note,
        recorded_at=log.recorded_at,
    )


@router.put("/{account_id}", response_model=AccountResponse)
def update_account_metadata(
    account_id: int,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    data = payload.model_dump(exclude_unset=True)

    # Enforce: initial_investment only makes sense on INVESTMENTS / RETIREMENT
    new_category = data.get("category", account.category)
    if new_category not in ("INVESTMENTS", "RETIREMENT"):
        data["initial_investment"] = None

    for field, value in data.items():
        setattr(account, field, value)
    account.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(account)
    return AccountResponse.from_orm_account(account)


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account.is_active = False
    account.updated_at = datetime.utcnow()
    db.commit()
