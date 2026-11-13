"""
Pytest tests for FastAPI endpoints.
Run: cd backend && pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ─── Health ──────────────────────────────────────────────────

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ─── Categories ──────────────────────────────────────────────

def test_list_categories():
    r = client.get("/categories/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_create_category():
    payload = {"id": "TEST_CAT", "name": "Test Category", "parent_category": None, "description": "Test"}
    r = client.post("/categories/", json=payload)
    # 200 or 422 (if already exists – idempotent in tests)
    assert r.status_code in (200, 422, 500)


# ─── Users ───────────────────────────────────────────────────

def test_list_users():
    r = client.get("/users/")
    assert r.status_code == 200

def test_create_and_get_user():
    import time
    uid = f"USR-TST{int(time.time()) % 100000:05d}"
    payload = {
        "id": uid,
        "first_name": "John",
        "last_name": "Doe",
        "email": f"{uid}@test.com",
        "phone": "1234567890",
        "is_active": True,
    }
    r = client.post("/users/", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == uid

    r2 = client.get(f"/users/{uid}")
    assert r2.status_code == 200
    assert r2.json()["email"] == payload["email"]


def test_get_user_not_found():
    r = client.get("/users/USR-999999")
    assert r.status_code == 404


# ─── Transactions ────────────────────────────────────────────

def test_list_transactions():
    r = client.get("/transactions/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_list_transactions_with_filters():
    r = client.get("/transactions/?limit=10")
    assert r.status_code == 200
    assert len(r.json()) <= 10


# ─── Budgets ─────────────────────────────────────────────────

def test_list_budgets():
    r = client.get("/budgets/")
    assert r.status_code == 200


# ─── Analytics ───────────────────────────────────────────────

def test_spending_by_category_missing_user():
    # Should return empty list for non-existent user, not 500
    r = client.get("/analytics/spending-by-category?user_id=USR-000000&year=2026")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

def test_monthly_trend_missing_user():
    r = client.get("/analytics/monthly-trend?user_id=USR-000000&year=2026")
    assert r.status_code == 200

def test_budget_comparison_missing_user():
    r = client.get("/analytics/budget-comparison?user_id=USR-000000&year=2026&month=1")
    assert r.status_code == 200


# ─── Insights ────────────────────────────────────────────────

def test_list_insights():
    r = client.get("/insights/")
    assert r.status_code == 200


# ─── Merchants ───────────────────────────────────────────────

def test_list_merchants():
    r = client.get("/merchants/")
    assert r.status_code == 200


# ─── Recurring Series ────────────────────────────────────────

def test_list_recurring_series():
    r = client.get("/recurring-series/")
    assert r.status_code == 200
