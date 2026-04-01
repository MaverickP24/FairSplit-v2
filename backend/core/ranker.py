"""
Ranker
------
Assigns ranks, tiers, and rank points to students sorted by CGPA.

Each tier contains 5 students. Every tier gets a unique point value:
  points = 200 - (tier - 1)
  Tier 1: 200,  Tier 2: 199,  ...  No floor or collapse.
"""
from typing import List
from ..models.student import Student


def assign_ranks(students):
    sorted_students = sorted(students, key=lambda s: (-s.cgpa, s.enrollment))

    num_full_tiers = len(sorted_students) // 5
    for idx, student in enumerate(sorted_students):
        rank = idx + 1
        tier = (idx // 5) + 1
        
        # Partial tier (beyond last full multiple of 5) gets 0 points
        if tier > num_full_tiers:
            rank_points = 0.0
        else:
            rank_points = 200.0 - (tier - 1)
            
        student.rank = rank
        student.tier = tier
        student.rank_points = rank_points

    return sorted_students

