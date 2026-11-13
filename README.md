# YottaFlex Hackathon – Full Project

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React.js + Vite |
| Styling | Tailwind CSS |
| Charts | Recharts |
| Backend | Python + FastAPI |
| Data Processing | Pandas + NumPy |
| Synthetic Data | Faker (seed=20261022) |
| Database | MySQL 8.0+ |
| ORM | SQLAlchemy |
| Testing | Pytest + Postman |
| Repository | GitHub |

---

## Project Structure
```
C:\CandidateWorkspace\
│
├─ backend\
│   ├─ app\
│   │   ├─ __init__.py
│   │   ├─ main.py           # FastAPI app + all routes
│   │   ├─ models.py         # 9 SQLAlchemy ORM models
│   │   ├─ schemas.py        # Pydantic schemas
│   │   ├─ crud.py           # CRUD + analytics queries
│   │   ├─ database.py       # MySQL engine + session
│   │   └─ utils\
│   │       ├─ data_generator.py  # 1,000 users / 500K txns generator
│   │       └─ validator.py       # Data integrity validation
│   ├─ tests\
│   │   └─ test_api.py
│   └─ requirements.txt
│
├─ frontend\
│   ├─ src\
│   │   ├─ main.jsx
│   │   ├─ App.jsx           # Full dashboard (charts, budgets, insights)
│   │   ├─ index.css
│   │   └─ services\
│   │       └─ api.js        # Axios API service
│   ├─ index.html
│   ├─ package.json
│   ├─ vite.config.js
│   ├─ tailwind.config.js
│   └─ postcss.config.js
│
├─ db\
│   ├─ schema.sql            # Full MySQL schema (all 9 tables)
│   └─ exports\              # Ground truth CSV/JSON (after generation)
│       ├─ ground_truth.csv
│       └─ ground_truth.json
│
├─ .gitignore
└─ README.md
```

---

## Core Entities
1. **UserProfile** – `USR-000001`
2. **Account** – `ACC-000001-01`
3. **Merchant** – auto-increment ID
4. **Transaction** – `TXN-2026-00000001`
5. **Category** – `FOOD`, `RENT`, `SUBSC`, etc.
6. **CategoryRule** – keyword-based categorisation rules
7. **Budget** – `BUD-000001-2026-01-FOOD`
8. **RecurringSeries** – `REC-000001`
9. **Insight** – auto-increment ID

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- MySQL 8.0+ running locally

### Step 1 – Create MySQL Database
```sql
CREATE DATABASE hackathon_db CHARACTER SET utf8mb4;
```
Then run `db/schema.sql`:
```bash
mysql -u root -p hackathon_db < db/schema.sql
```

### Step 2 – Backend
```powershell
cd C:\CandidateWorkspace\backend

# (Optional) Virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure DB credentials (edit database.py OR set env vars)
$env:DB_USER="root"
$env:DB_PASSWORD="your_password"
$env:DB_NAME="hackathon_db"

# Start API
uvicorn app.main:app --reload --port 8000
```
API docs: http://127.0.0.1:8000/docs

### Step 3 – Generate Synthetic Data
Via API (browser or curl):
```
POST http://127.0.0.1:8000/generate-data?users=1000&transactions_per_user=500&seed=20261022
```
Or via Python directly:
```powershell
python -c "from app.utils.data_generator import run_full_generation; run_full_generation(1000, 500)"
```

### Step 4 – Frontend
```powershell
cd C:\CandidateWorkspace\frontend
npm install
npm run dev
```
Open http://localhost:5173

### Step 5 – Run Tests
```powershell
cd C:\CandidateWorkspace\backend
pytest tests/ -v
```

---

## Edge Cases Handled
| Edge Case | Ground Truth Label |
|-----------|--------------------|
| Transfer counted as spending | `TRANSFER_AS_SPEND` |
| Refund treated as new expense | `REFUND_AS_EXPENSE` |
| Recurring series skipped | `RECURRING_SKIP` |
| Transaction crosses timezone boundary | `TZ_BOUNDARY` |
| Budget category mismatch | `BUDGET_MISMATCH` |

Ground truth exported to `db/exports/ground_truth.csv` and `.json`.

---

## API Endpoints (Summary)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/categories/` | List all categories |
| GET | `/users/` | List users |
| GET | `/accounts/` | List accounts |
| GET | `/merchants/` | List merchants |
| GET | `/transactions/` | List transactions (filterable) |
| GET | `/budgets/` | List budgets |
| GET | `/insights/` | List insights |
| GET | `/recurring-series/` | List recurring payments |
| GET | `/analytics/spending-by-category` | Spending per category |
| GET | `/analytics/monthly-trend` | Income vs spending trend |
| GET | `/analytics/budget-comparison` | Budget vs actual |
| POST | `/generate-data` | Trigger synthetic data generation |

Full interactive docs at: http://127.0.0.1:8000/docs
