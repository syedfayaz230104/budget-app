"""
Validation suite – run after data generation to verify data integrity.
Checks: PK uniqueness, FK integrity, arithmetic reconciliation,
        lifecycle transitions, duplicate detection.
"""

import pandas as pd
from sqlalchemy import text
from ..database import SessionLocal
from .. import models


def run_all_validations() -> dict:
    db = SessionLocal()
    results = {}
    try:
        results["pk_uniqueness"]       = check_pk_uniqueness(db)
        results["fk_integrity"]        = check_fk_integrity(db)
        results["budget_reconciliation"]= check_budget_reconciliation(db)
        results["duplicate_transactions"]= check_duplicate_transactions(db)
        results["lifecycle_states"]    = check_lifecycle_states(db)
    finally:
        db.close()
    return results


def check_pk_uniqueness(db) -> dict:
    issues = []
    for Model, label in [
        (models.Transaction, "transactions"),
        (models.UserProfile, "user_profiles"),
        (models.Account,     "accounts"),
        (models.Budget,      "budgets"),
        (models.RecurringSeries, "recurring_series"),
    ]:
        total = db.query(Model).count()
        ids   = [r[0] for r in db.query(Model.id).all()]
        unique_ids = len(set(ids))
        if total != unique_ids:
            issues.append(f"{label}: {total - unique_ids} duplicate PKs found")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_fk_integrity(db) -> dict:
    issues = []
    # Transactions must reference valid accounts
    orphan_txns = db.execute(text(
        "SELECT COUNT(*) FROM transactions t "
        "LEFT JOIN accounts a ON t.account_id = a.id "
        "WHERE a.id IS NULL"
    )).scalar()
    if orphan_txns:
        issues.append(f"{orphan_txns} transactions with invalid account_id")

    # Budgets must reference valid users
    orphan_budgets = db.execute(text(
        "SELECT COUNT(*) FROM budgets b "
        "LEFT JOIN user_profiles u ON b.user_id = u.id "
        "WHERE u.id IS NULL"
    )).scalar()
    if orphan_budgets:
        issues.append(f"{orphan_budgets} budgets with invalid user_id")

    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_budget_reconciliation(db) -> dict:
    """Verify budget amount_spent matches sum of actual transactions."""
    issues = []
    budgets = db.query(models.Budget).limit(100).all()  # sample 100
    for b in budgets:
        actual = db.execute(text(
            "SELECT COALESCE(ABS(SUM(t.amount)), 0) FROM transactions t "
            "JOIN accounts a ON t.account_id = a.id "
            "WHERE a.user_id = :uid AND t.category_id = :cat "
            "AND MONTH(t.txn_date) = :m AND YEAR(t.txn_date) = :y "
            "AND t.txn_type = 'debit'"
        ), {"uid": b.user_id, "cat": b.category_id, "m": b.period_month, "y": b.period_year}
        ).scalar() or 0.0

        diff = abs(round(actual, 2) - round(b.amount_spent, 2))
        if diff > 1.0:   # allow $1 rounding tolerance
            issues.append(
                f"Budget {b.id}: recorded={b.amount_spent:.2f}, actual={actual:.2f}, diff={diff:.2f}"
            )
    return {"status": "PASS" if not issues else "WARN", "issues": issues[:10]}


def check_duplicate_transactions(db) -> dict:
    """Detect potential duplicate transactions (same account, amount, date)."""
    rows = db.execute(text(
        "SELECT account_id, amount, DATE(txn_date), COUNT(*) as cnt "
        "FROM transactions "
        "GROUP BY account_id, amount, DATE(txn_date) "
        "HAVING cnt > 3 "
        "LIMIT 10"
    )).fetchall()
    issues = [str(r) for r in rows]
    return {"status": "WARN" if issues else "PASS", "issues": issues}


def check_lifecycle_states(db) -> dict:
    """Accounts with txns after closure should be flagged."""
    issues = []
    rows = db.execute(text(
        "SELECT a.id, a.closed_at, MAX(t.txn_date) as last_txn "
        "FROM accounts a JOIN transactions t ON t.account_id = a.id "
        "WHERE a.closed_at IS NOT NULL AND t.txn_date > a.closed_at "
        "GROUP BY a.id, a.closed_at "
        "LIMIT 10"
    )).fetchall()
    for r in rows:
        issues.append(f"Account {r[0]}: txn after closure ({r[1]})")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}
