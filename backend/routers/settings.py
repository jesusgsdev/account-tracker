"""Per-app UI settings persisted in the database so they follow you across devices."""
import json
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import AppSetting
from timeutil import utcnow

router = APIRouter(prefix="/api/settings", tags=["settings"])

FORECAST_KEY = "forecast"


class ForecastSettings(BaseModel):
    end_year: int = Field(ge=2000, le=2200)
    include_other: bool
    return_rate_investments: float = Field(ge=0, le=100)
    contrib_investments: float = Field(ge=0, le=1_000_000)
    return_rate_retirement: float = Field(ge=0, le=100)
    contrib_retirement: float = Field(ge=0, le=1_000_000)
    # Added later: older saved settings without it load with the default.
    contrib_retirement_growth: float = Field(default=1.0, ge=0, le=50)
    inflation_rate: float = Field(ge=0, le=50)
    adjust_inflation: bool
    birth_year: int = Field(ge=1900, le=2100)
    withdrawal_rate: float = Field(ge=0, le=100)


@router.get("/forecast", response_model=Optional[ForecastSettings])
def get_forecast_settings(db: Session = Depends(get_db)):
    """The saved forecast settings, or null if none were ever saved."""
    row = db.get(AppSetting, FORECAST_KEY)
    if row is None:
        return None
    try:
        return ForecastSettings(**json.loads(row.value))
    except Exception:
        return None  # unreadable/outdated shape: treat as unsaved


@router.put("/forecast", response_model=ForecastSettings)
def put_forecast_settings(payload: ForecastSettings, db: Session = Depends(get_db)):
    row = db.get(AppSetting, FORECAST_KEY)
    value = json.dumps(payload.model_dump())
    if row is None:
        db.add(AppSetting(key=FORECAST_KEY, value=value, updated_at=utcnow()))
    else:
        row.value = value
        row.updated_at = utcnow()
    db.commit()
    return payload
