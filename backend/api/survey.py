from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Dict
from ..state import state

router = APIRouter()


class SurveySubmission(BaseModel):
    enrollment: str
    preferences: Dict[str, int]  # {enrollment: priority(1-10)}

    @field_validator("preferences")
    @classmethod
    def validate_preferences(cls, v):
        if len(v) > 10:
            raise ValueError("Maximum 10 preferences allowed")
        for enr, priority in v.items():
            if not (1 <= priority <= 10):
                raise ValueError(f"Priority for {enr} must be between 1 and 10")
        priorities = list(v.values())
        if len(priorities) != len(set(priorities)):
            seen = {}
            for enr, p in v.items():
                if p in seen:
                    raise ValueError(f"Duplicate priority {p}: used by both {seen[p]} and {enr}")
                seen[p] = enr
        return v


@router.post("/survey")
def submit_survey(submission: SurveySubmission):
    if not state.students:
        raise HTTPException(status_code=404, detail="No student data loaded yet")

    student_map = state.student_map()
    student = student_map.get(submission.enrollment)
    if student is None:
        raise HTTPException(status_code=404, detail=f"Enrollment {submission.enrollment} not found")

    invalid = [e for e in submission.preferences if e not in student_map]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Unknown enrollments: {invalid}")

    student.preferences = {e: p for e, p in submission.preferences.items() if e != submission.enrollment}

    return {
        "message": "Preferences saved",
        "enrollment": submission.enrollment,
        "preferences_count": len(student.preferences),
    }


@router.get("/survey/status")
def survey_status():
    if not state.students:
        raise HTTPException(status_code=404, detail="No data loaded")
    submitted = sum(1 for s in state.students if s.preferences)
    return {
        "total_students": len(state.students),
        "submitted": submitted,
        "pending": len(state.students) - submitted,
    }


@router.post("/survey/random")
def generate_random_surveys(seed: int = 42, pref_count: int = 10, submit_rate: float = 0.85):
    """Auto-generate random preferences for testing. ~85% of students submit up to 10 friends."""
    if not state.students:
        raise HTTPException(status_code=404, detail="No student data loaded yet")

    import random
    rng = random.Random(seed)

    enrollments = [s.enrollment for s in state.students]
    submitted = 0

    for student in state.students:
        if rng.random() > submit_rate:
            student.preferences = {}
            continue

        others = [e for e in enrollments if e != student.enrollment]
        count = rng.randint(1, min(pref_count, len(others)))
        chosen = rng.sample(others, count)
        priorities = list(range(1, count + 1))
        rng.shuffle(priorities)
        student.preferences = dict(zip(chosen, priorities))
        submitted += 1

    return {
        "message": f"Random surveys generated for {submitted} students",
        "total_students": len(state.students),
        "submitted": submitted,
        "skipped": len(state.students) - submitted,
        "seed": seed,
    }
