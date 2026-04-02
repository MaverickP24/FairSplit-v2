from typing import List
from ..models.student import Student


def assign_ranks(students):
    """Sort by CGPA desc, assign tiers of 5. Points = 200 - (tier - 1). Partial tier gets 0."""
    sorted_students = sorted(students, key=lambda s: (-s.cgpa, s.enrollment))
    num_full_tiers = len(sorted_students) // 5

    for idx, student in enumerate(sorted_students):
        tier = (idx // 5) + 1
        student.rank = idx + 1
        student.tier = tier
        student.rank_points = 200.0 - (tier - 1) if tier <= num_full_tiers else 0.0

    return sorted_students
