"""
FastAPI main application – all routes for all 9 entities + analytics.
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List

from . import models, schemas, crud
from .database import get_db, engine

app = FastAPI(
    title="YottaFlex Hackathon API",
    description="Transaction categorisation, recurring payments, household budget comparison.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=engine)


# ─── Health ──────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "YottaFlex Hackathon API running"}


# ─── Categories ──────────────────────────────────────────────

@app.get("/categories/", response_model=List[schemas.CategoryRead], tags=["Categories"])
def list_categories(db: Session = Depends(get_db)):
    return crud.get_categories(db)

@app.post("/categories/", response_model=schemas.CategoryRead, tags=["Categories"])
def create_category(cat: schemas.CategoryCreate, db: Session = Depends(get_db)):
    return crud.create_category(db, cat)

@app.get("/categories/{cat_id}", response_model=schemas.CategoryRead, tags=["Categories"])
def get_category(cat_id: str, db: Session = Depends(get_db)):
    obj = crud.get_category(db, cat_id)
    if not obj:
        raise HTTPException(404, "Category not found")
    return obj


# ─── Category Rules ──────────────────────────────────────────

@app.get("/category-rules/", response_model=List[schemas.CategoryRuleRead], tags=["CategoryRules"])
def list_rules(db: Session = Depends(get_db)):
    return crud.get_category_rules(db)

@app.post("/category-rules/", response_model=schemas.CategoryRuleRead, tags=["CategoryRules"])
def create_rule(rule: schemas.CategoryRuleCreate, db: Session = Depends(get_db)):
    return crud.create_category_rule(db, rule)


# ─── Users ───────────────────────────────────────────────────

@app.get("/users/", response_model=List[schemas.UserProfileRead], tags=["Users"])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)

@app.get("/users/{user_id}", response_model=schemas.UserProfileRead, tags=["Users"])
def get_user(user_id: str, db: Session = Depends(get_db)):
    obj = crud.get_user(db, user_id)
    if not obj:
        raise HTTPException(404, "User not found")
    return obj

@app.post("/users/", response_model=schemas.UserProfileRead, tags=["Users"])
def create_user(user: schemas.UserProfileCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)


# ─── Accounts ────────────────────────────────────────────────

@app.get("/accounts/", response_model=List[schemas.AccountRead], tags=["Accounts"])
def list_accounts(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_accounts(db, user_id=user_id)

@app.post("/accounts/", response_model=schemas.AccountRead, tags=["Accounts"])
def create_account(acc: schemas.AccountCreate, db: Session = Depends(get_db)):
    return crud.create_account(db, acc)


# ─── Merchants ───────────────────────────────────────────────

@app.get("/merchants/", response_model=List[schemas.MerchantRead], tags=["Merchants"])
def list_merchants(skip: int = 0, limit: int = 200, db: Session = Depends(get_db)):
    return crud.get_merchants(db, skip=skip, limit=limit)

@app.post("/merchants/", response_model=schemas.MerchantRead, tags=["Merchants"])
def create_merchant(m: schemas.MerchantCreate, db: Session = Depends(get_db)):
    return crud.create_merchant(db, m)


# ─── Recurring Series ────────────────────────────────────────

@app.get("/recurring-series/", response_model=List[schemas.RecurringSeriesRead], tags=["RecurringSeries"])
def list_recurring(account_id: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_recurring_series(db, account_id=account_id)

@app.post("/recurring-series/", response_model=schemas.RecurringSeriesRead, tags=["RecurringSeries"])
def create_recurring(rs: schemas.RecurringSeriesCreate, db: Session = Depends(get_db)):
    return crud.create_recurring_series(db, rs)


# ─── Transactions ────────────────────────────────────────────

@app.get("/transactions/", response_model=List[schemas.TransactionRead], tags=["Transactions"])
def list_transactions(
    account_id:  Optional[str] = None,
    category_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    return crud.get_transactions(db, account_id=account_id, category_id=category_id,
                                 skip=skip, limit=limit)

@app.post("/transactions/", response_model=schemas.TransactionRead, tags=["Transactions"])
def create_transaction(txn: schemas.TransactionCreate, db: Session = Depends(get_db)):
    return crud.create_transaction(db, txn)


# ─── Budgets ─────────────────────────────────────────────────

@app.get("/budgets/", response_model=List[schemas.BudgetRead], tags=["Budgets"])
def list_budgets(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_budgets(db, user_id=user_id)

@app.post("/budgets/", response_model=schemas.BudgetRead, tags=["Budgets"])
def create_budget(b: schemas.BudgetCreate, db: Session = Depends(get_db)):
    return crud.create_budget(db, b)

@app.post("/budgets/recalculate", tags=["Budgets"])
def recalculate_budget(user_id: str, category_id: str, month: int, year: int,
                       db: Session = Depends(get_db)):
    result = crud.recalculate_budget_spent(db, user_id, category_id, month, year)
    if not result:
        raise HTTPException(404, "Budget not found")
    return result


# ─── Insights ────────────────────────────────────────────────

@app.get("/insights/", response_model=List[schemas.InsightRead], tags=["Insights"])
def list_insights(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.get_insights(db, user_id=user_id)

@app.post("/insights/", response_model=schemas.InsightRead, tags=["Insights"])
def create_insight(ins: schemas.InsightCreate, db: Session = Depends(get_db)):
    return crud.create_insight(db, ins)


# ─── Analytics ───────────────────────────────────────────────

@app.get("/analytics/spending-by-category", tags=["Analytics"])
def spending_by_category(
    user_id: str,
    year: int,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rows = crud.spending_by_category(db, user_id=user_id, year=year, month=month)
    return [
        {"category_id": r[0], "category_name": r[1],
         "total_spent": abs(r[2] or 0), "transaction_count": r[3]}
        for r in rows
    ]

@app.get("/analytics/monthly-trend", tags=["Analytics"])
def monthly_trend(user_id: str, year: int, db: Session = Depends(get_db)):
    rows = crud.monthly_trend(db, user_id=user_id, year=year)
    result: dict = {}
    for r in rows:
        m = int(r[0])
        t = r[1]
        v = r[2] or 0
        if m not in result:
            result[m] = {"month": m, "total_spent": 0.0, "total_income": 0.0}
        if t in ("debit",):
            result[m]["total_spent"] += abs(v)
        elif t in ("credit",):
            result[m]["total_income"] += abs(v)
    return sorted(result.values(), key=lambda x: x["month"])

@app.get("/analytics/budget-comparison", tags=["Analytics"])
def budget_comparison(user_id: str, year: int, month: int,
                      db: Session = Depends(get_db)):
    budgets = crud.get_budgets(db, user_id=user_id)
    return [
        {
            "category_id":    b.category_id,
            "category_name":  b.category.name if b.category else b.category_id,
            "budgeted":       b.amount_budgeted,
            "spent":          b.amount_spent,
            "variance":       b.amount_budgeted - b.amount_spent,
            "status":         b.status.value,
        }
        for b in budgets
        if b.period_month == month and b.period_year == year
    ]


# ─── Data Generation Trigger ─────────────────────────────────

@app.post("/generate-data", tags=["DataGeneration"])
def generate_synthetic_data(
    users: int = Query(default=100, ge=1, le=1000),
    transactions_per_user: int = Query(default=500, ge=10, le=1000),
    seed: int = Query(default=20261022),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """
    Trigger synthetic data generation.
    Default: 100 users × 500 txns = 50,000 rows.
    For full 1,000 users × 500 txns = 500,000 set users=1000.
    Runs synchronously – may take a few minutes for large volumes.
    """
    from seed_data import seed as run_seed
    run_seed(n_users=users, txns_per_user=transactions_per_user)
    return {"message": f"Generated {users} users, ~{users * transactions_per_user} transactions."}
