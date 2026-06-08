from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from enum import Enum


class AccountType(str, Enum):
    ISA = "ISA"
    LISA = "LISA"
    SIPP = "SIPP"
    GIA = "GIA"
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    WORKPLACE_PENSION = "WORKPLACE_PENSION"
    PREMIUM_BONDS = "PREMIUM_BONDS"
    FIXED_BOND = "FIXED_BOND"
    CASH_ISA = "CASH_ISA"
    SS_ISA = "SS_ISA"
    OTHER = "OTHER"


class AccountCategory(str, Enum):
    INVESTMENTS = "INVESTMENTS"
    RETIREMENT = "RETIREMENT"
    SAVINGS = "SAVINGS"


# ── Account schemas ──────────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    name: str
    account_type: AccountType
    category: AccountCategory
    provider: Optional[str] = None
    current_value: float = 0.0
    initial_investment: Optional[float] = None  # INVESTMENTS / RETIREMENT only
    notes: Optional[str] = None

    @field_validator("current_value")
    @classmethod
    def value_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("current_value must be non-negative")
        return v

    @field_validator("initial_investment")
    @classmethod
    def initial_must_be_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("initial_investment must be non-negative")
        return v


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[AccountType] = None
    category: Optional[AccountCategory] = None
    provider: Optional[str] = None
    initial_investment: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class AccountValueUpdate(BaseModel):
    new_value: float
    note: Optional[str] = None

    @field_validator("new_value")
    @classmethod
    def value_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("new_value must be non-negative")
        return v


class AccountResponse(BaseModel):
    id: int
    name: str
    account_type: str
    category: str
    provider: Optional[str]
    current_value: float
    initial_investment: Optional[float] = None
    profit_amount: Optional[float] = None   # computed: current - initial
    profit_percent: Optional[float] = None  # computed: (current - initial) / initial * 100
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_account(cls, account) -> "AccountResponse":
        """Build response with computed profit fields."""
        profit_amount = None
        profit_percent = None
        if (
            account.initial_investment is not None
            and account.category in ("INVESTMENTS", "RETIREMENT")
        ):
            profit_amount = account.current_value - account.initial_investment
            if account.initial_investment != 0:
                profit_percent = (profit_amount / account.initial_investment) * 100
        return cls(
            id=account.id,
            name=account.name,
            account_type=account.account_type,
            category=account.category,
            provider=account.provider,
            current_value=account.current_value,
            initial_investment=account.initial_investment,
            profit_amount=profit_amount,
            profit_percent=profit_percent,
            notes=account.notes,
            is_active=account.is_active,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )


# ── Audit Log schemas ────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    account_id: int
    account_name: Optional[str] = None
    previous_value: float
    new_value: float
    change_amount: float
    change_percent: Optional[float]
    note: Optional[str]
    recorded_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard schemas ────────────────────────────────────────────────────────

class CategorySummary(BaseModel):
    category: str
    total_value: float
    account_count: int
    last_change_percent: Optional[float] = None


class MortgageSummary(BaseModel):
    total_property_value_share: float
    total_outstanding_share: float
    total_equity: float
    mortgage_count: int


class DashboardSummary(BaseModel):
    total_value: float          # accounts_total + property_equity
    accounts_total: float
    mortgage_equity: float      # property equity contribution
    categories: List[CategorySummary]
    account_count: int
    mortgage_summary: Optional[MortgageSummary] = None
    last_updated: Optional[datetime]


class HistoryPoint(BaseModel):
    date: datetime
    total_value: float
    category: Optional[str] = None


class DashboardHistory(BaseModel):
    points: List[HistoryPoint]


# ── Property schemas ──────────────────────────────────────────────────────────

class MortgagePartCreate(BaseModel):
    name: str
    lender: Optional[str] = None
    outstanding_balance: float
    interest_rate: Optional[float] = None
    mortgage_type: str = "REPAYMENT"          # REPAYMENT | INTEREST_ONLY
    term_years: Optional[int] = None
    term_months: Optional[int] = None         # 0–11 additional months
    monthly_payment: Optional[float] = None
    notes: Optional[str] = None

    @field_validator("outstanding_balance")
    @classmethod
    def balance_non_negative(cls, v):
        if v < 0:
            raise ValueError("outstanding_balance must be non-negative")
        return v

    @field_validator("mortgage_type")
    @classmethod
    def valid_type(cls, v):
        if v not in ("REPAYMENT", "INTEREST_ONLY"):
            raise ValueError("mortgage_type must be REPAYMENT or INTEREST_ONLY")
        return v

    @field_validator("term_months")
    @classmethod
    def months_in_range(cls, v):
        if v is not None and not (0 <= v <= 11):
            raise ValueError("term_months must be 0–11")
        return v


class MortgagePartUpdate(BaseModel):
    name: Optional[str] = None
    lender: Optional[str] = None
    interest_rate: Optional[float] = None
    mortgage_type: Optional[str] = None
    term_years: Optional[int] = None
    term_months: Optional[int] = None
    monthly_payment: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class MortgagePartBalanceUpdate(BaseModel):
    new_balance: float
    note: Optional[str] = None

    @field_validator("new_balance")
    @classmethod
    def must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("new_balance must be non-negative")
        return v


class MortgagePartResponse(BaseModel):
    id: int
    property_id: int
    name: str
    lender: Optional[str]
    outstanding_balance: float
    interest_rate: Optional[float]
    mortgage_type: str
    term_years: Optional[int]
    term_months: Optional[int]
    monthly_payment: Optional[float]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Computed
    remaining_term_months: Optional[int]   # total months
    monthly_interest: Optional[float]      # outstanding * rate/100/12

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_part(cls, p) -> "MortgagePartResponse":
        rem = None
        if p.term_years is not None or p.term_months is not None:
            rem = (p.term_years or 0) * 12 + (p.term_months or 0)
        interest = None
        if p.interest_rate is not None:
            interest = p.outstanding_balance * p.interest_rate / 100.0 / 12.0
        return cls(
            id=p.id, property_id=p.property_id, name=p.name,
            lender=p.lender, outstanding_balance=p.outstanding_balance,
            interest_rate=p.interest_rate, mortgage_type=p.mortgage_type,
            term_years=p.term_years, term_months=p.term_months,
            monthly_payment=p.monthly_payment, notes=p.notes,
            is_active=p.is_active, created_at=p.created_at, updated_at=p.updated_at,
            remaining_term_months=rem, monthly_interest=interest,
        )


class MortgagePartAuditLogResponse(BaseModel):
    id: int
    part_id: int
    part_name: Optional[str] = None
    property_name: Optional[str] = None
    previous_value: float
    new_value: float
    change_amount: float
    note: Optional[str]
    recorded_at: datetime
    model_config = {"from_attributes": True}


class PropertyCreate(BaseModel):
    name: str
    property_address: Optional[str] = None
    original_price: Optional[float] = None
    property_value: float
    ownership_percent: float = 100.0
    notes: Optional[str] = None

    @field_validator("property_value")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("property_value must be positive")
        return v

    @field_validator("ownership_percent")
    @classmethod
    def percent_in_range(cls, v):
        if not (0 < v <= 100):
            raise ValueError("ownership_percent must be 1–100")
        return v


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    property_address: Optional[str] = None
    original_price: Optional[float] = None
    ownership_percent: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class PropertyValueUpdate(BaseModel):
    new_value: float
    note: Optional[str] = None

    @field_validator("new_value")
    @classmethod
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("new_value must be positive")
        return v


class PropertyValueAuditLogResponse(BaseModel):
    id: int
    property_id: int
    property_name: Optional[str] = None
    previous_value: float
    new_value: float
    change_amount: float
    note: Optional[str]
    recorded_at: datetime
    model_config = {"from_attributes": True}


class PropertyResponse(BaseModel):
    id: int
    name: str
    property_address: Optional[str]
    original_price: Optional[float]
    property_value: float
    ownership_percent: float
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    mortgage_parts: List[MortgagePartResponse]
    # Computed
    total_outstanding: float            # sum of active parts' balances
    equity: float                       # (property_value - total_outstanding) * ownership/100
    property_value_share: float
    outstanding_share: float
    ltv_percent: Optional[float]
    property_gain: Optional[float]
    property_gain_percent: Optional[float]
    weighted_avg_rate: Optional[float]  # balance-weighted average interest rate
    total_monthly_payment: Optional[float]

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_property(cls, p) -> "PropertyResponse":
        parts = [MortgagePartResponse.from_orm_part(pt) for pt in p.mortgage_parts]
        total_out = sum(pt.outstanding_balance for pt in p.mortgage_parts)
        share = p.ownership_percent / 100.0
        pv_share = p.property_value * share
        ob_share = total_out * share
        equity = pv_share - ob_share
        ltv = (total_out / p.property_value * 100) if p.property_value > 0 else None
        gain = (p.property_value - p.original_price) if p.original_price is not None else None
        gain_pct = (gain / p.original_price * 100) if gain is not None and p.original_price else None

        # Weighted average rate
        w_rate = None
        rate_parts = [pt for pt in p.mortgage_parts if pt.interest_rate is not None]
        if rate_parts:
            total_bal = sum(pt.outstanding_balance for pt in rate_parts)
            if total_bal > 0:
                w_rate = sum(pt.outstanding_balance * pt.interest_rate for pt in rate_parts) / total_bal

        total_payment = None
        pay_parts = [pt for pt in p.mortgage_parts if pt.monthly_payment is not None]
        if pay_parts:
            total_payment = sum(pt.monthly_payment for pt in pay_parts)

        return cls(
            id=p.id, name=p.name, property_address=p.property_address,
            original_price=p.original_price, property_value=p.property_value,
            ownership_percent=p.ownership_percent, notes=p.notes,
            is_active=p.is_active, created_at=p.created_at, updated_at=p.updated_at,
            mortgage_parts=parts,
            total_outstanding=total_out, equity=equity,
            property_value_share=pv_share, outstanding_share=ob_share,
            ltv_percent=ltv, property_gain=gain, property_gain_percent=gain_pct,
            weighted_avg_rate=w_rate, total_monthly_payment=total_payment,
        )


