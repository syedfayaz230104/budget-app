"""
Pydantic v2-compatible schemas for all 9 entities.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from .models import (
    AccountType, AccountStatus, TransactionType, TransactionStatus,
    Frequency, BudgetStatus, InsightType, Severity
)


# ─── Category ────────────────────────────────────────────────

class CategoryBase(BaseModel):
    id: str
    name: str
    parent_category: Optional[str] = None
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    model_config = {"from_attributes": True}


# ─── CategoryRule ────────────────────────────────────────────

class CategoryRuleBase(BaseModel):
    merchant_pattern: str
    category_id: str
    priority: int = 1
    is_active: bool = True

class CategoryRuleCreate(CategoryRuleBase):
    pass

class CategoryRuleRead(CategoryRuleBase):
    id: int
    model_config = {"from_attributes": True}


# ─── UserProfile ─────────────────────────────────────────────

class UserProfileBase(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    is_active: bool = True

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileRead(UserProfileBase):
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Account ─────────────────────────────────────────────────

class AccountBase(BaseModel):
    id: str
    user_id: str
    account_type: AccountType
    balance: float = 0.0
    currency: str = "USD"
    status: AccountStatus = AccountStatus.ACTIVE

class AccountCreate(AccountBase):
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

class AccountRead(AccountBase):
    opened_at: datetime
    closed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─── Merchant ────────────────────────────────────────────────

class MerchantBase(BaseModel):
    name: str
    alias: Optional[str] = None
    category_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "US"
    is_online: bool = False

class MerchantCreate(MerchantBase):
    pass

class MerchantRead(MerchantBase):
    id: int
    model_config = {"from_attributes": True}


# ─── RecurringSeries ─────────────────────────────────────────

class RecurringSeriesBase(BaseModel):
    id: str
    account_id: str
    merchant_id: Optional[int] = None
    category_id: Optional[str] = None
    frequency: Frequency
    amount: float
    start_date: datetime
    end_date: Optional[datetime] = None
    day_of_month: Optional[int] = None
    is_active: bool = True

class RecurringSeriesCreate(RecurringSeriesBase):
    pass

class RecurringSeriesRead(RecurringSeriesBase):
    model_config = {"from_attributes": True}


# ─── Transaction ─────────────────────────────────────────────

class TransactionBase(BaseModel):
    id: str
    account_id: str
    merchant_id: Optional[int] = None
    category_id: Optional[str] = None
    recurring_series_id: Optional[str] = None
    amount: float
    txn_type: TransactionType
    status: TransactionStatus = TransactionStatus.CLEARED
    description: Optional[str] = None
    txn_date: datetime
    posted_date: Optional[datetime] = None
    is_recurring: bool = False
    timezone: str = "UTC"
    is_anomaly: bool = False
    ground_truth_label: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionRead(TransactionBase):
    model_config = {"from_attributes": True}


# ─── Budget ──────────────────────────────────────────────────

class BudgetBase(BaseModel):
    id: str
    user_id: str
    category_id: str
    period_month: int
    period_year: int
    amount_budgeted: float
    amount_spent: float = 0.0
    status: BudgetStatus = BudgetStatus.ON_TRACK

class BudgetCreate(BudgetBase):
    pass

class BudgetRead(BudgetBase):
    model_config = {"from_attributes": True}


# ─── Insight ─────────────────────────────────────────────────

class InsightBase(BaseModel):
    user_id: str
    category_id: Optional[str] = None
    insight_type: InsightType
    description: str
    severity: Severity = Severity.LOW
    is_resolved: bool = False

class InsightCreate(InsightBase):
    pass

class InsightRead(InsightBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Summary / Stats ─────────────────────────────────────────

class SpendingSummary(BaseModel):
    category_id: str
    category_name: str
    total_spent: float
    transaction_count: int

class BudgetComparison(BaseModel):
    category_id: str
    category_name: str
    budgeted: float
    spent: float
    variance: float
    status: str

class MonthlyTrend(BaseModel):
    month: str
    total_spent: float
    total_income: float
