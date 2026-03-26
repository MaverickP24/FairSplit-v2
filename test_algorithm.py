"""
Algorithm correctness test — run directly with: python test_algorithm.py

Verifies all hard constraints hold after allocation + friendship pass:
  1. Every tier of 5 has exactly one student per section
  2. Section sizes within ±1
  3. Rank points perfectly equal across sections
  4. Every student placed exactly once
  5. Deterministic — two runs produce identical results
  6. Friendship pass never violates constraints
"""
import sys
import random
sys.path.insert(0, ".")

from backend.models.student import Student
from backend.models.section import Section
from backend.core.ranker import assign_ranks
from backend.core.allocator import snake_draft
from backend.core.optimizer import run_friendship_pass
from backend.core.evaluator import compute_metrics


# ─── Generate dummy students ───────────────────────────────────────────────

def make_students(n=576, seed=42) -> list:
    rng = random.Random(seed)
    students = []
    for i in range(n):
        cgpa = round(rng.uniform(4.0, 10.0), 2)
        enrollment = f"2021{str(i+1).zfill(5)}"
        students.append(Student(
            enrollment=enrollment,
            name=f"Student_{i+1}",
            cgpa=cgpa,
        ))
    return students


def add_dummy_preferences(students: list, seed=99):
    """Give ~80% of students up to 10 random preferences."""
    rng = random.Random(seed)
    enrollments = [s.enrollment for s in students]
    for student in students:
        if rng.random() < 0.8:
            others = [e for e in enrollments if e != student.enrollment]
            chosen = rng.sample(others, min(10, len(others)))
            student.preferences = {
                e: rng.randint(1, 10) for e in chosen
            }


# ─── Constraint checkers ───────────────────────────────────────────────────

def check_one_per_tier(sections: list, students: list) -> list:
    errors = []
    for section in sections:
        tier_counts = {}
        for s in section.members:
            tier_counts[s.tier] = tier_counts.get(s.tier, 0) + 1
        for tier, count in tier_counts.items():
            if count > 1:
                errors.append(
                    f"Section {section.name}: tier {tier} appears {count} times"
                )
    return errors


def check_size_parity(sections: list) -> list:
    sizes = [s.size for s in sections]
    if max(sizes) - min(sizes) > 1:
        return [f"Size imbalance: {dict((s.name, s.size) for s in sections)}"]
    return []


def check_rank_point_balance(sections: list) -> list:
    pts = [s.total_rank_points for s in sections]
    delta = max(pts) - min(pts)
    if delta > 0.001:
        return [f"Rank point imbalance: delta={delta:.4f}, per section: "
                f"{dict((s.name, round(s.total_rank_points,2)) for s in sections)}"]
    return []


def check_all_placed(students: list, sections: list) -> list:
    placed = {s.enrollment for sec in sections for s in sec.members}
    all_enr = {s.enrollment for s in students}
    missing = all_enr - placed
    duplicated = []
    seen = {}
    for sec in sections:
        for s in sec.members:
            if s.enrollment in seen:
                duplicated.append(s.enrollment)
            seen[s.enrollment] = sec.name
    errors = []
    if missing:
        errors.append(f"{len(missing)} students not placed: {list(missing)[:5]}")
    if duplicated:
        errors.append(f"{len(duplicated)} students placed twice: {duplicated[:5]}")
    return errors


def check_determinism(students_factory) -> list:
    """Run allocation twice with identical input, compare section assignments."""
    errors = []
    results = []
    for _ in range(2):
        sts = students_factory()
        ranked = assign_ranks(sts)
        sections = snake_draft(ranked)
        # Collect enrollment→section mapping
        mapping = {s.enrollment: sec.name for sec in sections for s in sec.members}
        results.append(mapping)
    if results[0] != results[1]:
        errors.append("Non-deterministic: two runs gave different results")
    return errors


# ─── Run all tests ─────────────────────────────────────────────────────────

def run_tests():
    print("=" * 60)
    print("FairSplit Algorithm Test Suite — 576 students")
    print("=" * 60)

    all_passed = True

    # ── Test 1: Determinism ────────────────────────────────────────
    print("\n[1] Determinism check...")
    det_errors = check_determinism(lambda: make_students(576))
    if det_errors:
        for e in det_errors:
            print(f"  FAIL: {e}")
        all_passed = False
    else:
        print("  PASS — identical output on two runs")

    # ── Build allocation for remaining tests ───────────────────────
    students = make_students(576)
    ranked = assign_ranks(students)
    sections = snake_draft(ranked)

    # ── Test 2: All students placed ────────────────────────────────
    print("\n[2] All students placed exactly once...")
    place_errors = check_all_placed(ranked, sections)
    if place_errors:
        for e in place_errors:
            print(f"  FAIL: {e}")
        all_passed = False
    else:
        total = sum(s.size for s in sections)
        print(f"  PASS — {total} students placed across {len(sections)} sections")

    # ── Test 3: One per tier per section ──────────────────────────
    print("\n[3] One student per tier per section...")
    tier_errors = check_one_per_tier(sections, ranked)
    if tier_errors:
        for e in tier_errors:
            print(f"  FAIL: {e}")
        all_passed = False
    else:
        tier_count = ranked[-1].tier
        print(f"  PASS — {tier_count} tiers, all correctly distributed")

    # ── Test 4: Size parity ────────────────────────────────────────
    print("\n[4] Section size parity (±1)...")
    size_errors = check_size_parity(sections)
    sizes = {s.name: s.size for s in sections}
    if size_errors:
        for e in size_errors:
            print(f"  FAIL: {e}")
        all_passed = False
    else:
        print(f"  PASS — sizes: {sizes}")

    # ── Test 5: Rank point balance ─────────────────────────────────
    print("\n[5] Rank point balance (perfect equality)...")
    bal_errors = check_rank_point_balance(sections)
    pts = {s.name: round(s.total_rank_points, 2) for s in sections}
    if bal_errors:
        for e in bal_errors:
            print(f"  FAIL: {e}")
        all_passed = False
    else:
        print(f"  PASS — rank points: {pts}")

    # ── Test 6: Friendship pass preserves all constraints ─────────
    print("\n[6] Friendship pass — constraints survive optimization...")
    add_dummy_preferences(ranked)
    opt_stats = run_friendship_pass(ranked, sections, mode="balanced")
    print(f"  Optimizer stats: {opt_stats}")

    post_tier_errors = check_one_per_tier(sections, ranked)
    post_size_errors = check_size_parity(sections)
    post_bal_errors  = check_rank_point_balance(sections)
    post_place_errors = check_all_placed(ranked, sections)

    post_errors = post_tier_errors + post_size_errors + post_bal_errors + post_place_errors
    if post_errors:
        for e in post_errors:
            print(f"  FAIL: {e}")
        all_passed = False
    else:
        print("  PASS — all hard constraints still hold after friendship pass")

    # ── Test 7: Metrics ────────────────────────────────────────────
    print("\n[7] Metrics computation...")
    m = compute_metrics(ranked, sections)
    print(f"  Satisfaction score   : {m.get('satisfaction_score')}%")
    print(f"  Isolation rate       : {m.get('isolation_rate')}%")
    print(f"  At-least-1 friend    : {m.get('at_least_one_rate')}%")
    print(f"  Avg friends/student  : {m.get('avg_friends_per_student')}")
    print(f"  Balance score (delta): {m.get('balance_score')} pts")
    print("  PASS" if "satisfaction_score" in m else "  FAIL — metrics returned error")

    # ── Tier assignment spot check ─────────────────────────────────
    print("\n[8] Tier/rank-point spot check (first 15 students)...")
    print(f"  {'Rank':<6} {'Tier':<6} {'Pts':<8} {'CGPA':<8} {'Section'}")
    print(f"  {'-'*40}")
    for s in ranked[:15]:
        print(f"  {s.rank:<6} {s.tier:<6} {s.rank_points:<8.1f} {s.cgpa:<8} {s.section}")

    # ── Summary ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED — see above")
    print("=" * 60)
    return all_passed


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
