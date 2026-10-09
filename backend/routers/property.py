from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from timeutil import utcnow
from services.money import round_money, money_delta
from models import Property, MortgagePart, PropertyValueAuditLog, MortgagePartAuditLog
from schemas import (
    PropertyCreate, PropertyUpdate, PropertyValueUpdate, PropertyResponse,
    PropertyValueAuditLogResponse, MortgagePartCreate, MortgagePartUpdate,
    MortgagePartBalanceUpdate, MortgagePartResponse, MortgagePartAuditLogResponse
)

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("", response_model=List[PropertyResponse])
def list_properties(is_active: bool = True, db: Session = Depends(get_db)):
    properties = (
        db.query(Property)
        .filter(Property.is_active == is_active)
        .order_by(Property.name)
        .all()
    )
    return [PropertyResponse.from_orm_property(p) for p in properties]


@router.post("", response_model=PropertyResponse, status_code=201)
def create_property(payload: PropertyCreate, db: Session = Depends(get_db)):
    p = Property(
        name=payload.name,
        property_address=payload.property_address,
        original_price=payload.original_price,
        property_value=round_money(payload.property_value),
        ownership_percent=payload.ownership_percent,
        notes=payload.notes,
        purchase_date=payload.purchase_date,
    )
    db.add(p)
    db.flush()

    # Initial audit log for property value
    db.add(PropertyValueAuditLog(
        property_id=p.id,
        previous_value=0.0,
        new_value=round_money(payload.property_value),
        change_amount=round_money(payload.property_value),
        note="Initial property value",
        recorded_at=utcnow()
    ))
    db.commit()
    db.refresh(p)
    return PropertyResponse.from_orm_property(p)


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(property_id: int, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    return PropertyResponse.from_orm_property(p)


@router.put("/{property_id}", response_model=PropertyResponse)
def update_property_metadata(
    property_id: int,
    payload: PropertyUpdate,
    db: Session = Depends(get_db)
):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is None and field in ("name", "is_active", "ownership_percent"):
            continue  # NOT NULL columns
        setattr(p, field, value)
    p.updated_at = utcnow()
    db.commit()
    db.refresh(p)
    return PropertyResponse.from_orm_property(p)


@router.patch("/{property_id}/value", response_model=PropertyValueAuditLogResponse)
def update_property_value(
    property_id: int,
    payload: PropertyValueUpdate,
    db: Session = Depends(get_db)
):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    if not p.is_active:
        raise HTTPException(status_code=409, detail="Property is deleted")

    previous = p.property_value
    new_value = round_money(payload.new_value)
    change, _ = money_delta(previous, new_value)
    
    log = PropertyValueAuditLog(
        property_id=p.id,
        previous_value=previous,
        new_value=new_value,
        change_amount=change,
        note=payload.note,
        recorded_at=utcnow()
    )
    db.add(log)
    
    p.property_value = new_value
    p.updated_at = utcnow()
    
    db.commit()
    db.refresh(log)
    
    return PropertyValueAuditLogResponse(
        id=log.id,
        property_id=log.property_id,
        property_name=p.name,
        previous_value=log.previous_value,
        new_value=log.new_value,
        change_amount=log.change_amount,
        note=log.note,
        recorded_at=log.recorded_at
    )


@router.delete("/{property_id}", status_code=204)
def delete_property(property_id: int, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    p.is_active = False
    p.updated_at = utcnow()
    # Also mark all its mortgage parts as inactive
    for part in p.mortgage_parts:
        part.is_active = False
        part.updated_at = utcnow()
    db.commit()


@router.get("/{property_id}/history", response_model=List[PropertyValueAuditLogResponse])
def get_property_value_history(property_id: int, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    
    logs = (
        db.query(PropertyValueAuditLog)
        .filter(PropertyValueAuditLog.property_id == property_id)
        .order_by(PropertyValueAuditLog.recorded_at)
        .all()
    )
    return [
        PropertyValueAuditLogResponse(
            id=l.id,
            property_id=l.property_id,
            property_name=p.name,
            previous_value=l.previous_value,
            new_value=l.new_value,
            change_amount=l.change_amount,
            note=l.note,
            recorded_at=l.recorded_at
        )
        for l in logs
    ]


# ── Mortgage Part Endpoints ──────────────────────────────────────────────────

@router.post("/{property_id}/parts", response_model=MortgagePartResponse, status_code=201)
def create_mortgage_part(
    property_id: int,
    payload: MortgagePartCreate,
    db: Session = Depends(get_db)
):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    if not p.is_active:
        raise HTTPException(status_code=409, detail="Property is deleted")

    part = MortgagePart(
        property_id=property_id,
        name=payload.name,
        lender=payload.lender,
        outstanding_balance=round_money(payload.outstanding_balance),
        interest_rate=payload.interest_rate,
        mortgage_type=payload.mortgage_type,
        term_years=payload.term_years,
        term_months=payload.term_months,
        monthly_payment=payload.monthly_payment,
        notes=payload.notes,
    )
    db.add(part)
    db.flush()
    
    # Initial audit log for mortgage balance
    db.add(MortgagePartAuditLog(
        part_id=part.id,
        previous_value=0.0,
        new_value=round_money(payload.outstanding_balance),
        change_amount=round_money(payload.outstanding_balance),
        note="Initial mortgage balance",
        recorded_at=utcnow()
    ))
    db.commit()
    db.refresh(part)
    return MortgagePartResponse.from_orm_part(part)


@router.put("/parts/{part_id}", response_model=MortgagePartResponse)
def update_mortgage_part_metadata(
    part_id: int,
    payload: MortgagePartUpdate,
    db: Session = Depends(get_db)
):
    part = db.query(MortgagePart).filter(MortgagePart.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Mortgage part not found")
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is None and field in ("name", "is_active", "mortgage_type"):
            continue  # NOT NULL columns
        setattr(part, field, value)
    part.updated_at = utcnow()
    db.commit()
    db.refresh(part)
    return MortgagePartResponse.from_orm_part(part)


@router.patch("/parts/{part_id}/balance", response_model=MortgagePartAuditLogResponse)
def update_mortgage_part_balance(
    part_id: int,
    payload: MortgagePartBalanceUpdate,
    db: Session = Depends(get_db)
):
    part = db.query(MortgagePart).filter(MortgagePart.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Mortgage part not found")
    if not part.is_active:
        raise HTTPException(status_code=409, detail="Mortgage part is deleted")

    previous = part.outstanding_balance
    new_balance = round_money(payload.new_balance)
    change, _ = money_delta(previous, new_balance)
    
    log = MortgagePartAuditLog(
        part_id=part.id,
        previous_value=previous,
        new_value=new_balance,
        change_amount=change,
        note=payload.note,
        recorded_at=utcnow()
    )
    db.add(log)
    
    part.outstanding_balance = new_balance
    part.updated_at = utcnow()
    
    db.commit()
    db.refresh(log)
    
    return MortgagePartAuditLogResponse(
        id=log.id,
        part_id=log.part_id,
        part_name=part.name,
        property_name=part.property.name,
        previous_value=log.previous_value,
        new_value=log.new_value,
        change_amount=log.change_amount,
        note=log.note,
        recorded_at=log.recorded_at
    )


@router.delete("/parts/{part_id}", status_code=204)
def delete_mortgage_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(MortgagePart).filter(MortgagePart.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Mortgage part not found")
    part.is_active = False
    part.updated_at = utcnow()
    db.commit()


@router.get("/parts/{part_id}/history", response_model=List[MortgagePartAuditLogResponse])
def get_mortgage_part_history(part_id: int, db: Session = Depends(get_db)):
    part = db.query(MortgagePart).filter(MortgagePart.id == part_id).first()
    if not part:
        raise HTTPException(status_code=404, detail="Mortgage part not found")
    
    logs = (
        db.query(MortgagePartAuditLog)
        .filter(MortgagePartAuditLog.part_id == part_id)
        .order_by(MortgagePartAuditLog.recorded_at)
        .all()
    )
    return [
        MortgagePartAuditLogResponse(
            id=l.id,
            part_id=l.part_id,
            part_name=part.name,
            property_name=part.property.name,
            previous_value=l.previous_value,
            new_value=l.new_value,
            change_amount=l.change_amount,
            note=l.note,
            recorded_at=l.recorded_at
        )
        for l in logs
    ]
