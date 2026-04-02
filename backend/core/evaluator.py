import random
from typing import List
from ..models.student import Student
from ..models.section import Section


def _satisfaction_for_student(student: Student, section_members: List[Student]) -> dict:
    section_enrollments = {s.enrollment for s in section_members if s.enrollment != student.enrollment}
    total_weight = sum(11 - p for p in student.preferences.values())
    achieved_weight = 0.0
    friend_count = 0

    for enr, priority in student.preferences.items():
        if enr in section_enrollments:
            achieved_weight += (11 - priority)
            friend_count += 1

    return {
        "satisfaction": (achieved_weight / total_weight * 100) if total_weight > 0 else 0.0,
        "friend_count": friend_count,
        "has_friend": friend_count > 0,
    }


def compute_metrics(students: List[Student], sections: List[Section]) -> dict:
    section_map = {s.name: s.members for s in sections}
    with_prefs = [s for s in students if s.preferences]
    if not with_prefs:
        return {"error": "No preference data submitted yet"}

    scores = []
    isolated = 0
    friends = []

    for student in with_prefs:
        result = _satisfaction_for_student(student, section_map.get(student.section, []))
        scores.append(result["satisfaction"])
        friends.append(result["friend_count"])
        if not result["has_friend"]:
            isolated += 1

    n = len(with_prefs)
    pts = [s.total_rank_points for s in sections]

    return {
        "satisfaction_score": round(sum(scores) / n, 2),
        "isolation_rate": round(isolated / n * 100, 2),
        "at_least_one_rate": round((n - isolated) / n * 100, 2),
        "avg_friends_per_student": round(sum(friends) / n, 2),
        "balance_score": round(max(pts) - min(pts), 2),
        "students_with_preferences": n,
        "section_rank_points": {s.name: round(s.total_rank_points, 2) for s in sections},
        "section_sizes": {s.name: s.size for s in sections},
    }


def compute_baseline_metrics(students: List[Student]) -> dict:
    """Average metrics over 10 random allocations for comparison."""
    with_prefs = [s for s in students if s.preferences]
    if not with_prefs:
        return {}

    NAMES = ["A", "B", "C", "D", "E"]
    runs = 10
    sat_scores = []
    iso_rates = []

    original_sections = {s.enrollment: s.section for s in students}

    for _ in range(runs):
        shuffled = students[:]
        random.shuffle(shuffled)
        chunk = len(shuffled) // 5
        temp = [Section(name=n) for n in NAMES]
        for i, s in enumerate(shuffled):
            temp[min(i // chunk, 4)].add(s)

        sm = {s.name: s.members for s in temp}
        sats, iso = [], 0
        for student in with_prefs:
            r = _satisfaction_for_student(student, sm.get(student.section, []))
            sats.append(r["satisfaction"])
            if not r["has_friend"]:
                iso += 1
        sat_scores.append(sum(sats) / len(sats))
        iso_rates.append(iso / len(with_prefs) * 100)

        for s in temp:
            s.members.clear()
            s.tier_set.clear()

    for s in students:
        s.section = original_sections[s.enrollment]

    return {
        "baseline_satisfaction_score": round(sum(sat_scores) / runs, 2),
        "baseline_isolation_rate": round(sum(iso_rates) / runs, 2),
    }
