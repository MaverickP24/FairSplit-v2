"""
Evaluator
---------
Computes all metrics after allocation is complete.

Metrics:
  satisfaction_score    % of preferred friends who ended up in same section
                        (weighted by priority — priority-1 friend counts more)
  isolation_rate        % of students with 0 preferred friends in their section
  at_least_one_rate     % of students with ≥1 preferred friend in section
  balance_score         max rank_points delta across all section pairs (0 = perfect)
  avg_friends_per_student  average count of preferred friends in same section
  baseline_*            same metrics under random assignment (for comparison)
"""
import random
from typing import List
from ..models.student import Student
from ..models.section import Section


def _satisfaction_for_student(student: Student, section_members: List[Student]) -> dict:
    section_enrollments = {s.enrollment for s in section_members if s.enrollment != student.enrollment}
    total_possible_weight = sum(11 - p for p in student.preferences.values())
    achieved_weight = 0.0
    friend_count = 0

    for enr, priority in student.preferences.items():
        if enr in section_enrollments:
            achieved_weight += (11 - priority)
            friend_count += 1

    satisfaction = (achieved_weight / total_possible_weight * 100) if total_possible_weight > 0 else 0.0
    return {
        "satisfaction": satisfaction,
        "friend_count": friend_count,
        "has_friend": friend_count > 0,
    }


def compute_metrics(students: List[Student], sections: List[Section]) -> dict:
    section_member_map = {s.name: s.members for s in sections}

    students_with_prefs = [s for s in students if s.preferences]
    if not students_with_prefs:
        return {"error": "No preference data submitted yet"}

    satisfaction_scores = []
    isolated_count = 0
    friend_counts = []

    for student in students_with_prefs:
        members = section_member_map.get(student.section, [])
        result = _satisfaction_for_student(student, members)
        satisfaction_scores.append(result["satisfaction"])
        friend_counts.append(result["friend_count"])
        if not result["has_friend"]:
            isolated_count += 1

    n = len(students_with_prefs)
    pts = [s.total_rank_points for s in sections]
    balance_score = max(pts) - min(pts)

    return {
        "satisfaction_score": round(sum(satisfaction_scores) / n, 2),
        "isolation_rate": round(isolated_count / n * 100, 2),
        "at_least_one_rate": round((n - isolated_count) / n * 100, 2),
        "avg_friends_per_student": round(sum(friend_counts) / n, 2),
        "balance_score": round(balance_score, 2),
        "students_with_preferences": n,
        "section_rank_points": {s.name: round(s.total_rank_points, 2) for s in sections},
        "section_sizes": {s.name: s.size for s in sections},
    }


def compute_baseline_metrics(students: List[Student]) -> dict:
    """Run a random allocation 10 times and average the metrics for comparison."""
    students_with_prefs = [s for s in students if s.preferences]
    if not students_with_prefs:
        return {}

    from ..models.section import Section
    NAMES = ["A", "B", "C", "D", "E"]
    runs = 10
    sat_scores = []
    iso_rates = []

    # Save original section assignments before mutating
    original_sections = {s.enrollment: s.section for s in students}

    for _ in range(runs):
        shuffled = students[:]
        random.shuffle(shuffled)
        chunk = len(shuffled) // 5
        temp_sections = [Section(name=n) for n in NAMES]
        for i, s in enumerate(shuffled):
            temp_sections[min(i // chunk, 4)].add(s)

        sm = {s.name: s.members for s in temp_sections}
        sats, isolated = [], 0
        for student in students_with_prefs:
            members = sm.get(student.section, [])
            r = _satisfaction_for_student(student, members)
            sats.append(r["satisfaction"])
            if not r["has_friend"]:
                isolated += 1
        sat_scores.append(sum(sats) / len(sats))
        iso_rates.append(isolated / len(students_with_prefs) * 100)

        # Reset temp section members
        for s in temp_sections:
            s.members.clear()
            s.tier_set.clear()

    # Restore original section assignments
    for s in students:
        s.section = original_sections[s.enrollment]

    return {
        "baseline_satisfaction_score": round(sum(sat_scores) / runs, 2),
        "baseline_isolation_rate": round(sum(iso_rates) / runs, 2),
    }
