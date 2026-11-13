"""
Bulletproof standalone database seeder for YottaFlex Hackathon.
Can be executed directly from terminal:
    python seed_data.py [n_users] [txns_per_user]
"""

import sys
import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from faker import Faker
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models
from app.utils.data_generator import (
    CATEGORIES, CATEGORY_RULES, MERCHANT_TEMPLATES, TIMEZONES,
    usr_id, acc_id, txn_id, bud_id, rec_id, _export_ground_truth,
    _seed_categories, _seed_category_rules, _seed_merchants,
    _seed_users_and_accounts, _seed_recurring_series, _seed_insights
)

SEED = 20261022
YEAR = 2026

def seed(n_users: int = 50, txns_per_user: int = 50):
    print(f"🚀 Starting Seeder: {n_users} Users, {txns_per_user} Transactions each...")
    Faker.seed(SEED)
    random.seed(SEED)
    np.random.seed(SEED)

    db = SessionLocal()
    try:
        # Disable foreign key checks for clean wipe
        db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        db.commit()

        print("🔄 Clearing existing database records...")
        for tbl in [models.Insight, models.Budget, models.Transaction,
                    models.RecurringSeries, models.Account, models.Merchant,
                    models.CategoryRule, models.UserProfile, models.Category]:
            db.query(tbl).delete()
        db.commit()

        db.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        db.commit()

        print("📂 1/7 Seeding categories...")
        cats = _seed_categories(db)

        print("📂 2/7 Seeding category rules...")
        _seed_category_rules(db)

        print("🏪 3/7 Seeding merchants...")
        merchants = _seed_merchants(db)

        print(f"👤 4/7 Generating {n_users} users and accounts...")
        users, accounts = _seed_users_and_accounts(db, n_users)

        print("🔄 5/7 Generating recurring series...")
        rec_series = _seed_recurring_series(db, accounts, merchants)

        print(f"💳 6/7 Generating ~{n_users * txns_per_user} transactions...")
        spend_cats = ["FOOD","GROC","REST","TRANS","ENTMT","HEALTH","SHOP","TRAVEL","UTIL","MISC","SUBSC"]
        merchant_by_cat = {}
        for m in merchants:
            merchant_by_cat.setdefault(m.category_id, []).append(m)

        all_txns = []
        ground_truth = []
        txn_counter = 1

        user_accounts = {}
        for acc in accounts:
            user_accounts.setdefault(acc.user_id, []).append(acc)

        rec_by_account = {}
        for rs in rec_series:
            rec_by_account.setdefault(rs.account_id, []).append(rs)

        for user in users:
            u_accs = user_accounts.get(user.id, [])
            if not u_accs:
                continue
            primary_acc = u_accs[0]
            tz = random.choice(TIMEZONES)

            # Recurring transactions
            for rs in rec_by_account.get(primary_acc.id, []):
                for month in range(1, 13):
                    if random.random() < 0.05:
                        ground_truth.append({
                            "issue_type": "recurring_missed",
                            "account_id": primary_acc.id,
                            "series_id": rs.id,
                            "month": month,
                            "year": YEAR,
                            "expected_amount": rs.amount,
                            "ground_truth_label": "RECURRING_SKIP",
                        })
                        continue

                    day = min(rs.day_of_month or 1, 28)
                    txn_date = datetime(YEAR, month, day)
                    is_credit = rs.category_id == "SALARY"
                    txn_type = models.TransactionType.CREDIT if is_credit else models.TransactionType.DEBIT

                    all_txns.append({
                        "id": txn_id(txn_counter),
                        "account_id": primary_acc.id,
                        "merchant_id": rs.merchant_id,
                        "category_id": rs.category_id,
                        "recurring_series_id": rs.id,
                        "amount": rs.amount,
                        "txn_type": txn_type.value,
                        "status": "cleared",
                        "description": f"Recurring: {rs.category_id}",
                        "txn_date": txn_date,
                        "posted_date": txn_date + timedelta(days=1),
                        "is_recurring": True,
                        "timezone": tz,
                        "is_anomaly": False,
                        "ground_truth_label": None,
                    })
                    txn_counter += 1

            # Random spending
            for _ in range(txns_per_user):
                cat_id = random.choice(spend_cats)
                cat_m = merchant_by_cat.get(cat_id, merchants)
                merchant = random.choice(cat_m)
                month = random.randint(1, 12)
                day = random.randint(1, 28)
                txn_date = datetime(YEAR, month, day, random.randint(0, 23), random.randint(0, 59))
                amount = -abs(round(np.random.lognormal(mean=3.5, sigma=1.0), 2))
                txn_type = models.TransactionType.DEBIT
                is_anomaly = False
                gt_label = None

                if random.random() < 0.05:
                    txn_type = models.TransactionType.TRANSFER
                    is_anomaly = True
                    gt_label = "TRANSFER_AS_SPEND"
                    ground_truth.append({
                        "issue_type": "transfer_double",
                        "txn_id": txn_id(txn_counter),
                        "account_id": primary_acc.id,
                        "amount": amount,
                        "txn_date": str(txn_date),
                        "ground_truth_label": gt_label,
                    })
                elif random.random() < 0.03:
                    txn_type = models.TransactionType.REFUND
                    amount = abs(amount)
                    is_anomaly = True
                    gt_label = "REFUND_AS_EXPENSE"
                    ground_truth.append({
                        "issue_type": "refund_detected",
                        "txn_id": txn_id(txn_counter),
                        "account_id": primary_acc.id,
                        "amount": amount,
                        "txn_date": str(txn_date),
                        "ground_truth_label": gt_label,
                    })

                all_txns.append({
                    "id": txn_id(txn_counter),
                    "account_id": primary_acc.id,
                    "merchant_id": merchant.id,
                    "category_id": cat_id,
                    "recurring_series_id": None,
                    "amount": amount,
                    "txn_type": txn_type.value,
                    "status": "cleared",
                    "description": f"{merchant.name} purchase",
                    "txn_date": txn_date,
                    "posted_date": txn_date + timedelta(days=random.randint(0, 2)),
                    "is_recurring": False,
                    "timezone": tz,
                    "is_anomaly": is_anomaly,
                    "ground_truth_label": gt_label,
                })
                txn_counter += 1

        # Direct bulk insert (pure python dicts without Pandas NaN conversion)
        print(f"   Writing {len(all_txns):,} transactions to MySQL in batches...")
        chunk_size = 5000
        for start in range(0, len(all_txns), chunk_size):
            chunk = all_txns[start:start + chunk_size]
            db.bulk_insert_mappings(models.Transaction, chunk)
            db.commit()

        # Build DataFrame for budget & insight calculation
        txn_df = pd.DataFrame(all_txns)

        print("📊 7/7 Generating budgets & insights...")
        # Fast vectorized budget seeding
        if not txn_df.empty:
            txn_copy = txn_df[txn_df["txn_type"] == "debit"].copy()
            txn_copy["month"] = pd.to_datetime(txn_copy["txn_date"]).dt.month
            txn_copy["uid"] = txn_copy["account_id"].apply(lambda acc: f"USR-{acc.split('-')[1]}")
            spent_summary = txn_copy.groupby(["uid", "month", "category_id"])["amount"].sum().abs().to_dict()
        else:
            spent_summary = {}

        budget_objs = []
        for i, user in enumerate(users, 1):
            for month in range(1, 13):
                for cat_id in spend_cats:
                    bid = bud_id(i, YEAR, month, cat_id)
                    budgeted = round(random.uniform(100, 1500), 2)
                    spent = round(float(spent_summary.get((user.id, month, cat_id), 0.0)), 2)
                    if spent > budgeted:
                        status = models.BudgetStatus.OVER_BUDGET
                    elif spent < budgeted * 0.5:
                        status = models.BudgetStatus.UNDER_BUDGET
                    else:
                        status = models.BudgetStatus.ON_TRACK

                    budget_objs.append({
                        "id": bid,
                        "user_id": user.id,
                        "category_id": cat_id,
                        "period_month": month,
                        "period_year": YEAR,
                        "amount_budgeted": budgeted,
                        "amount_spent": spent,
                        "status": status.value,
                    })

        for start in range(0, len(budget_objs), 5000):
            db.bulk_insert_mappings(models.Budget, budget_objs[start:start+5000])
            db.commit()

        # Seed insights
        _seed_insights(db, users, txn_df)

        # Export ground truth files
        _export_ground_truth(ground_truth)

        print(f"\n✅ SUCCESS! Generated {len(users)} users, {len(accounts)} accounts, and {len(all_txns):,} transactions!")
        print("🎉 Database is ready for dashboard visualization!")

    finally:
        db.close()

if __name__ == "__main__":
    n_users = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    txns = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    seed(n_users, txns)
