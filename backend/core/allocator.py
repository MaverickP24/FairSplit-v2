"""
Allocator
---------
Produces the initial section assignment using a snake-draft over rank-sorted
students, grouped by complete tiers of 5.

For each complete tier of 5:
  Even tiers (0,2,4,...): assign left-to-right  S1,S2,S3,S4,S5
  Odd  tiers (1,3,5,...): assign right-to-left  S5,S4,S3,S2,S1
  This keeps total rank_points perfectly equal across all sections.

For the partial last tier (1-4 students):
  These students share the same rank_points as the last full tier.
  We cannot do one-per-section (not enough of them), so we must distribute
  them to maintain rank_point balance. We assign each partial-tier student
  to the section currently lowest in total rank_points (tiebreak: section
  index for determinism). Since all partial students have the same points,
  their placement doesn't disturb balance as long as they go to sections
  that are already equal or slightly behind -- but with only 1 student in
  the partial tier (576 students, remainder=1) the simplest and correct
  approach is to assign them to the section that gets one fewer student from
  the snake-draft (i.e. the one that's currently smallest).

Always deterministic: no randomness anywhere.
"""
from typing import List
from ..models.student import Student
from ..models.section import Section

SECTION_NAMES = ["A", "B", "C", "D", "E"]
NUM_SECTIONS = 5


def _make_sections() -> List[Section]:
    return [Section(name=n) for n in SECTION_NAMES]


def snake_draft(students: List[Student]) -> List[Section]:
    """
    students must already be rank-sorted (assign_ranks called).
    Returns 5 Sections with members assigned.
    """
    sections = _make_sections()

    full_count = (len(students) // NUM_SECTIONS) * NUM_SECTIONS
    full_students = students[:full_count]
    partial_students = students[full_count:]   

    for tier_idx in range(len(full_students) // NUM_SECTIONS):
        tier_students = full_students[tier_idx * NUM_SECTIONS: (tier_idx + 1) * NUM_SECTIONS]
        if tier_idx % 2 == 0:
            order = list(range(NUM_SECTIONS))               
        else:
            order = list(range(NUM_SECTIONS - 1, -1, -1)) 
        for student, section_idx in zip(tier_students, order):
            sections[section_idx].add(student)
    for student in partial_students:
        target = min(
            sections,
            key=lambda s: (s.total_rank_points, SECTION_NAMES.index(s.name))
        )
        target.add(student)

    return sections
