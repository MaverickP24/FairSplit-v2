from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
from ..state import state
from ..core.allocator import snake_draft
from ..core.optimizer import run_friendship_pass

router = APIRouter()


class AllocateRequest(BaseModel):
    mode: Literal["strict", "balanced"] = "balanced"


@router.post("/allocate")
def run_allocation(request: AllocateRequest = AllocateRequest()):
    """Snake-draft → friendship optimization. Deterministic for same input."""
    if not state.students:
        raise HTTPException(status_code=404, detail="No student data loaded. Call /api/ingest first.")

    sections = snake_draft(state.students)
    opt_stats = run_friendship_pass(state.students, sections, mode=request.mode)

    state.sections = sections
    state.allocation_done = True
    state.optimizer_stats = opt_stats

    return {
        "mode": request.mode,
        "optimizer_stats": opt_stats,
        "sections": [s.to_dict() for s in sections],
        "rank_point_totals": {s.name: round(s.total_rank_points, 2) for s in sections},
        "section_sizes": {s.name: s.size for s in sections},
    }


@router.get("/allocation")
def get_allocation():
    if not state.allocation_done:
        raise HTTPException(status_code=404, detail="No allocation computed yet.")
    return {
        "sections": [s.to_dict() for s in state.sections],
        "rank_point_totals": {s.name: round(s.total_rank_points, 2) for s in state.sections},
        "section_sizes": {s.name: s.size for s in state.sections},
        "optimizer_stats": state.optimizer_stats,
    }
