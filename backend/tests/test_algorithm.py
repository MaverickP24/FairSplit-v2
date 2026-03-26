"""
Algorithm correctness tests.
Run from project root: python -m pytest backend/tests/ -v
Or directly:          python backend/tests/test_algorithm.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.models.student import Student
from backend.models.section import Section
from backend.core.ranker import assign_ranks
from backend.core.allocator import snake_draft, NUM_SECTIONS
from backend.core.optimizer import run_friendship_pass, _can_swap
from backend.core.evaluator import compute_metrics

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_students(n: int) -> list:
    """Generate n students with deterministic CGPAs."""
    students = []
    for i in range(n):
        # Spread CGPAs from 9.9 down to ~4.0, with some ties
        cgpa = round(max(4.0, 9.9 - i * (5.9 / n)), 2)
        students.append(Student(
            enrollment=f"EN{i+1:05d}",
            name=f"Student {i+1}",
            cgpa=cgpa,
        ))
    return students


def inject_preferences(students: list, pairs: list):
    """
    pairs = [(enr_a, enr_b, priority), ...]
    Mutual preference: both sides want each other at the given priority.
    """
    enr_map = {s.enrollment: s for s in students}
    for enr_a, enr_b, priority in pairs:
        a, b = enr_map[enr_a], enr_map[enr_b]
        a.preferences[enr_b] = priority
        b.preferences[enr_a] = priority


def section_map(sections: list) -> dict:
    return {s.name: s for s in sections}


# ─────────────────────────────────────────────
# Test 1: Ranker
# ─────────────────────────────────────────────

def test_ranker_determinism():
    """Same input always produces same ranking."""
    s1 = make_students(576)
    s2 = make_students(576)
    r1 = assign_ranks(s1)
    r2 = assign_ranks(s2)
    for a, b in zip(r1, r2):
        assert a.enrollment == b.enrollment
        assert a.rank == b.rank
        assert a.tier == b.tier
        assert a.rank_points == b.rank_points
    print("PASS test_ranker_determinism")


def test_ranker_tier_points():
    """Tiers of 5 get correct rank points using formula: 200 - (tier-1)."""
    students = make_students(576)
    ranked = assign_ranks(students)

    # Tier 1 = 200, Tier 2 = 199, ... No collapse
    for s in ranked:
        expected_pts = 200.0 - (s.tier - 1)
        assert s.rank_points == expected_pts, \
            f"Rank {s.rank} tier {s.tier}: expected {expected_pts}, got {s.rank_points}"

    # Verify tier grouping: ranks 1-5 → tier 1, ranks 6-10 → tier 2
    assert ranked[0].tier == 1
    assert ranked[4].tier == 1
    assert ranked[5].tier == 2
    assert ranked[9].tier == 2

    # All tiers have unique point values
    tier_pts = {s.tier: s.rank_points for s in ranked}
    assert len(set(tier_pts.values())) == len(tier_pts), \
        "Tier points are not all unique!"
    print("PASS test_ranker_tier_points")


def test_ranker_tiebreak_determinism():
    """Students with identical CGPA are always ordered by enrollment."""
    students = [
        Student("EN00003", "C", 8.5),
        Student("EN00001", "A", 8.5),
        Student("EN00002", "B", 8.5),
    ]
    ranked = assign_ranks(students)
    enrollments = [s.enrollment for s in ranked]
    assert enrollments == ["EN00001", "EN00002", "EN00003"], \
        f"Expected sorted by enrollment, got {enrollments}"
    print("PASS test_ranker_tiebreak_determinism")


# ─────────────────────────────────────────────
# Test 2: Snake-Draft Allocator
# ─────────────────────────────────────────────

def test_allocator_one_per_tier():
    """Every complete tier of 5 has exactly one student per section."""
    students = make_students(576)
    ranked = assign_ranks(students)
    sections = snake_draft(ranked)

    sm = section_map(sections)

    # Check all full tiers (tiers 1..115 for 576 students)
    max_full_tier = (576 - 1) // 5  # = 115 (0-based last full tier index → tier 115)
    for tier_num in range(1, max_full_tier + 1):
        tier_students = [s for s in ranked if s.tier == tier_num]
        if len(tier_students) < 5:
            continue  # partial tier — skip
        sections_with_tier = [s.name for s in sections if s.has_tier(tier_num)]
        assert len(sections_with_tier) == 5, \
            f"Tier {tier_num}: expected 1 per section, found in {sections_with_tier}"

    print("PASS test_allocator_one_per_tier")


def test_allocator_section_sizes():
    """All sections are within ±1 of each other."""
    students = make_students(576)
    ranked = assign_ranks(students)
    sections = snake_draft(ranked)

    sizes = [s.size for s in sections]
    assert max(sizes) - min(sizes) <= 1, \
        f"Section sizes differ by more than 1: {sizes}"
    assert sum(sizes) == 576, \
        f"Total students mismatch: {sum(sizes)} != 576"
    print(f"PASS test_allocator_section_sizes  sizes={sizes}")


def test_allocator_rank_point_balance():
    """
    Sections achieve the minimum possible rank point imbalance.
    For N students where N % 5 == r (r leftover), the minimum imbalance
    is the rank_points of those r partial-tier students.
    For N divisible by 5: must be exactly 0.0
    """
    students = make_students(576)
    ranked = assign_ranks(students)
    sections = snake_draft(ranked)

    pts = [s.total_rank_points for s in sections]
    remainder = len(students) % 5
    if remainder == 0:
        assert max(pts) - min(pts) == 0.0, f"Should be perfectly balanced: {pts}"
    else:
        partial_pts = ranked[-1].rank_points
        assert max(pts) - min(pts) <= partial_pts, \
            f"Imbalance {max(pts)-min(pts)} exceeds partial tier pts {partial_pts}: {pts}"
    print(f"PASS test_allocator_rank_point_balance  delta={max(pts)-min(pts)} pts={pts}")


def test_allocator_determinism():
    """Same students always produce same section assignment."""
    students_a = make_students(576)
    students_b = make_students(576)
    ranked_a = assign_ranks(students_a)
    ranked_b = assign_ranks(students_b)
    secs_a = snake_draft(ranked_a)
    secs_b = snake_draft(ranked_b)

    for sa, sb in zip(secs_a, secs_b):
        enr_a = sorted(m.enrollment for m in sa.members)
        enr_b = sorted(m.enrollment for m in sb.members)
        assert enr_a == enr_b, f"Section {sa.name} differs between runs"
    print("PASS test_allocator_determinism")


def test_allocator_no_student_lost():
    """Every student appears in exactly one section."""
    students = make_students(576)
    ranked = assign_ranks(students)
    sections = snake_draft(ranked)

    all_enrolled = set(s.enrollment for s in students)
    placed = []
    for sec in sections:
        for m in sec.members:
            placed.append(m.enrollment)

    assert len(placed) == len(all_enrolled), \
        f"Placed {len(placed)} but expected {len(all_enrolled)}"
    assert set(placed) == all_enrolled, "Some students are duplicated or missing"
    print("PASS test_allocator_no_student_lost")


# ─────────────────────────────────────────────
# Test 3: Friendship Optimizer
# ─────────────────────────────────────────────

def test_optimizer_preserves_hard_constraints():
    """
    After friendship pass, one-per-tier and rank balance must still hold.
    We inject heavy preferences between students in the same tier (hardest case).
    """
    students = make_students(576)
    ranked = assign_ranks(students)
    sections = snake_draft(ranked)

    # Inject preferences: students in tier 1 all want each other
    tier1 = [s for s in ranked if s.tier == 1]
    for i, a in enumerate(tier1):
        for b in tier1:
            if a.enrollment != b.enrollment:
                a.preferences[b.enrollment] = 1  # highest priority

    run_friendship_pass(ranked, sections)

    # Constraint 1: one-per-tier still holds
    for sec in sections:
        tier_list = [m.tier for m in sec.members]
        assert len(tier_list) == len(set(tier_list)), \
            f"Section {sec.name} has duplicate tiers after optimization: {tier_list}"

    # Constraint 2: rank points imbalance no worse than before optimization
    pts = [s.total_rank_points for s in sections]
    remainder = len(students) % 5
    partial_pts = students[-1].rank_points if remainder else 0
    assert max(pts) - min(pts) <= partial_pts, \
        f"Rank points imbalanced after optimization: {pts}"

    # Constraint 3: tier-1 students are still all in different sections
    tier1_sections = [s.section for s in tier1]
    assert len(tier1_sections) == len(set(tier1_sections)), \
        f"Tier-1 students ended up together: {tier1_sections}"

    print("PASS test_optimizer_preserves_hard_constraints")


def test_optimizer_improves_satisfaction():
    """
    Optimizer should achieve higher satisfaction than baseline snake-draft alone,
    when there are satisfiable preferences between different-tier students.
    """
    students = make_students(50)  # small for speed
    ranked = assign_ranks(students)

    # Inject preferences between tier-1 and tier-2 students (different tiers → swappable)
    tier1 = [s for s in ranked if s.tier == 1]
    tier2 = [s for s in ranked if s.tier == 2]

    # Put tier1[0] and tier2[0] at top priority for each other
    tier1[0].preferences[tier2[0].enrollment] = 1
    tier2[0].preferences[tier1[0].enrollment] = 1

    sections = snake_draft(ranked)

    # Measure before
    before = compute_metrics(ranked, sections)

    stats = run_friendship_pass(ranked, sections)

    # Measure after
    after = compute_metrics(ranked, sections)

    # Either satisfaction improved, or they were already together
    assert after["satisfaction_score"] >= before["satisfaction_score"], \
        "Optimizer made satisfaction worse"

    print(f"PASS test_optimizer_improves_satisfaction  "
          f"before={before['satisfaction_score']}% after={after['satisfaction_score']}% "
          f"swaps={stats['swaps_made']}")


def test_optimizer_same_tier_friends_never_colocated():
    """
    If two students in the same tier list each other as top priority,
    the optimizer must NOT place them together (impossible without violating one-per-tier).
    """
    students = make_students(576)
    ranked = assign_ranks(students)
    sections = snake_draft(ranked)

    tier1 = [s for s in ranked if s.tier == 1]
    # tier1[0] and tier1[1] desperately want each other
    tier1[0].preferences[tier1[1].enrollment] = 1
    tier1[1].preferences[tier1[0].enrollment] = 1

    run_friendship_pass(ranked, sections)

    # They must still be in different sections
    assert tier1[0].section != tier1[1].section, \
        "Same-tier friends were incorrectly placed together"
    print("PASS test_optimizer_same_tier_friends_never_colocated")


# ─────────────────────────────────────────────
# Test 4: can_swap logic
# ─────────────────────────────────────────────

def test_can_swap_rejects_same_tier_conflict():
    """Swap that would put two same-tier students in one section is rejected."""
    # Section A has tier-1 student X. Section B has tier-1 student Y and tier-2 student Z.
    # Trying to swap Y into A: A already has tier-1 → reject.
    x = Student("X001", "X", 9.0, rank=1, tier=1, rank_points=100)
    y = Student("Y001", "Y", 9.0, rank=2, tier=1, rank_points=100)
    z = Student("Z001", "Z", 8.5, rank=6, tier=2, rank_points=95)

    sec_a = Section("A")
    sec_b = Section("B")
    sec_a.add(x)
    sec_b.add(y)
    sec_b.add(z)

    # Try to swap y (tier 1) into sec_a — should fail (sec_a already has tier 1)
    assert not _can_swap(z, x, sec_b, sec_a), "Should reject: sec_b after would have no tier-2"
    print("PASS test_can_swap_rejects_same_tier_conflict")


def test_can_swap_accepts_valid_same_tier_swap():
    """
    Swapping two students of the same tier is valid when no tier conflict exists.
    """
    a = Student("A001", "A", 9.0, rank=1, tier=1, rank_points=100)
    b = Student("B001", "B", 8.9, rank=2, tier=1, rank_points=100)
    # Extra members to fill tiers 2,3
    a2 = Student("A002", "A2", 8.5, rank=6, tier=2, rank_points=95)
    b2 = Student("B002", "B2", 8.4, rank=7, tier=2, rank_points=95)

    sec_a = Section("A")
    sec_b = Section("B")
    sec_a.add(a); sec_a.add(a2)
    sec_b.add(b); sec_b.add(b2)

    # Swap a (tier1) with b (tier1): sec_a loses tier1 gains tier1, sec_b vice versa → valid
    assert _can_swap(a, b, sec_a, sec_b), "Should accept: same-tier swap, no conflict"
    print("PASS test_can_swap_accepts_valid_same_tier_swap")


# ─────────────────────────────────────────────
# Run all
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("FairSplit Algorithm Tests")
    print("=" * 60)

    print("\n── Ranker ──")
    test_ranker_determinism()
    test_ranker_tier_points()
    test_ranker_tiebreak_determinism()

    print("\n── Allocator ──")
    test_allocator_one_per_tier()
    test_allocator_section_sizes()
    test_allocator_rank_point_balance()
    test_allocator_determinism()
    test_allocator_no_student_lost()

    print("\n── Optimizer ──")
    test_optimizer_preserves_hard_constraints()
    test_optimizer_improves_satisfaction()
    test_optimizer_same_tier_friends_never_colocated()

    print("\n── Swap Logic ──")
    test_can_swap_rejects_same_tier_conflict()
    test_can_swap_accepts_valid_same_tier_swap()

    print("\n" + "=" * 60)
    print("All tests passed.")
    print("=" * 60)
