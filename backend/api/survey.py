from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Dict
from ..state import state

router = APIRouter()


class SurveySubmission(BaseModel):
    enrollment: str
    # preferences: {enrollment: priority(1-10)}
    preferences: Dict[str, int]

    @field_validator("preferences")
    @classmethod
    def validate_preferences(cls, v):
        if len(v) > 10:
            raise ValueError("Maximum 10 preferences allowed")
        for enr, priority in v.items():
            if not (1 <= priority <= 10):
                raise ValueError(f"Priority for {enr} must be between 1 and 10")
        # Ensure each priority is used at most once
        priorities = list(v.values())
        if len(priorities) != len(set(priorities)):
            seen = {}
            for enr, p in v.items():
                if p in seen:
                    raise ValueError(
                        f"Duplicate priority {p}: used by both {seen[p]} and {enr}. Each priority must be unique."
                    )
                seen[p] = enr
        return v


@router.post("/survey")
def submit_survey(submission: SurveySubmission):
    """
    Student submits their friend preferences.
    Enrollment must exist in the loaded dataset.
    Preferred enrollments must also exist in the dataset.
    """
    if not state.students:
        raise HTTPException(status_code=404, detail="No student data loaded yet")

    student_map = state.student_map()

    student = student_map.get(submission.enrollment)
    if student is None:
        raise HTTPException(
            status_code=404,
            detail=f"Enrollment {submission.enrollment} not found in dataset"
        )

    # Validate all preferred enrollments exist
    invalid = [e for e in submission.preferences if e not in student_map]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown enrollments in preferences: {invalid}"
        )

    # Prevent self-preference
    cleaned = {
        e: p for e, p in submission.preferences.items()
        if e != submission.enrollment
    }

    student.preferences = cleaned

    return {
        "message": "Preferences saved",
        "enrollment": submission.enrollment,
        "preferences_count": len(cleaned),
    }


@router.get("/survey/status")
def survey_status():
    """How many students have submitted preferences."""
    if not state.students:
        raise HTTPException(status_code=404, detail="No data loaded")
    submitted = sum(1 for s in state.students if s.preferences)
    return {
        "total_students": len(state.students),
        "submitted": submitted,
        "pending": len(state.students) - submitted,
    }


@router.post("/survey/random")
def generate_random_surveys(
    seed: int = 42,
    pref_count: int = 10,
    submit_rate: float = 0.85,
):
    """
    Auto-generate random friend preferences for all students.
    Simulates a realistic survey response — ~85% of students submit,
    each with up to 10 random friends at random priorities.
    Overwrites any existing preferences.

    Params:
      seed        : random seed (change to get a different set of preferences)
      pref_count  : max preferences per student (1–10)
      submit_rate : fraction of students who "submit" (0.0–1.0)
    """
    if not state.students:
        raise HTTPException(status_code=404, detail="No student data loaded yet")

    import random
    rng = random.Random(seed)

    enrollments = [s.enrollment for s in state.students]
    submitted = 0

    for student in state.students:
        # Simulate some students not filling in the survey
        if rng.random() > submit_rate:
            student.preferences = {}
            continue

        others = [e for e in enrollments if e != student.enrollment]
        count  = rng.randint(1, min(pref_count, len(others)))
        chosen = rng.sample(others, count)

        # Assign distinct priorities 1..count, shuffled
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
