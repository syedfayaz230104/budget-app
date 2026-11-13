"""
SQLAlchemy ORM models for all 9 core entities.
Entities: UserProfile, Account, Merchant, Transaction,
          Category, CategoryRule, Budget, RecurringSeries, Insight
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    Text, ForeignKey, Enum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .database import Base
import enum


# ─────────────────── Enums ───────────────────

class AccountType(str, enum.Enum):
    CHECKING = "checking"
    SAVINGS  = "savings"
    CREDIT   = "credit"

class AccountStatus(str, enum.Enum):
    ACTIVE   = "active"
    CLOSED   = "closed"
    FROZEN   = "frozen"

class TransactionType(str, enum.Enum):
    DEBIT    = "debit"
    CREDIT   = "credit"
    TRANSFER = "transfer"
    REFUND   = "refund"

class TransactionStatus(str, enum.Enum):
    PENDING  = "pending"
    CLEARED  = "cleared"
    FAILED   = "failed"

class Frequency(str, enum.Enum):
    WEEKLY   = "weekly"
    MONTHLY  = "monthly"
    ANNUAL   = "annual"

class BudgetStatus(str, enum.Enum):
    ON_TRACK     = "on_track"
    OVER_BUDGET  = "over_budget"
    UNDER_BUDGET = "under_budget"

class InsightType(str, enum.Enum):
    OVER_BUDGET      = "over_budget"
    UNUSUAL_SPEND    = "unusual_spend"
    RECURRING_MISSED = "recurring_missed"
    REFUND_DETECTED  = "refund_detected"
    TRANSFER_DOUBLE  = "transfer_double"
    BUDGET_MISMATCH  = "budget_mismatch"

class Severity(str, enum.Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


# ─────────────────── Category ───────────────────

class Category(Base):
    __tablename__ = "categories"

    id              = Column(String(32), primary_key=True)   # e.g. FOOD, RENT
    name            = Column(String(128), nullable=False)
    parent_category = Column(String(32), ForeignKey("categories.id"), nullable=True)
    description     = Column(Text, nullable=True)

    children    = relationship("Category",   back_populates="parent")
    parent      = relationship("Category",   back_populates="children", remote_side="Category.id")
    rules       = relationship("CategoryRule", back_populates="category")
    transactions= relationship("Transaction", back_populates="category")
    budgets     = relationship("Budget",      back_populates="category")
    insights    = relationship("Insight",     back_populates="category")


# ─────────────────── CategoryRule ───────────────────

class CategoryRule(Base):
    __tablename__ = "category_rules"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    merchant_pattern = Column(String(255), nullable=False)
    category_id      = Column(String(32), ForeignKey("categories.id"), nullable=False)
    priority         = Column(Integer, default=1)
    is_active        = Column(Boolean, default=True)

    category = relationship("Category", back_populates="rules")


# ─────────────────── UserProfile ───────────────────

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id         = Column(String(16), primary_key=True)   # USR-000001
    first_name = Column(String(64), nullable=False)
    last_name  = Column(String(64), nullable=False)
    email      = Column(String(128), unique=True, nullable=False)
    phone      = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active  = Column(Boolean, default=True)

    accounts = relationship("Account", back_populates="user")
    budgets  = relationship("Budget",  back_populates="user")
    insights = relationship("Insight", back_populates="user")


# ─────────────────── Account ───────────────────

class Account(Base):
    __tablename__ = "accounts"

    id           = Column(String(24), primary_key=True)   # ACC-USR000001-01
    user_id      = Column(String(16), ForeignKey("user_profiles.id"), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    balance      = Column(Float, default=0.0)
    currency     = Column(String(8), default="USD")
    opened_at    = Column(DateTime, default=datetime.utcnow)
    closed_at    = Column(DateTime, nullable=True)
    status       = Column(Enum(AccountStatus), default=AccountStatus.ACTIVE)

    user             = relationship("UserProfile",    back_populates="accounts")
    transactions     = relationship("Transaction",    back_populates="account")
    recurring_series = relationship("RecurringSeries",back_populates="account")


# ─────────────────── Merchant ───────────────────

class Merchant(Base):
    __tablename__ = "merchants"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(255), nullable=False)
    alias         = Column(String(255), nullable=True)
    category_id   = Column(String(32), ForeignKey("categories.id"), nullable=True)
    city          = Column(String(128), nullable=True)
    state         = Column(String(64), nullable=True)
    country       = Column(String(64), default="US")
    is_online     = Column(Boolean, default=False)

    category         = relationship("Category")
    transactions     = relationship("Transaction",    back_populates="merchant")
    recurring_series = relationship("RecurringSeries",back_populates="merchant")


# ─────────────────── RecurringSeries ───────────────────

class RecurringSeries(Base):
    __tablename__ = "recurring_series"

    id          = Column(String(16), primary_key=True)   # REC-000001
    account_id  = Column(String(24), ForeignKey("accounts.id"), nullable=False)
    merchant_id = Column(Integer,    ForeignKey("merchants.id"), nullable=True)
    category_id = Column(String(32), ForeignKey("categories.id"), nullable=True)
    frequency   = Column(Enum(Frequency), nullable=False)
    amount      = Column(Float, nullable=False)
    start_date  = Column(DateTime, nullable=False)
    end_date    = Column(DateTime, nullable=True)
    day_of_month= Column(Integer, nullable=True)   # 1-28
    is_active   = Column(Boolean, default=True)

    account      = relationship("Account",  back_populates="recurring_series")
    merchant     = relationship("Merchant", back_populates="recurring_series")
    category     = relationship("Category")
    transactions = relationship("Transaction", back_populates="recurring_series")


# ─────────────────── Transaction ───────────────────

class Transaction(Base):
    __tablename__ = "transactions"

    id                 = Column(String(24), primary_key=True)   # TXN-2026-00000001
    account_id         = Column(String(24), ForeignKey("accounts.id"),          nullable=False)
    merchant_id        = Column(Integer,    ForeignKey("merchants.id"),          nullable=True)
    category_id        = Column(String(32), ForeignKey("categories.id"),         nullable=True)
    recurring_series_id= Column(String(16), ForeignKey("recurring_series.id"),   nullable=True)
    amount             = Column(Float, nullable=False)   # negative = spend
    txn_type           = Column(Enum(TransactionType), nullable=False)
    status             = Column(Enum(TransactionStatus), default=TransactionStatus.CLEARED)
    description        = Column(String(512), nullable=True)
    txn_date           = Column(DateTime, nullable=False)
    posted_date        = Column(DateTime, nullable=True)
    is_recurring       = Column(Boolean, default=False)
    timezone           = Column(String(64), default="UTC")
    is_anomaly         = Column(Boolean, default=False)
    ground_truth_label = Column(String(64), nullable=True)

    account          = relationship("Account",         back_populates="transactions")
    merchant         = relationship("Merchant",        back_populates="transactions")
    category         = relationship("Category",        back_populates="transactions")
    recurring_series = relationship("RecurringSeries", back_populates="transactions")

    __table_args__ = (
        Index("idx_txn_account_date", "account_id", "txn_date"),
        Index("idx_txn_category",     "category_id"),
    )


# ─────────────────── Budget ───────────────────

class Budget(Base):
    __tablename__ = "budgets"

    id               = Column(String(48), primary_key=True)  # BUD-USR000001-2026-01-FOOD
    user_id          = Column(String(16), ForeignKey("user_profiles.id"), nullable=False)
    category_id      = Column(String(32), ForeignKey("categories.id"),    nullable=False)
    period_month     = Column(Integer, nullable=False)   # 1-12
    period_year      = Column(Integer, nullable=False)
    amount_budgeted  = Column(Float, nullable=False)
    amount_spent     = Column(Float, default=0.0)
    status           = Column(Enum(BudgetStatus), default=BudgetStatus.ON_TRACK)

    user     = relationship("UserProfile", back_populates="budgets")
    category = relationship("Category",    back_populates="budgets")

    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "period_month", "period_year",
                         name="uq_budget_user_cat_period"),
    )


# ─────────────────── Insight ───────────────────

class Insight(Base):
    __tablename__ = "insights"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(String(16), ForeignKey("user_profiles.id"), nullable=False)
    category_id  = Column(String(32), ForeignKey("categories.id"),    nullable=True)
    insight_type = Column(Enum(InsightType), nullable=False)
    description  = Column(Text, nullable=False)
    severity     = Column(Enum(Severity), default=Severity.LOW)
    created_at   = Column(DateTime, default=datetime.utcnow)
    is_resolved  = Column(Boolean, default=False)

    user     = relationship("UserProfile", back_populates="insights")
    category = relationship("Category",    back_populates="insights")
