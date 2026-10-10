from timeutil import utcnow
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    provider = Column(String(255), nullable=True)
    current_value = Column(Float, default=0.0, nullable=False)
    initial_investment = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    audit_logs = relationship("AuditLog", back_populates="account", cascade="all, delete-orphan")
    share_holdings = relationship("ShareHolding", back_populates="account", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    previous_value = Column(Float, nullable=False)
    new_value = Column(Float, nullable=False)
    change_amount = Column(Float, nullable=False)
    change_percent = Column(Float, nullable=True)
    note = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=utcnow, nullable=False)

    account = relationship("Account", back_populates="audit_logs")



# ── Share Holdings ────────────────────────────────────────────────────────────

class ShareHolding(Base):
    """Tracks individual share positions within an investment account."""
    __tablename__ = "share_holdings"

    id           = Column(Integer, primary_key=True, index=True)
    account_id   = Column(Integer, ForeignKey("accounts.id"), nullable=False)

    ticker       = Column(String(20), nullable=False)       # e.g. "JPM", "TROW", "HSBA.L"
    display_name = Column(String(255), nullable=True)        # optional friendly label
    quantity     = Column(Float, nullable=False)              # number of shares held
    avg_cost     = Column(Float, nullable=True)              # average cost per share (ticker currency)
    currency     = Column(String(10), nullable=True)         # "USD", "GBP", "GBX" — inferred from suffix
    notes        = Column(Text, nullable=True)

    # Last successfully fetched price (persisted so stale data survives restarts)
    last_price          = Column(Float, nullable=True)
    last_price_currency = Column(String(10), nullable=True)
    last_price_at       = Column(DateTime, nullable=True)

    created_at   = Column(DateTime, default=utcnow, nullable=False)
    updated_at   = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    account = relationship("Account", back_populates="share_holdings")


# ── Property / Mortgage ───────────────────────────────────────────────────────

class Property(Base):
    """Represents a physical property. One property can have multiple mortgage parts."""
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)           # e.g. "Main Home"
    property_address = Column(Text, nullable=True)

    original_price = Column(Float, nullable=True)        # Purchase price paid
    property_value = Column(Float, nullable=False)       # Current estimated value

    ownership_percent = Column(Float, default=100.0, nullable=False)  # 0–100

    notes = Column(Text, nullable=True)
    purchase_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    mortgage_parts = relationship(
        "MortgagePart", back_populates="property",
        cascade="all, delete-orphan",
        primaryjoin="and_(MortgagePart.property_id==Property.id, MortgagePart.is_active==True)",
        lazy="joined",
    )
    value_audit_logs = relationship(
        "PropertyValueAuditLog", back_populates="property", cascade="all, delete-orphan"
    )


class MortgagePart(Base):
    """A single mortgage tranche on a property (e.g. fixed part, interest-only part)."""
    __tablename__ = "mortgage_parts"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    name = Column(String(255), nullable=False)           # e.g. "Fixed Rate Part"
    lender = Column(String(255), nullable=True)

    outstanding_balance = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=True)         # Annual % rate

    # REPAYMENT or INTEREST_ONLY
    mortgage_type = Column(String(20), nullable=False, default="REPAYMENT")

    # Term remaining
    term_years = Column(Integer, nullable=True)          # whole years
    term_months = Column(Integer, nullable=True)         # extra months (0–11)

    monthly_payment = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    property = relationship("Property", back_populates="mortgage_parts", foreign_keys=[property_id])
    balance_audit_logs = relationship(
        "MortgagePartAuditLog", back_populates="part", cascade="all, delete-orphan"
    )


class PropertyValueAuditLog(Base):
    """Tracks changes to a property's estimated value."""
    __tablename__ = "property_value_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    previous_value = Column(Float, nullable=False)
    new_value = Column(Float, nullable=False)
    change_amount = Column(Float, nullable=False)
    note = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=utcnow, nullable=False)

    property = relationship("Property", back_populates="value_audit_logs")


class MortgagePartAuditLog(Base):
    """Tracks changes to a mortgage part's outstanding balance."""
    __tablename__ = "mortgage_part_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("mortgage_parts.id"), nullable=False)
    previous_value = Column(Float, nullable=False)
    new_value = Column(Float, nullable=False)
    change_amount = Column(Float, nullable=False)
    note = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=utcnow, nullable=False)

    part = relationship("MortgagePart", back_populates="balance_audit_logs")


class AppSetting(Base):
    """Small JSON key/value store for UI settings shared across devices (e.g. the forecast)."""
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
