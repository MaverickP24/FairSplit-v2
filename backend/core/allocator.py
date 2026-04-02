"""
Snake-draft allocator.

Assigns students to 5 sections in a snake pattern (tier 0: A→E, tier 1: E→A, …)
so every section gets exactly one student per tier and identical total rank points.
"""
from typing import List
from ..models.student import Student
from ..models.section import Section

SECTION_NAMES = ["A", "B", "C", "D", "E"]
NUM_SECTIONS = 5


def snake_draft(students: List[Student]) -> List[Section]:
    """students must already be rank-sorted."""
    sections = [Section(name=n) for n in SECTION_NAMES]

    full_count = (len(students) // NUM_SECTIONS) * NUM_SECTIONS
    full_students = students[:full_count]
    partial_students = students[full_count:]

    for tier_idx in range(len(full_students) // NUM_SECTIONS):
        tier = full_students[tier_idx * NUM_SECTIONS: (tier_idx + 1) * NUM_SECTIONS]
        order = list(range(NUM_SECTIONS)) if tier_idx % 2 == 0 else list(range(NUM_SECTIONS - 1, -1, -1))
        for student, sec_idx in zip(tier, order):
            sections[sec_idx].add(student)

    # Partial tier: assign to the section with the lowest total rank points
    for student in partial_students:
        target = min(sections, key=lambda s: (s.total_rank_points, SECTION_NAMES.index(s.name)))
        target.add(student)

    return sections
