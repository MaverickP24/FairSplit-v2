"""
POST /api/dummy
--------------
Generates N dummy students, ranks them, and loads them into app state.
Replaces the ingest pipeline during development.

Query params:
  n    : number of students (default 576, max 2000)
  seed : random seed for reproducibility (default 42)
"""
from fastapi import APIRouter, Query
from ..state import state
from ..utils.dummy_generator import generate_dummy_students
from ..core.ranker import assign_ranks

router = APIRouter()


@router.post("/dummy")
def load_dummy_data(
    n: int = Query(default=576, ge=5, le=2000),
    seed: int = Query(default=42),
):
    """
    Generate dummy students and load into state.
    Resets any existing data including preferences and allocation.
    """
    state.reset()

    raw = generate_dummy_students(n=n, seed=seed)
    ranked = assign_ranks(raw)
    state.students = ranked

    # Tier stats for response
    tier_count = ranked[-1].tier
    pts_sample = {
        "tier_1_pts": ranked[0].rank_points,
        "tier_2_pts": ranked[5].rank_points if len(ranked) > 5 else None,
        "last_full_tier_pts": next(
            (s.rank_points for s in reversed(ranked) if s.rank_points > 0), 0
        ),
        "partial_tier_pts": ranked[-1].rank_points if n % 5 != 0 else "N/A",
    }

    return {
        "message": f"Loaded {n} dummy students (seed={seed})",
        "total_students": len(ranked),
        "tiers": tier_count,
        "sections_target": 5,
        "size_per_section": f"{n // 5} or {n // 5 + 1}",
        "rank_points_sample": pts_sample,
        "preview": [s.to_dict() for s in ranked[:5]],
    }
