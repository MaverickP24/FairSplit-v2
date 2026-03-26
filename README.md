# FairSplit

A system that divides university students into balanced sections while maximising
friend co-placement. Built with FastAPI (Python) + React (Vite).

---

## The Problem It Solves

Universities typically split students into sections purely by rank (CGPA). This
ensures academic fairness but completely ignores social structure — students end
up with zero friends in their section, hurting collaboration and mental wellbeing.

FairSplit solves both at once:
- **Academic fairness**: every section gets exactly equal total rank points
- **Social structure**: friend preferences are satisfied wherever constraints allow
- **Transparency**: full metrics show exactly how much better the result is vs random

---

## How the Algorithm Works

### Step 1 — Rank & Tier assignment (ranker.py)

Students are sorted by CGPA (descending). Ties broken by enrollment number (ascending)
for full determinism. Then assigned rank points in tiers of 5:

| Tier | Ranks  | Rank points |
|------|--------|-------------|
| 1    | 1–5    | 100         |
| 2    | 6–10   | 95          |
| 3    | 11–15  | 90          |
| ...  | ...    | ...         |
| 115  | 571–575| 5           |
| partial | 576 | 0           |

Points floor at 5 for full tiers. If total students isn't divisible by 5,
the partial last tier students get **0 points** — this is the only way to keep
section rank point totals exactly equal when section sizes differ by ±1.

### Step 2 — Snake-draft allocation (allocator.py)

Students are distributed into 5 sections using a snake-draft over tiers:

```
Tier 1:  S1 ← rank1,  S2 ← rank2,  S3 ← rank3,  S4 ← rank4,  S5 ← rank5
Tier 2:  S5 ← rank6,  S4 ← rank7,  S3 ← rank8,  S2 ← rank9,  S1 ← rank10
Tier 3:  S1 ← rank11, S2 ← rank12, ...
```

Direction alternates each tier (snake pattern). This guarantees:
- Every tier of 5 has **exactly one student per section** (hard constraint)
- Section rank point totals are **perfectly equal**
- Result is **fully deterministic** — same input always gives same output

### Step 3 — Friendship optimisation (optimizer.py)

After the snake-draft, the optimizer tries to co-place preferred friends.

For every mutual-preference pair (sorted by combined weight, highest first):
1. Check if they're already in the same section — skip if yes
2. Try to swap one of them with a same-tier student from the other's section
3. Before accepting: verify ALL hard constraints still hold
4. Accept only if valid; move on otherwise

**A swap is only legal if:**
- Both students being swapped are from the **same tier** (guarantees rank points stay equal)
- The destination section doesn't already have someone from that tier
- Section sizes remain within ±1

This means friendship optimisation **can never break academic fairness**.

### Metrics (evaluator.py)

After allocation, the system computes:

| Metric | What it measures |
|--------|-----------------|
| Satisfaction score | Weighted % of preferred friends co-placed (priority 1 = weight 10, priority 10 = weight 1) |
| Isolation rate | % of students with 0 preferred friends in their section |
| At-least-1 friend rate | % of students with ≥1 preferred friend |
| Avg friends/student | Average count of co-placed preferred friends |
| Balance score | Max rank point delta across sections (0 = perfect) |

All metrics are also computed for a random baseline (10 runs averaged) so you
can see exactly how much better FairSplit is vs pure random assignment.

---

## Project Structure

```
fairsplit/
│
├── README.md                     ← You are here
├── test_algorithm.py             ← Run this to verify everything works
│
├── backend/
│   ├── main.py                   ← FastAPI app, CORS, route registration
│   ├── state.py                  ← In-memory store (students, sections, results)
│   ├── requirements.txt          ← Python dependencies
│   │
│   ├── models/
│   │   ├── student.py            ← Student dataclass (rank, tier, pts, prefs, section)
│   │   └── section.py            ← Section dataclass (members, tier_set, rank pts)
│   │
│   ├── core/
│   │   ├── ranker.py             ← CGPA sort → rank → tier → rank_points
│   │   ├── allocator.py          ← Snake-draft (guarantees one-per-tier-per-section)
│   │   ├── optimizer.py          ← Friendship pass (constraint-safe swaps only)
│   │   └── evaluator.py          ← All metrics + baseline comparison
│   │
│   ├── utils/
│   │   ├── dummy_generator.py    ← Generate N fake students for development
│   │   ├── pdf_parser.py         ← pdfplumber-based SGPA extractor (plug in later)
│   │   └── excel_parser.py       ← openpyxl name+enrollment reader
│   │
│   └── api/
│       ├── dummy.py              ← POST /api/dummy  (dev data loader)
│       ├── ingest.py             ← POST /api/ingest (PDF + Excel upload)
│       ├── survey.py             ← POST /api/survey (preference submission)
│       ├── allocate.py           ← POST /api/allocate (run algorithm)
│       └── metrics.py            ← GET  /api/metrics
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx              ← React entry point
        ├── App.jsx               ← Navigation shell
        ├── api/
        │   └── client.js         ← All API calls in one place
        └── pages/
            ├── RankDashboard.jsx ← Upload files, view ranked student table
            ├── SurveyPage.jsx    ← Students enter friend preferences
            ├── SimulationPage.jsx← Run allocation, inspect section assignments
            └── MetricsDashboard.jsx ← Satisfaction / isolation / balance charts
```

---

## Setup & Running

### Requirements

- Python 3.10+
- Node.js 18+

### Backend

```bash
cd fairsplit/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API runs at: http://localhost:8000
Interactive API docs: http://localhost:8000/docs

### Frontend

```bash
cd fairsplit/frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/dummy?n=576&seed=42 | Load dummy students (dev mode) |
| POST | /api/ingest | Upload PDF + Excel files |
| GET  | /api/students | Get all ranked students |
| POST | /api/survey | Submit friend preferences |
| GET  | /api/survey/status | How many students have submitted |
| POST | /api/allocate | Run the allocation algorithm |
| GET  | /api/allocation | Get last computed allocation |
| GET  | /api/metrics | Get all evaluation metrics |

---

## Workflow

### Development (no real data yet)

1. Start the backend
2. Hit `POST /api/dummy` to load 576 fake students instantly
3. Open the frontend → Rank Dashboard shows all students
4. Go to Survey → submit some friend preferences
5. Go to Simulation → run allocation
6. Go to Metrics → see satisfaction and balance scores

### Production (real university data)

1. Upload result PDF + student names Excel via Rank Dashboard
2. Share the Survey page URL with students (they enter their own enrollment number)
3. After survey period closes, run allocation from Simulation page
4. Review Metrics Dashboard
5. Export section lists

---

## Running the Algorithm Test Suite

```bash
cd fairsplit
python test_algorithm.py
```

This runs 8 tests on 576 dummy students and verifies:
1. Determinism — two runs give identical results
2. All students placed exactly once
3. One student per tier per section (hard constraint)
4. Section sizes within ±1
5. Rank points perfectly equal across all sections
6. Friendship pass preserves all hard constraints after optimisation
7. Metrics compute correctly
8. Tier/rank-point spot check (prints first 15 students)

All 8 must pass. If any fail, do not deploy.

---

## Key Design Decisions

**Why snake-draft instead of greedy assignment?**
Greedy (fill S1 first, then S2...) creates a top-heavy S1. Snake-draft is the
only O(n) method that guarantees equal rank point totals from the start.

**Why same-tier-only swaps in the friendship pass?**
Students in the same tier have identical rank points. Swapping them is the only
way to move students between sections without changing any section's total rank
points. Cross-tier swaps would always create an imbalance.

**Why 0 points for the partial tier?**
576 ÷ 5 = 115 remainder 1. The 576th student must go into one section, making it
116 students while others have 115. If that student had 5 rank points, one section
would total 5 more points than the others — making perfect balance impossible.
Assigning 0 points to partial-tier students keeps all totals equal.

**Why not use a proper ILP solver?**
For 576 students, 5 sections, and 10 preferences each, a solver like PuLP or
scipy would work but adds a dependency and obscures the logic. The snake-draft +
greedy friendship pass runs in milliseconds, is fully transparent, and produces
results that are provably optimal on the hard constraints.

---

## Adding Real PDF Support Later

When you have your university's PDF:

1. Run `python debug_pdf.py your_result.pdf` to inspect what pdfplumber extracts
2. Tune the column detection in `backend/utils/pdf_parser.py`:
   - `ENROLLMENT_PATTERN` — regex for your enrollment number format
   - `_extract_from_tables()` — adjust which column holds SGPA
   - `_extract_from_text()` — fallback regex if tables don't work
3. Test with `python -c "from backend.utils.pdf_parser import parse_pdf; print(parse_pdf('your.pdf')[:5])"`

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI | Async, auto-docs, Pydantic validation |
| Algorithm | Pure Python | No solver dependency, fully transparent |
| PDF parsing | pdfplumber | Best table extraction for university PDFs |
| Excel | openpyxl | Zero-dependency xlsx reading |
| Frontend | React + Vite | Fast dev server, no config overhead |
| State | In-memory | Simple for now; swap for Redis/DB in prod |



---

## Frontend — What's on each page

### Rank Dashboard
- Upload PDF + Excel **or** click "Load 576 dummy students" (dev mode)
- Live sortable table — click any column header to sort
- Search by name or enrollment number
- Paginated (50 per page) for 576+ students
- Section badges appear after allocation is run
- **Export CSV** button downloads the full ranked list

### Survey Page
- Live submission counter (how many students have submitted)
- Student verifies identity with enrollment number
- **Search friends by name** — type a name, pick from dropdown (no need to memorise enrollment numbers)
- Rank shown next to each friend in the dropdown
- Up to 10 preferences with priority 1–10
- Confirmation screen after submission

### Simulation Page
- Mode toggle: **Strict** (same hard guarantees, minimal friend swaps) vs **Balanced** (maximise friend co-placement)
- Optimizer stats: swaps made, pairs evaluated, already-together count
- Rank balance bar chart — confirms all sections equal
- Expandable section cards — click any section to see all members
- **Export CSV** downloads all sections in one file (sorted by rank within each section)

### Metrics Dashboard
- 4 headline stats with descriptions
- Side-by-side comparison bars: FairSplit vs random baseline (10-run average)
- Rank point balance bar chart per section
- Section size cards

### Navigation bar
- Green dot on each nav item when that step is complete
- Progress hint in top-right: ✓ Data → ✓ Survey → ✓ Allocated

