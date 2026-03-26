from fastapi import APIRouter, HTTPException
from ..state import state
from ..core.evaluator import compute_metrics, compute_baseline_metrics

router = APIRouter()


@router.get("/metrics")
def get_metrics(include_baseline: bool = True):
    """
    Returns all evaluation metrics for the current allocation.
    Optionally includes baseline (random allocation) comparison.
    """
    if not state.allocation_done:
        raise HTTPException(status_code=404, detail="No allocation computed yet.")

    metrics = compute_metrics(state.students, state.sections)

    if include_baseline:
        baseline = compute_baseline_metrics(state.students)
        metrics.update(baseline)

    return metrics
