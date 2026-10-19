# Quiz Performance Analytics System

> **CSE494 – Intelligent NoSQL Databases** | Lovely Professional University

A MongoDB + PyMongo analytics system that stores quiz data (students, questions, attempts) and uses aggregation pipelines to produce insights: topic-wise accuracy, leaderboards, score trends, difficulty analysis, and personalized student dashboards.

---

## Features

- **3 collections** with `$jsonSchema` validation (strict mode)
- **Full CRUD operations** with error handling (`$set`, `$inc`, `$addToSet`, `$push`, `upsert`, `arrayFilters`, transactions)
- **8 aggregation pipelines**: topic accuracy, leaderboard, time analysis, monthly trends, weakest topics, hardest questions, score distribution, student dashboard (`$facet`)
- **Bonus pipelines**: Pass/Fail labeling (`$addFields` + `$cond`), student rankings (`$setWindowFields` + `$rank`)
- **Strategic indexes** with `explain()` verification (IXSCAN vs COLLSCAN)
- **Realistic seed data**: 30 students, 60 real technical MCQs, 300 attempts with hidden strength profiles
- **Menu-driven CLI** and **non-interactive demo script** with saved outputs
- **Equivalent mongosh queries** for every operation

---

## Folder Structure

```
quiz-analytics/
├── README.md               ← You are here
├── requirements.txt         ← Python dependencies
├── .env.example             ← Environment variables template
├── .env                     ← Your actual connection settings
├── config.py                ← MongoDB connection and configuration
├── schema.py                ← Collection creation, validators, indexes
├── seed_data.py             ← Data generation and insertion
├── crud_operations.py       ← All CRUD functions
├── aggregations.py          ← All aggregation pipelines
├── main.py                  ← Interactive menu-driven CLI
├── demo_run.py              ← Non-interactive demo (run for report)
├── mongo_shell_queries.js   ← mongosh equivalents for viva/report
├── outputs/                 ← Demo outputs saved here (auto-created)
├── report/
│   ├── REPORT.md            ← Project report draft
│   └── VIVA_NOTES.md        ← Viva preparation cheat sheet
└── tests/
    └── test_validation.py   ← Validation rule tests
```

---

## Prerequisites

1. **Python 3.10+** — [Download](https://www.python.org/downloads/)
2. **MongoDB 7.0+** — Choose one:
   - **Local install**: [MongoDB Community Edition](https://www.mongodb.com/try/download/community)
   - **Cloud (Atlas)**: [MongoDB Atlas Free Tier](https://cloud.mongodb.com)

---

## Step-by-Step Setup

### 1. Clone/Download the Project

```bash
cd "Quiz Performance Analytics System"
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB Connection

Copy the example and edit if needed:

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

**For local MongoDB** (default — no changes needed):
```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=quiz_analytics
```

**For MongoDB Atlas** (free tier):
1. Go to [cloud.mongodb.com](https://cloud.mongodb.com)
2. Create a free M0 cluster
3. Create a database user (Database Access → Add New Database User)
4. Whitelist your IP (Network Access → Add IP Address → Allow Access from Anywhere)
5. Get the connection string (Connect → Connect your application → Python)
6. Update `.env`:
```env
MONGO_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=quiz_analytics
```

### 5. Start MongoDB (Local Only)

```bash
# Windows (if installed as a service)
net start MongoDB

# Or run mongod directly
"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe"
```

### 6. Test Connection

```bash
python config.py
```

You should see: `[OK] Connected to MongoDB at mongodb://localhost:27017`

---

## How to Run

### Option A: Full Demo (Non-Interactive) — For Report Screenshots

```bash
python demo_run.py
```

This runs everything automatically and saves outputs to the `outputs/` folder.

### Option B: Interactive CLI

```bash
python main.py
```

Navigate through the menu to explore individual operations.

### Option C: Individual Modules

```bash
python schema.py --reset    # Reset and recreate collections
python seed_data.py          # Generate and insert sample data
python crud_operations.py    # Run CRUD demo
python aggregations.py       # Run all aggregation pipelines
```

---

## How to Run Tests

```bash
python tests/test_validation.py
```

Expected: 6 invalid documents rejected (PASS), 1 valid document accepted (PASS).

---

## Quick Start (3 Commands)

```bash
pip install -r requirements.txt
python config.py              # Verify MongoDB connection
python demo_run.py            # Run the complete demo
```

---

## Troubleshooting

### "Connection refused" / Cannot connect to MongoDB

- **Cause:** MongoDB server is not running
- **Fix (Local):** Start MongoDB: `net start MongoDB` or run `mongod.exe`
- **Fix (Atlas):** Check your connection string in `.env`, ensure IP is whitelisted

### DuplicateKeyError on re-seed

- **Cause:** Running `seed_data.py` without resetting first
- **Fix:** Use `python schema.py --reset` first, then seed, or use `python demo_run.py` which resets automatically

### "Transactions require a replica set"

- **Cause:** Multi-document transactions don't work on standalone MongoDB
- **Fix:** This is expected behavior. The code falls back to sequential deletes on standalone. For full transaction support, either:
  - Use MongoDB Atlas (always a replica set)
  - Convert local MongoDB to a replica set:
    ```bash
    mongod --replSet rs0
    # Then in mongosh:
    rs.initiate()
    ```

### WriteError on insert

- **Cause:** Document doesn't match the `$jsonSchema` validation rules
- **Fix:** Check the error message — it tells you which field failed validation

### ModuleNotFoundError

- **Cause:** Dependencies not installed or not in virtual environment
- **Fix:** `pip install -r requirements.txt` (make sure venv is activated)

---

## MongoDB Shell (mongosh)

To run the equivalent queries in mongosh:

```bash
mongosh
use quiz_analytics
load("mongo_shell_queries.js")
```

Or copy individual queries from `mongo_shell_queries.js` into MongoDB Compass for visualization.

---

## Project Report

See `report/REPORT.md` for the full project report. After running `demo_run.py`, replace the `[Insert screenshot]` placeholders with actual screenshots from the `outputs/` folder.

**Remember to fill in:**
- Your name
- Your registration number

---

## License

Academic project for CSE494. Not intended for production use.
