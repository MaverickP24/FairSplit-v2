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
    """Generate n dummy students with random CGPAs for dev/testing."""
    state.reset()
    ranked = assign_ranks(generate_dummy_students(n=n, seed=seed))
    state.students = ranked

    return {
        "message": f"Loaded {n} dummy students (seed={seed})",
        "total_students": len(ranked),
        "tiers": ranked[-1].tier,
        "sections_target": 5,
        "size_per_section": f"{n // 5} or {n // 5 + 1}",
        "preview": [s.to_dict() for s in ranked[:5]],
    }
