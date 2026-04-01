"""
Optimizer
---------
Improves friendship satisfaction AFTER the snake-draft, while never violating
any hard constraint.

Hard constraints checked on EVERY proposed swap:
  1. One-per-tier: the destination section must not already contain a student
     from the same tier as the incoming student.
  2. Size parity: section sizes must remain within ±1 of each other after swap.
  3. Rank-point balance: total rank points per section must remain PERFECTLY
     equal after the swap (this is automatically satisfied when swapping two
     students from the same tier, since they share identical rank_points).

Algorithm (3 phases):
  Phase 1 — Multi-pass friendship optimization (up to MAX_PASSES):
    For each pass, iterate all preference pairs sorted by combined weight.
    Try swapping to co-locate each pair. Stop early when a pass yields 0 swaps.

  Phase 2 — Isolation-targeted pass:
    Identify students with 0 preferred friends in their section.
    For each isolated student, try to swap them into a section containing
    at least one of their preferred friends.

  Swap partner selection prefers the "least-connected" candidate — the student
  with the fewest preferred friends in their current section — so we displace
  students who lose the least.

Mode: "strict" → only zero-cost swaps (same constraints apply)
      "balanced" → runs normally (default)
"""
from typing import List, Optional, Tuple, Set
from ..models.student import Student
from ..models.section import Section

NUM_SECTIONS = 5
MAX_PASSES = 10
TARGET_ISOLATION = 10.0  # target isolation rate %


def _can_swap(
    student_a: Student,  # moving into section_b
    student_b: Student,  # moving into section_a
    section_a: Section,
    section_b: Section,
) -> bool:
    """
    Check if swapping student_a (in section_a) with student_b (in section_b)
    is legal under all hard constraints.
    """
    # Same section — no-op
    if section_a.name == section_b.name:
        return False

    # Build post-swap tier sets
    tier_set_a_after = {s.tier for s in section_a.members if s != student_a}
    tier_set_b_after = {s.tier for s in section_b.members if s != student_b}

    if student_b.tier in tier_set_a_after:
        return False
    if student_a.tier in tier_set_b_after:
        return False

    # Rank point balance: only valid if rank_points are equal
    if student_a.rank_points != student_b.rank_points:
        return False

    return True


def _count_friends_in_section(student: Student, section: Section) -> int:
    """Count how many of student's preferred friends are in the given section."""
    section_enrollments = {s.enrollment for s in section.members}
    return sum(1 for enr in student.preferences if enr in section_enrollments)


def _find_swap_partner(
    target: Student,           # student we want to move to dest_section
    dest_section: Section,     # where we want to place target
    src_section: Section,      # target's current section
    pair_partner: Optional[Student] = None,  # the other student in the preference pair — exclude from candidates
) -> Optional[Student]:
    """
    Find the best swap partner in dest_section for target.
    Must share the same tier and pass all constraint checks.
    Excludes pair_partner (if given) so we don't do a no-op swap
    that just trades positions between two students trying to be together.
    Prefers the candidate with the fewest friends in their current section
    (least disruption).
    """
    candidates = [
        s for s in dest_section.members
        if s.tier == target.tier
        and (pair_partner is None or s.enrollment != pair_partner.enrollment)
        and _can_swap(target, s, src_section, dest_section)
    ]
    if not candidates:
        return None

    # Pick the least-connected candidate (fewest friends in dest_section)
    candidates.sort(key=lambda c: _count_friends_in_section(c, dest_section))
    return candidates[0]


def _build_preference_pairs(
    students: List[Student],
) -> List[Tuple[float, Student, Student]]:
    """
    Returns all preference pairs sorted by combined weight descending.
    Combined weight = weight(A wants B) + weight(B wants A).
    Only includes pairs where at least one side has a preference.
    """
    enrollment_map = {s.enrollment: s for s in students}
    seen = set()
    pairs = []

    for student in students:
        for other_enr, priority in student.preferences.items():
            key = tuple(sorted([student.enrollment, other_enr]))
            if key in seen:
                continue
            seen.add(key)

            other = enrollment_map.get(other_enr)
            if other is None:
                continue

            w_ab = student.preference_weight(other_enr)
            w_ba = other.preference_weight(student.enrollment)
            combined = w_ab + w_ba
            pairs.append((combined, student, other))

    pairs.sort(key=lambda x: -x[0])
    return pairs


def _section_of(student: Student, sections: List[Section]) -> Section:
    for s in sections:
        if s.name == student.section:
            return s
    raise ValueError(f"Student {student.enrollment} has no valid section")


def _execute_swap(
    student_a: Student, student_b: Student,
    section_a: Section, section_b: Section,
) -> None:
    """Swap student_a (in section_a) with student_b (in section_b)."""
    section_a.remove(student_a)
    section_b.remove(student_b)
    section_a.add(student_b)
    section_b.add(student_a)


def _run_single_friendship_pass(
    students: List[Student],
    sections: List[Section],
) -> Tuple[int, int]:
    """
    Single pass over all preference pairs.
    Returns (swaps_made, already_together).
    """
    pairs = _build_preference_pairs(students)
    swaps_made = 0
    already_together = 0

    for _weight, student_a, student_b in pairs:
        sec_a = _section_of(student_a, sections)
        sec_b = _section_of(student_b, sections)

        if sec_a.name == sec_b.name:
            already_together += 1
            continue

        # Try: move student_b into sec_a
        partner = _find_swap_partner(student_b, sec_a, sec_b, pair_partner=student_a)
        if partner is not None:
            _execute_swap(student_b, partner, sec_b, sec_a)
            swaps_made += 1
            continue

        # Try: move student_a into sec_b (symmetric)
        partner = _find_swap_partner(student_a, sec_b, sec_a, pair_partner=student_b)
        if partner is not None:
            _execute_swap(student_a, partner, sec_a, sec_b)
            swaps_made += 1

    return swaps_made, already_together


def _get_isolated_students(
    students: List[Student],
    sections: List[Section],
) -> List[Student]:
    """Return students who have preferences but 0 preferred friends in their section."""
    section_member_map = {s.name: {m.enrollment for m in s.members} for s in sections}
    isolated = []
    for student in students:
        if not student.preferences:
            continue
        section_peers = section_member_map.get(student.section, set())
        has_friend = any(enr in section_peers for enr in student.preferences)
        if not has_friend:
            isolated.append(student)
    return isolated


def _run_isolation_pass(
    students: List[Student],
    sections: List[Section],
) -> int:
    """
    Dedicated pass targeting isolated students.

    Strategy 1 (push direct): Swap student directly into a friend's section.
    Strategy 2 (push bridge): Two-step swap through an intermediate section.
    Strategy 3 (pull friend): Swap a friend into the student's section instead.

    Returns number of isolation-resolving swaps made.
    """
    enrollment_map = {s.enrollment: s for s in students}
    swaps_made = 0

    for _attempt in range(10):
        isolated = _get_isolated_students(students, sections)
        if not isolated:
            break

        pass_swaps = 0
        for student in isolated:
            src_section = _section_of(student, sections)

            # Build a set of sections containing at least one friend
            friend_sections: dict = {}   # section_name -> friend list
            for friend_enr in student.preferences:
                friend = enrollment_map.get(friend_enr)
                if friend is None or friend.section == student.section:
                    continue
                friend_sections.setdefault(friend.section, []).append(friend)

            # Sort target sections by number of friends (most friends first)
            sorted_targets = sorted(
                friend_sections.items(),
                key=lambda x: -len(x[1]),
            )

            swapped = False

            # Strategy 1: Direct push — swap student into a friend's section
            for sec_name, _friends in sorted_targets:
                dest_section = _section_of(_friends[0], sections)
                partner = _find_swap_partner(student, dest_section, src_section)
                if partner is not None:
                    _execute_swap(student, partner, src_section, dest_section)
                    pass_swaps += 1
                    swapped = True
                    break

            if swapped:
                continue

            # Strategy 2: Bridge push — two-step swap through intermediate
            for sec_name, _friends in sorted_targets:
                dest_section = _section_of(_friends[0], sections)
                for bridge_section in sections:
                    if bridge_section.name == src_section.name or bridge_section.name == dest_section.name:
                        continue
                    bridge_partner = _find_swap_partner(student, bridge_section, src_section)
                    if bridge_partner is None:
                        continue
                    _execute_swap(student, bridge_partner, src_section, bridge_section)
                    final_partner = _find_swap_partner(student, dest_section, bridge_section)
                    if final_partner is not None:
                        _execute_swap(student, final_partner, bridge_section, dest_section)
                        pass_swaps += 2
                        swapped = True
                        break
                    else:
                        _execute_swap(student, bridge_partner, bridge_section, src_section)
                if swapped:
                    break

            if swapped:
                continue

            # Strategy 3: Pull friend — swap a friend INTO student's section
            for sec_name, friends in sorted_targets:
                for friend in friends:
                    friend_section = _section_of(friend, sections)
                    partner = _find_swap_partner(friend, src_section, friend_section)
                    if partner is not None:
                        _execute_swap(friend, partner, friend_section, src_section)
                        pass_swaps += 1
                        swapped = True
                        break
                if swapped:
                    break

            if swapped:
                continue

            # Strategy 4: 3-way rotation — A→B, B→C, C→A
            # Student is in src. Find a friend in dest. Rotate through a third section.
            for sec_name, _friends in sorted_targets:
                dest_section = _section_of(_friends[0], sections)
                # Find all same-tier students
                tier = student.tier
                src_same_tier = [s for s in src_section.members if s.tier == tier and s != student]
                dest_same_tier = [s for s in dest_section.members if s.tier == tier]

                for third_section in sections:
                    if third_section.name in (src_section.name, dest_section.name):
                        continue
                    third_same_tier = [s for s in third_section.members if s.tier == tier]

                    # Try rotation: student→dest, dest_member→third, third_member→src
                    for d_student in dest_same_tier:
                        for t_student in third_same_tier:
                            # Check all 3 moves are individually valid after the full rotation
                            # After rotation: src loses student + gains t_student
                            #                 dest loses d_student + gains student
                            #                 third loses t_student + gains d_student
                            # Since all 3 are same tier, tier constraints are satisfied.
                            # Rank points: all same, so balance preserved.
                            if (student.rank_points == d_student.rank_points == t_student.rank_points):
                                # Execute 3-way rotation
                                src_section.remove(student)
                                dest_section.remove(d_student)
                                third_section.remove(t_student)
                                dest_section.add(student)
                                third_section.add(d_student)
                                src_section.add(t_student)
                                pass_swaps += 3
                                swapped = True
                                break
                        if swapped:
                            break
                    if swapped:
                        break
                if swapped:
                    break

        swaps_made += pass_swaps
        if pass_swaps == 0:
            break

    return swaps_made


def _current_isolation_rate(students: List[Student], sections: List[Section]) -> float:
    """Quick isolation rate calculation."""
    with_prefs = [s for s in students if s.preferences]
    if not with_prefs:
        return 0.0
    isolated = _get_isolated_students(students, sections)
    return len(isolated) / len(with_prefs) * 100


def _scatter_tier_students(
    students: List[Student],
    sections: List[Section],
    seed: int = 0,
) -> int:
    """Deterministically shuffle same-tier students across sections to break deadlocks.
    Only shuffles tiers that have isolated students. Returns swap count."""
    import random as _rng
    rng = _rng.Random(seed)
    swaps = 0

    isolated = _get_isolated_students(students, sections)
    isolated_tiers = {s.tier for s in isolated}

    for tier in sorted(isolated_tiers):
        # Collect all students at this tier and their sections
        tier_students = [(s, _section_of(s, sections)) for s in students if s.tier == tier]
        if len(tier_students) < 2:
            continue

        # All same rank_points, so any permutation preserves balance
        # Just shuffle section assignments within-tier
        student_objs = [s for s, _ in tier_students]
        section_objs = [sec for _, sec in tier_students]
        rng.shuffle(section_objs)

        for (stu, old_sec), new_sec in zip(tier_students, section_objs):
            if old_sec.name != new_sec.name:
                old_sec.remove(stu)
                new_sec.add(stu)
                swaps += 1

    return swaps


def run_friendship_pass(
    students: List[Student],
    sections: List[Section],
    mode: str = "balanced",
) -> dict:
    """
    Runs the full optimization pipeline in interleaved cycles:
      1. Multi-pass friendship optimization (up to MAX_PASSES)
      2. Isolation-targeted pass
      3. Repeat up to 5 cycles
      4. If isolation > target, scatter stuck tiers and retry

    Returns a stats dict with detailed swap information.
    """
    best_swaps = 0
    best_iso = float('inf')
    best_state = None  # enrollment -> section_name
    already_together = 0
    total_friendship_passes = 0
    total_isolation_swaps = 0

    for scatter_attempt in range(4):  # try up to 4 scatter attempts
        total_swaps = 0

        for _cycle in range(5):
            # Friendship passes
            cycle_swaps = 0
            for _ in range(MAX_PASSES):
                swaps, together = _run_single_friendship_pass(students, sections)
                total_swaps += swaps
                cycle_swaps += swaps
                already_together = together
                total_friendship_passes += 1
                if swaps == 0:
                    break

            # Isolation pass
            iso_swaps = _run_isolation_pass(students, sections)
            total_swaps += iso_swaps
            total_isolation_swaps += iso_swaps

            # If neither phase made progress, stop this cycle
            if cycle_swaps == 0 and iso_swaps == 0:
                break

        # Check isolation rate
        current_iso = _current_isolation_rate(students, sections)

        # Track best state
        if current_iso < best_iso:
            best_iso = current_iso
            best_swaps = total_swaps
            best_state = {s.enrollment: s.section for s in students}

        if current_iso <= TARGET_ISOLATION:
            break

        # Not at target yet — scatter stuck tiers and retry
        if scatter_attempt < 3:
            _scatter_tier_students(students, sections, seed=scatter_attempt + 1)

    # Restore best state if we didn't end on the best
    if best_state and _current_isolation_rate(students, sections) > best_iso:
        for s in students:
            if s.enrollment in best_state:
                target_sec_name = best_state[s.enrollment]
                if s.section != target_sec_name:
                    current_sec = _section_of(s, sections)
                    current_sec.remove(s)
        # Rebuild sections from best state
        for sec in sections:
            sec.members.clear()
            sec.tier_set.clear()
        for s in students:
            target_sec_name = best_state[s.enrollment]
            target_sec = next(sec for sec in sections if sec.name == target_sec_name)
            target_sec.add(s)

    return {
        "pairs_evaluated": len(_build_preference_pairs(students)),
        "already_together": already_together,
        "swaps_made": best_swaps,
        "friendship_passes": total_friendship_passes,
        "isolation_swaps": total_isolation_swaps,
    }
