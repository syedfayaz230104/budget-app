"""
Full synthetic data generator.
- 1,000 UserProfiles
- Multiple Accounts per user
- 500,000 Transactions across 12 months
- Merchants, Categories, CategoryRules
- RecurringSeries (salary, rent, subscriptions)
- Budgets (monthly per user per category)
- Insights derived from anomalies
- Edge cases injected deterministically
- Fixed seed for reproducibility
- Ground truth exported to CSV/JSON
"""

import random
import string
import json
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict

import numpy as np
import pandas as pd
from faker import Faker

from ..database import SessionLocal
from sqlalchemy import text
from sqlalchemy import text

from .. import models

SEED = 20261022
fake = Faker()
Faker.seed(SEED)
random.seed(SEED)
np.random.seed(SEED)

YEAR = 2026
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", "exports")

# ─── Category taxonomy ───────────────────────────────────────

CATEGORIES = [
    {"id": "FOOD",    "name": "Food & Dining",       "parent_category": None,   "description": "Restaurants, groceries, cafes"},
    {"id": "GROC",    "name": "Groceries",            "parent_category": "FOOD", "description": "Supermarkets and grocery stores"},
    {"id": "REST",    "name": "Restaurants",          "parent_category": "FOOD", "description": "Dining out"},
    {"id": "RENT",    "name": "Rent & Housing",       "parent_category": None,   "description": "Monthly rent, mortgage"},
    {"id": "UTIL",    "name": "Utilities",            "parent_category": None,   "description": "Electricity, water, gas"},
    {"id": "TRANS",   "name": "Transportation",       "parent_category": None,   "description": "Gas, public transit, ride-share"},
    {"id": "ENTMT",   "name": "Entertainment",        "parent_category": None,   "description": "Movies, games, streaming"},
    {"id": "HEALTH",  "name": "Health & Fitness",     "parent_category": None,   "description": "Gym, pharmacy, doctors"},
    {"id": "SHOP",    "name": "Shopping",             "parent_category": None,   "description": "Clothing, electronics, general retail"},
    {"id": "TRAVEL",  "name": "Travel",               "parent_category": None,   "description": "Hotels, flights, vacation"},
    {"id": "SALARY",  "name": "Salary / Income",      "parent_category": None,   "description": "Payroll deposits"},
    {"id": "INVEST",  "name": "Investments",          "parent_category": None,   "description": "Stock purchases, savings transfers"},
    {"id": "MISC",    "name": "Miscellaneous",        "parent_category": None,   "description": "Uncategorised expenses"},
    {"id": "SUBSC",   "name": "Subscriptions",        "parent_category": "ENTMT","description": "Streaming, SaaS subscriptions"},
]

# Merchant name → category mapping
MERCHANT_TEMPLATES = [
    ("Walmart",         "GROC",  False),
    ("Whole Foods",     "GROC",  False),
    ("Kroger",          "GROC",  False),
    ("Costco",          "GROC",  False),
    ("Trader Joe's",    "GROC",  False),
    ("McDonald's",      "REST",  False),
    ("Starbucks",       "REST",  False),
    ("Chipotle",        "REST",  False),
    ("Subway",          "REST",  False),
    ("Pizza Hut",       "REST",  False),
    ("Shell Gas",       "TRANS", False),
    ("Uber",            "TRANS", True),
    ("Lyft",            "TRANS", True),
    ("Metro Transit",   "TRANS", False),
    ("Netflix",         "SUBSC", True),
    ("Spotify",         "SUBSC", True),
    ("Amazon Prime",    "SUBSC", True),
    ("Hulu",            "SUBSC", True),
    ("Apple Music",     "SUBSC", True),
    ("Gym Membership",  "HEALTH",False),
    ("CVS Pharmacy",    "HEALTH",False),
    ("Walgreens",       "HEALTH",False),
    ("Nike",            "SHOP",  False),
    ("Best Buy",        "SHOP",  False),
    ("ZARA",            "SHOP",  False),
    ("Airbnb",          "TRAVEL",True),
    ("Delta Airlines",  "TRAVEL",True),
    ("Expedia",         "TRAVEL",True),
    ("Electricity Co",  "UTIL",  False),
    ("Water Corp",      "UTIL",  False),
    ("Internet Co",     "UTIL",  False),
    ("Employer Inc",    "SALARY",False),
]

CATEGORY_RULES = [
    ("walmart|kroger|costco|whole foods|trader", "GROC"),
    ("mcdonald|starbucks|chipotle|subway|pizza", "REST"),
    ("shell|uber|lyft|metro|transit",            "TRANS"),
    ("netflix|spotify|amazon prime|hulu|apple music", "SUBSC"),
    ("gym|pharmacy|cvs|walgreens",               "HEALTH"),
    ("nike|best buy|zara",                       "SHOP"),
    ("airbnb|delta|expedia",                     "TRAVEL"),
    ("electricity|water|internet",               "UTIL"),
    ("employer|payroll|salary",                  "SALARY"),
]

TIMEZONES = ["UTC", "US/Eastern", "US/Pacific", "US/Central", "US/Mountain"]


# ─── ID generators ───────────────────────────────────────────

def usr_id(n: int) -> str:
    return f"USR-{n:06d}"

def acc_id(user_num: int, acc_num: int) -> str:
    return f"ACC-{user_num:06d}-{acc_num:02d}"

def txn_id(n: int) -> str:
    return f"TXN-{YEAR}-{n:08d}"

def bud_id(user_num: int, year: int, month: int, cat: str) -> str:
    return f"BUD-{user_num:06d}-{year}-{month:02d}-{cat}"

def rec_id(n: int) -> str:
    return f"REC-{n:06d}"


# ─── Main generation function ─────────────────────────────────

def run_full_generation(n_users: int = 1000, txns_per_user: int = 500, seed: int = SEED):
    """Generate all synthetic data and load into MySQL."""
    global fake
    Faker.seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    fake = Faker()

    db = SessionLocal()
    try:
        # Disable foreign key checks
        db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        db.commit()

        print("🔄 Clearing existing data (FK checks disabled)…")
        for tbl in [models.Insight, models.Budget, models.Transaction,
                    models.RecurringSeries, models.Account, models.Merchant,
                    models.CategoryRule, models.UserProfile, models.Category]:
            db.query(tbl).delete()
        db.commit()

        # Re-enable foreign key checks
        db.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        db.commit()

        print("📂 Seeding categories...")
        cats = _seed_categories(db)

        print("📂 Seeding category rules...")
        _seed_category_rules(db)

        print("🏪 Seeding merchants...")
        merchants = _seed_merchants(db)

        print("👤 Generating users & accounts...")
        users, accounts = _seed_users_and_accounts(db, n_users)

        print("🔄 Generating recurring series...")
        rec_series = _seed_recurring_series(db, accounts, merchants)

        print("💳 Generating transactions...")
        txn_df, ground_truth = _seed_transactions(
            db, users, accounts, merchants, rec_series, txns_per_user
        )

        print("📊 Generating budgets...")
        _seed_budgets(db, users, txn_df)

        print("💡 Generating insights...")
        _seed_insights(db, users, txn_df)

        print("💾 Exporting ground truth...")
        _export_ground_truth(ground_truth)

        print(f"✅ Done! {len(txn_df):,} transactions generated.")
    finally:
        db.close()


# ─── Seeders ─────────────────────────────────────────────────

def _seed_categories(db) -> List[models.Category]:
    # Insert parents first
    parents = [c for c in CATEGORIES if c["parent_category"] is None]
    children = [c for c in CATEGORIES if c["parent_category"] is not None]
    objs = []
    for c in parents + children:
        obj = models.Category(**c)
        db.add(obj)
        objs.append(obj)
    db.commit()
    return objs


def _seed_category_rules(db):
    for pattern, cat_id in CATEGORY_RULES:
        obj = models.CategoryRule(merchant_pattern=pattern, category_id=cat_id, priority=1)
        db.add(obj)
    db.commit()


def _seed_merchants(db) -> List[models.Merchant]:
    objs = []
    for name, cat_id, is_online in MERCHANT_TEMPLATES:
        city  = fake.city()
        state = fake.state_abbr()
        obj = models.Merchant(name=name, alias=name.lower().replace(" ", "_"),
                              category_id=cat_id, city=city, state=state,
                              country="US", is_online=is_online)
        db.add(obj)
        objs.append(obj)
    db.commit()
    for o in objs:
        db.refresh(o)
    return objs


def _seed_users_and_accounts(db, n_users: int):
    users, accounts = [], []
    for i in range(1, n_users + 1):
        uid = usr_id(i)
        profile = models.UserProfile(
            id=uid,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=f"user{i}@{fake.domain_name()}",
            phone=fake.phone_number()[:20],
            created_at=datetime(2025, 1, 1) + timedelta(days=random.randint(0, 180)),
            is_active=True,
        )
        db.add(profile)
        users.append(profile)

        # Each user gets 1-3 accounts
        n_accts = random.randint(1, 3)
        for j in range(1, n_accts + 1):
            acc_type = random.choice(list(models.AccountType))
            acc = models.Account(
                id=acc_id(i, j),
                user_id=uid,
                account_type=acc_type,
                balance=round(random.uniform(500, 50000), 2),
                currency="USD",
                opened_at=datetime(2025, 1, 1) + timedelta(days=random.randint(0, 90)),
                status=models.AccountStatus.ACTIVE,
            )
            db.add(acc)
            accounts.append(acc)
    db.commit()
    return users, accounts


def _seed_recurring_series(db, accounts, merchants):
    """Create salary, rent, and subscription recurring series per account."""
    series_list = []
    counter = 1
    # group merchants by category
    salary_merchants = [m for m in merchants if m.category_id == "SALARY"]
    rent_cat = "RENT"
    sub_merchants = [m for m in merchants if m.category_id == "SUBSC"]

    seen_accounts = set()
    for acc in accounts:
        if acc.id in seen_accounts:
            continue
        seen_accounts.add(acc.id)

        # Salary (monthly credit)
        salary_m = random.choice(salary_merchants) if salary_merchants else None
        salary_rs = models.RecurringSeries(
            id=rec_id(counter),
            account_id=acc.id,
            merchant_id=salary_m.id if salary_m else None,
            category_id="SALARY",
            frequency=models.Frequency.MONTHLY,
            amount=round(random.uniform(3000, 12000), 2),
            start_date=datetime(YEAR, 1, 1),
            day_of_month=random.randint(1, 5),
            is_active=True,
        )
        db.add(salary_rs)
        series_list.append(salary_rs)
        counter += 1

        # Rent (monthly debit)
        rent_rs = models.RecurringSeries(
            id=rec_id(counter),
            account_id=acc.id,
            merchant_id=None,
            category_id=rent_cat,
            frequency=models.Frequency.MONTHLY,
            amount=-round(random.uniform(800, 3500), 2),
            start_date=datetime(YEAR, 1, 1),
            day_of_month=1,
            is_active=True,
        )
        db.add(rent_rs)
        series_list.append(rent_rs)
        counter += 1

        # 1-3 subscriptions
        for sub_m in random.sample(sub_merchants, min(len(sub_merchants), random.randint(1, 3))):
            sub_rs = models.RecurringSeries(
                id=rec_id(counter),
                account_id=acc.id,
                merchant_id=sub_m.id,
                category_id="SUBSC",
                frequency=models.Frequency.MONTHLY,
                amount=-round(random.choice([9.99, 12.99, 14.99, 15.99, 17.99]), 2),
                start_date=datetime(YEAR, 1, 1),
                day_of_month=random.randint(5, 28),
                is_active=True,
            )
            db.add(sub_rs)
            series_list.append(sub_rs)
            counter += 1

    db.commit()
    for s in series_list:
        db.refresh(s)
    return series_list


def _seed_transactions(db, users, accounts, merchants, rec_series, txns_per_user: int):
    """Generate all transactions; return DataFrame and ground truth list."""
    spend_cats   = ["FOOD","GROC","REST","TRANS","ENTMT","HEALTH","SHOP","TRAVEL","UTIL","MISC","SUBSC"]
    merchant_by_cat: Dict[str, List[models.Merchant]] = {}
    for m in merchants:
        merchant_by_cat.setdefault(m.category_id, []).append(m)

    all_txns = []
    ground_truth = []
    txn_counter = 1
    account_map = {a.id: a for a in accounts}
    user_accounts: Dict[str, List[models.Account]] = {}
    for acc in accounts:
        user_accounts.setdefault(acc.user_id, []).append(acc)

    rec_by_account: Dict[str, List[models.RecurringSeries]] = {}
    for rs in rec_series:
        rec_by_account.setdefault(rs.account_id, []).append(rs)

    for user in users:
        u_accs = user_accounts.get(user.id, [])
        if not u_accs:
            continue
        primary_acc = u_accs[0]
        tz = random.choice(TIMEZONES)

        # --- Inject recurring transactions ---
        for rs in rec_by_account.get(primary_acc.id, []):
            for month in range(1, 13):
                # Edge case: skip one recurring payment randomly (~5% chance)
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

                day = rs.day_of_month or 1
                try:
                    txn_date = datetime(YEAR, month, min(day, 28))
                except ValueError:
                    txn_date = datetime(YEAR, month, 28)

                is_credit = rs.category_id == "SALARY"
                txn_type  = models.TransactionType.CREDIT if is_credit else models.TransactionType.DEBIT
                tid = txn_id(txn_counter)
                txn_counter += 1
                all_txns.append({
                    "id": tid,
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

        # --- Random spending transactions ---
        for _ in range(txns_per_user):
            cat_id = random.choice(spend_cats)
            cat_merchants = merchant_by_cat.get(cat_id, merchants)
            merchant = random.choice(cat_merchants)
            month = random.randint(1, 12)
            day   = random.randint(1, 28)
            txn_date = datetime(YEAR, month, day,
                                random.randint(0, 23), random.randint(0, 59))

            amount = -abs(round(np.random.lognormal(mean=3.5, sigma=1.0), 2))
            txn_type = models.TransactionType.DEBIT
            is_anomaly = False
            gt_label   = None

            # Edge case 1: Transfer counted as spending (5% of non-salary txns)
            if random.random() < 0.05:
                txn_type   = models.TransactionType.TRANSFER
                is_anomaly = True
                gt_label   = "TRANSFER_AS_SPEND"
                ground_truth.append({
                    "issue_type":   "transfer_double",
                    "txn_id":       txn_id(txn_counter),
                    "account_id":   primary_acc.id,
                    "amount":       amount,
                    "txn_date":     str(txn_date),
                    "ground_truth_label": gt_label,
                })

            # Edge case 2: Refund treated as new expense (3%)
            elif random.random() < 0.03:
                txn_type   = models.TransactionType.REFUND
                amount     = abs(amount)   # positive = income, but mis-labelled
                is_anomaly = True
                gt_label   = "REFUND_AS_EXPENSE"
                ground_truth.append({
                    "issue_type":   "refund_detected",
                    "txn_id":       txn_id(txn_counter),
                    "account_id":   primary_acc.id,
                    "amount":       amount,
                    "txn_date":     str(txn_date),
                    "ground_truth_label": gt_label,
                })

            # Edge case 3: Timezone boundary (1%)
            elif random.random() < 0.01:
                txn_date   = datetime(YEAR, month, day, 23, 58)
                tz         = "US/Pacific"
                is_anomaly = True
                gt_label   = "TZ_BOUNDARY"
                ground_truth.append({
                    "issue_type":   "timezone_boundary",
                    "txn_id":       txn_id(txn_counter),
                    "account_id":   primary_acc.id,
                    "txn_date":     str(txn_date),
                    "timezone":     tz,
                    "ground_truth_label": gt_label,
                })

            # Edge case 4: Budget category mismatch (2%)
            elif random.random() < 0.02:
                cat_id     = random.choice(["MISC", "SHOP"])
                is_anomaly = True
                gt_label   = "BUDGET_MISMATCH"
                ground_truth.append({
                    "issue_type":   "budget_mismatch",
                    "txn_id":       txn_id(txn_counter),
                    "account_id":   primary_acc.id,
                    "category_id":  cat_id,
                    "ground_truth_label": gt_label,
                })

            tid = txn_id(txn_counter)
            txn_counter += 1
            all_txns.append({
                "id":          tid,
                "account_id":  primary_acc.id,
                "merchant_id": merchant.id,
                "category_id": cat_id,
                "recurring_series_id": None,
                "amount":      amount,
                "txn_type":    txn_type.value,
                "status":      "cleared",
                "description": f"{merchant.name} purchase",
                "txn_date":    txn_date,
                "posted_date": txn_date + timedelta(days=random.randint(0, 2)),
                "is_recurring": False,
                "timezone":    tz,
                "is_anomaly":  is_anomaly,
                "ground_truth_label": gt_label,
            })

    # Bulk insert in chunks of 5,000
    df = pd.DataFrame(all_txns)
    chunk_size = 5000
    for start in range(0, len(all_txns), chunk_size):
        chunk = all_txns[start:start + chunk_size]
        db.bulk_insert_mappings(models.Transaction, chunk)
        db.commit()

    return df, ground_truth


def _seed_budgets(db, users, txn_df: pd.DataFrame):
    """Create monthly budgets per user per spend category."""
    spend_cats = ["FOOD","GROC","REST","TRANS","ENTMT","HEALTH","SHOP","UTIL","MISC","SUBSC"]
    for i, user in enumerate(users, 1):
        for month in range(1, 13):
            for cat_id in spend_cats:
                bid = bud_id(i, YEAR, month, cat_id)
                budgeted = round(random.uniform(100, 1500), 2)
                # Calculate actual spending from df
                user_accs = [f"ACC-{i:06d}-{j:02d}" for j in range(1, 4)]
                spent_df = txn_df[
                    (txn_df["account_id"].isin(user_accs)) &
                    (txn_df["category_id"] == cat_id) &
                    (pd.to_datetime(txn_df["txn_date"]).dt.month == month) &
                    (txn_df["txn_type"] == "debit")
                ]
                spent = abs(float(spent_df["amount"].sum()))
                if spent > budgeted:
                    status = models.BudgetStatus.OVER_BUDGET
                elif spent < budgeted * 0.5:
                    status = models.BudgetStatus.UNDER_BUDGET
                else:
                    status = models.BudgetStatus.ON_TRACK

                obj = models.Budget(
                    id=bid,
                    user_id=user.id,
                    category_id=cat_id,
                    period_month=month,
                    period_year=YEAR,
                    amount_budgeted=budgeted,
                    amount_spent=round(spent, 2),
                    status=status,
                )
                db.add(obj)
        # Commit per user to avoid huge transactions
        db.commit()


def _seed_insights(db, users, txn_df: pd.DataFrame):
    """Create insights for over-budget, anomalies, and missed recurrings."""
    anomaly_df = txn_df[txn_df["is_anomaly"] == True]
    for _, row in anomaly_df.head(500).iterrows():    # cap at 500 insights
        acc_id_val = row["account_id"]
        # derive user number from account id e.g. ACC-000001-01 → USR-000001
        try:
            parts = acc_id_val.split("-")
            user_num = int(parts[1])
            uid = usr_id(user_num)
        except Exception:
            continue
        label = row.get("ground_truth_label") or "ANOMALY"
        itype_map = {
            "TRANSFER_AS_SPEND": models.InsightType.TRANSFER_DOUBLE,
            "REFUND_AS_EXPENSE":  models.InsightType.REFUND_DETECTED,
            "TZ_BOUNDARY":        models.InsightType.UNUSUAL_SPEND,
            "BUDGET_MISMATCH":    models.InsightType.BUDGET_MISMATCH,
        }
        itype = itype_map.get(label, models.InsightType.UNUSUAL_SPEND)
        obj = models.Insight(
            user_id=uid,
            category_id=row.get("category_id"),
            insight_type=itype,
            description=f"Anomaly detected: {label} on txn {row['id']}",
            severity=models.Severity.HIGH if label == "TRANSFER_AS_SPEND" else models.Severity.MEDIUM,
            created_at=row["txn_date"] if isinstance(row["txn_date"], datetime) else datetime.utcnow(),
        )
        db.add(obj)
    db.commit()


def _export_ground_truth(ground_truth: list):
    """Export ground truth to CSV and JSON for evaluation."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.DataFrame(ground_truth)
    csv_path  = os.path.join(OUTPUT_DIR, "ground_truth.csv")
    json_path = os.path.join(OUTPUT_DIR, "ground_truth.json")
    df.to_csv(csv_path, index=False)
    with open(json_path, "w") as f:
        json.dump(ground_truth, f, indent=2, default=str)
    print(f"   Ground truth saved → {csv_path}")
    print(f"   Ground truth saved → {json_path}")
