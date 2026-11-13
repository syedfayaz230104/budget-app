"""
CRUD helpers for all 9 entities.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
from . import models, schemas


# ─── Category ────────────────────────────────────────────────

def get_categories(db: Session) -> List[models.Category]:
    return db.query(models.Category).all()

def create_category(db: Session, cat: schemas.CategoryCreate) -> models.Category:
    obj = models.Category(**cat.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def get_category(db: Session, cat_id: str) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.id == cat_id).first()


# ─── CategoryRule ────────────────────────────────────────────

def get_category_rules(db: Session) -> List[models.CategoryRule]:
    return db.query(models.CategoryRule).all()

def create_category_rule(db: Session, rule: schemas.CategoryRuleCreate) -> models.CategoryRule:
    obj = models.CategoryRule(**rule.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


# ─── UserProfile ─────────────────────────────────────────────

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.UserProfile]:
    return db.query(models.UserProfile).offset(skip).limit(limit).all()

def get_user(db: Session, user_id: str) -> Optional[models.UserProfile]:
    return db.query(models.UserProfile).filter(models.UserProfile.id == user_id).first()

def create_user(db: Session, user: schemas.UserProfileCreate) -> models.UserProfile:
    obj = models.UserProfile(**user.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


# ─── Account ─────────────────────────────────────────────────

def get_accounts(db: Session, user_id: Optional[str] = None) -> List[models.Account]:
    q = db.query(models.Account)
    if user_id:
        q = q.filter(models.Account.user_id == user_id)
    return q.all()

def create_account(db: Session, acc: schemas.AccountCreate) -> models.Account:
    obj = models.Account(**acc.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


# ─── Merchant ────────────────────────────────────────────────

def get_merchants(db: Session, skip: int = 0, limit: int = 200) -> List[models.Merchant]:
    return db.query(models.Merchant).offset(skip).limit(limit).all()

def create_merchant(db: Session, m: schemas.MerchantCreate) -> models.Merchant:
    obj = models.Merchant(**m.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


# ─── RecurringSeries ─────────────────────────────────────────

def get_recurring_series(db: Session, account_id: Optional[str] = None):
    q = db.query(models.RecurringSeries)
    if account_id:
        q = q.filter(models.RecurringSeries.account_id == account_id)
    return q.all()

def create_recurring_series(db: Session, rs: schemas.RecurringSeriesCreate):
    obj = models.RecurringSeries(**rs.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


# ─── Transaction ─────────────────────────────────────────────

def get_transactions(
    db: Session,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 500,
) -> List[models.Transaction]:
    q = db.query(models.Transaction)
    if account_id:
        q = q.filter(models.Transaction.account_id == account_id)
    if category_id:
        q = q.filter(models.Transaction.category_id == category_id)
    return q.order_by(models.Transaction.txn_date.desc()).offset(skip).limit(limit).all()

def create_transaction(db: Session, txn: schemas.TransactionCreate) -> models.Transaction:
    obj = models.Transaction(**txn.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def bulk_insert_transactions(db: Session, txns: list):
    db.bulk_insert_mappings(models.Transaction, txns)
    db.commit()


# ─── Budget ──────────────────────────────────────────────────

def get_budgets(db: Session, user_id: Optional[str] = None):
    q = db.query(models.Budget)
    if user_id:
        q = q.filter(models.Budget.user_id == user_id)
    return q.all()

def create_budget(db: Session, b: schemas.BudgetCreate):
    obj = models.Budget(**b.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def recalculate_budget_spent(db: Session, user_id: str, category_id: str, month: int, year: int):
    """Re-compute amount_spent from transactions and update budget status."""
    total = db.query(func.sum(models.Transaction.amount)).filter(
        models.Transaction.category_id == category_id,
        models.Transaction.account_id.in_(
            db.query(models.Account.id).filter(models.Account.user_id == user_id)
        ),
        extract("month", models.Transaction.txn_date) == month,
        extract("year",  models.Transaction.txn_date) == year,
        models.Transaction.txn_type.in_(["debit", "transfer"]),
    ).scalar() or 0.0

    budget = db.query(models.Budget).filter(
        models.Budget.user_id    == user_id,
        models.Budget.category_id== category_id,
        models.Budget.period_month == month,
        models.Budget.period_year  == year,
    ).first()

    if budget:
        budget.amount_spent = abs(total)
        if budget.amount_spent > budget.amount_budgeted:
            budget.status = models.BudgetStatus.OVER_BUDGET
        elif budget.amount_spent < budget.amount_budgeted * 0.5:
            budget.status = models.BudgetStatus.UNDER_BUDGET
        else:
            budget.status = models.BudgetStatus.ON_TRACK
        db.commit()
        db.refresh(budget)
    return budget


# ─── Insight ─────────────────────────────────────────────────

def get_insights(db: Session, user_id: Optional[str] = None):
    q = db.query(models.Insight)
    if user_id:
        q = q.filter(models.Insight.user_id == user_id)
    return q.order_by(models.Insight.created_at.desc()).all()

def create_insight(db: Session, ins: schemas.InsightCreate):
    obj = models.Insight(**ins.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


# ─── Analytics ───────────────────────────────────────────────

def spending_by_category(db: Session, user_id: str, year: int, month: Optional[int] = None):
    """Return spending totals grouped by category for a user."""
    q = (
        db.query(
            models.Transaction.category_id,
            models.Category.name,
            func.sum(models.Transaction.amount).label("total"),
            func.count(models.Transaction.id).label("count"),
        )
        .join(models.Account, models.Transaction.account_id == models.Account.id)
        .join(models.Category, models.Transaction.category_id == models.Category.id)
        .filter(
            models.Account.user_id == user_id,
            extract("year", models.Transaction.txn_date) == year,
            models.Transaction.txn_type.in_(["debit"]),
        )
    )
    if month:
        q = q.filter(extract("month", models.Transaction.txn_date) == month)
    return q.group_by(models.Transaction.category_id, models.Category.name).all()

def monthly_trend(db: Session, user_id: str, year: int):
    """Return monthly income vs spending for a user."""
    rows = (
        db.query(
            extract("month", models.Transaction.txn_date).label("month"),
            models.Transaction.txn_type,
            func.sum(models.Transaction.amount).label("total"),
        )
        .join(models.Account, models.Transaction.account_id == models.Account.id)
        .filter(
            models.Account.user_id == user_id,
            extract("year", models.Transaction.txn_date) == year,
        )
        .group_by("month", models.Transaction.txn_type)
        .order_by("month")
        .all()
    )
    return rows
