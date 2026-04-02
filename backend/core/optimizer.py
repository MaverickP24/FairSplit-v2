"""
Friendship optimizer.

Swaps same-tier students between sections to co-locate preferred friends.
Only same-tier swaps are legal (preserves rank-point balance and one-per-tier constraint).

Pipeline:
  1. Multi-pass pairwise optimization (highest-weight pairs first)
  2. Isolation-targeted pass (direct push, bridge, pull, 3-way rotation)
  3. If isolation > target, scatter stuck tiers and retry (up to 4 attempts)
  4. Restore best state seen across all attempts
"""
from typing import List, Optional, Tuple
from ..models.student import Student
from ..models.section import Section

NUM_SECTIONS = 5
MAX_PASSES = 10
TARGET_ISOLATION = 10.0


def _can_swap(student_a: Student, student_b: Student, section_a: Section, section_b: Section) -> bool:
    """True if swapping A (in section_a) with B (in section_b) is constraint-safe."""
    if section_a.name == section_b.name:
        return False
    if student_a.rank_points != student_b.rank_points:
        return False
    tier_set_a = {s.tier for s in section_a.members if s != student_a}
    tier_set_b = {s.tier for s in section_b.members if s != student_b}
    if student_b.tier in tier_set_a or student_a.tier in tier_set_b:
        return False
    return True


def _count_friends_in_section(student: Student, section: Section) -> int:
    enrollments = {s.enrollment for s in section.members}
    return sum(1 for enr in student.preferences if enr in enrollments)


def _find_swap_partner(
    target: Student,
    dest_section: Section,
    src_section: Section,
    pair_partner: Optional[Student] = None,
) -> Optional[Student]:
    """Find the least-connected same-tier student in dest_section to swap with target.
    Excludes pair_partner to prevent no-op swaps between two students trying to be together."""
    candidates = [
        s for s in dest_section.members
        if s.tier == target.tier
        and (pair_partner is None or s.enrollment != pair_partner.enrollment)
        and _can_swap(target, s, src_section, dest_section)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda c: _count_friends_in_section(c, dest_section))
    return candidates[0]


def _build_preference_pairs(students: List[Student]) -> List[Tuple[float, Student, Student]]:
    """All preference pairs sorted by combined weight (mutual friends ranked highest)."""
    enrollment_map = {s.enrollment: s for s in students}
    seen = set()
    pairs = []

    for student in students:
        for other_enr in student.preferences:
            key = tuple(sorted([student.enrollment, other_enr]))
            if key in seen:
                continue
            seen.add(key)
            other = enrollment_map.get(other_enr)
            if other is None:
                continue
            combined = student.preference_weight(other_enr) + other.preference_weight(student.enrollment)
            pairs.append((combined, student, other))

    pairs.sort(key=lambda x: -x[0])
    return pairs


def _section_of(student: Student, sections: List[Section]) -> Section:
    for s in sections:
        if s.name == student.section:
            return s
    raise ValueError(f"Student {student.enrollment} has no valid section")


def _execute_swap(student_a: Student, student_b: Student, section_a: Section, section_b: Section) -> None:
    section_a.remove(student_a)
    section_b.remove(student_b)
    section_a.add(student_b)
    section_b.add(student_a)


def _run_single_friendship_pass(students: List[Student], sections: List[Section]) -> Tuple[int, int]:
    """Single pass over all preference pairs. Returns (swaps_made, already_together)."""
    pairs = _build_preference_pairs(students)
    swaps_made = 0
    already_together = 0

    for _weight, student_a, student_b in pairs:
        sec_a = _section_of(student_a, sections)
        sec_b = _section_of(student_b, sections)

        if sec_a.name == sec_b.name:
            already_together += 1
            continue

        partner = _find_swap_partner(student_b, sec_a, sec_b, pair_partner=student_a)
        if partner is not None:
            _execute_swap(student_b, partner, sec_b, sec_a)
            swaps_made += 1
            continue

        partner = _find_swap_partner(student_a, sec_b, sec_a, pair_partner=student_b)
        if partner is not None:
            _execute_swap(student_a, partner, sec_a, sec_b)
            swaps_made += 1

    return swaps_made, already_together


def _get_isolated_students(students: List[Student], sections: List[Section]) -> List[Student]:
    """Students who submitted preferences but have zero friends in their section."""
    section_members = {s.name: {m.enrollment for m in s.members} for s in sections}
    return [
        s for s in students
        if s.preferences and not any(enr in section_members.get(s.section, set()) for enr in s.preferences)
    ]


def _run_isolation_pass(students: List[Student], sections: List[Section]) -> int:
    """Try to de-isolate students via 4 strategies: direct push, bridge, pull, 3-way rotation."""
    enrollment_map = {s.enrollment: s for s in students}
    swaps_made = 0

    for _ in range(10):
        isolated = _get_isolated_students(students, sections)
        if not isolated:
            break

        pass_swaps = 0
        for student in isolated:
            src = _section_of(student, sections)

            # Map: section_name -> [friends in that section]
            friend_sections: dict = {}
            for friend_enr in student.preferences:
                friend = enrollment_map.get(friend_enr)
                if friend is None or friend.section == student.section:
                    continue
                friend_sections.setdefault(friend.section, []).append(friend)

            targets = sorted(friend_sections.items(), key=lambda x: -len(x[1]))
            swapped = False

            # Strategy 1: Direct push
            for _, friends in targets:
                dest = _section_of(friends[0], sections)
                partner = _find_swap_partner(student, dest, src)
                if partner:
                    _execute_swap(student, partner, src, dest)
                    pass_swaps += 1
                    swapped = True
                    break
            if swapped:
                continue

            # Strategy 2: Bridge push (src -> bridge -> dest)
            for _, friends in targets:
                dest = _section_of(friends[0], sections)
                for bridge in sections:
                    if bridge.name in (src.name, dest.name):
                        continue
                    bp = _find_swap_partner(student, bridge, src)
                    if not bp:
                        continue
                    _execute_swap(student, bp, src, bridge)
                    fp = _find_swap_partner(student, dest, bridge)
                    if fp:
                        _execute_swap(student, fp, bridge, dest)
                        pass_swaps += 2
                        swapped = True
                        break
                    else:
                        _execute_swap(student, bp, bridge, src)
                if swapped:
                    break
            if swapped:
                continue

            # Strategy 3: Pull a friend into student's section
            for _, friends in targets:
                for friend in friends:
                    fsec = _section_of(friend, sections)
                    partner = _find_swap_partner(friend, src, fsec)
                    if partner:
                        _execute_swap(friend, partner, fsec, src)
                        pass_swaps += 1
                        swapped = True
                        break
                if swapped:
                    break
            if swapped:
                continue

            # Strategy 4: 3-way rotation (student->dest, dest_member->third, third_member->src)
            tier = student.tier
            for _, friends in targets:
                dest = _section_of(friends[0], sections)
                dest_same = [s for s in dest.members if s.tier == tier]
                for third in sections:
                    if third.name in (src.name, dest.name):
                        continue
                    third_same = [s for s in third.members if s.tier == tier]
                    for d in dest_same:
                        for t in third_same:
                            if student.rank_points == d.rank_points == t.rank_points:
                                src.remove(student)
                                dest.remove(d)
                                third.remove(t)
                                dest.add(student)
                                third.add(d)
                                src.add(t)
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
    with_prefs = [s for s in students if s.preferences]
    if not with_prefs:
        return 0.0
    return len(_get_isolated_students(students, sections)) / len(with_prefs) * 100


def _scatter_tier_students(students: List[Student], sections: List[Section], seed: int = 0) -> int:
    """Shuffle within-tier section assignments for tiers that have isolated students."""
    import random as _rng
    rng = _rng.Random(seed)
    swaps = 0

    isolated_tiers = {s.tier for s in _get_isolated_students(students, sections)}
    for tier in sorted(isolated_tiers):
        tier_students = [(s, _section_of(s, sections)) for s in students if s.tier == tier]
        if len(tier_students) < 2:
            continue
        section_objs = [sec for _, sec in tier_students]
        rng.shuffle(section_objs)
        for (stu, old_sec), new_sec in zip(tier_students, section_objs):
            if old_sec.name != new_sec.name:
                old_sec.remove(stu)
                new_sec.add(stu)
                swaps += 1
    return swaps


def run_friendship_pass(students: List[Student], sections: List[Section], mode: str = "balanced") -> dict:
    """Full optimization pipeline. Returns stats dict."""
    best_swaps = 0
    best_iso = float('inf')
    best_state = None
    already_together = 0
    total_friendship_passes = 0
    total_isolation_swaps = 0

    for scatter_attempt in range(4):
        total_swaps = 0

        for _ in range(5):
            cycle_swaps = 0
            for _ in range(MAX_PASSES):
                swaps, together = _run_single_friendship_pass(students, sections)
                total_swaps += swaps
                cycle_swaps += swaps
                already_together = together
                total_friendship_passes += 1
                if swaps == 0:
                    break

            iso_swaps = _run_isolation_pass(students, sections)
            total_swaps += iso_swaps
            total_isolation_swaps += iso_swaps

            if cycle_swaps == 0 and iso_swaps == 0:
                break

        current_iso = _current_isolation_rate(students, sections)
        if current_iso < best_iso:
            best_iso = current_iso
            best_swaps = total_swaps
            best_state = {s.enrollment: s.section for s in students}

        if current_iso <= TARGET_ISOLATION:
            break

        if scatter_attempt < 3:
            _scatter_tier_students(students, sections, seed=scatter_attempt + 1)

    # Restore best state if current isn't the best
    if best_state and _current_isolation_rate(students, sections) > best_iso:
        for sec in sections:
            sec.members.clear()
            sec.tier_set.clear()
        for s in students:
            target_sec = next(sec for sec in sections if sec.name == best_state[s.enrollment])
            target_sec.add(s)

    return {
        "pairs_evaluated": len(_build_preference_pairs(students)),
        "already_together": already_together,
        "swaps_made": best_swaps,
        "friendship_passes": total_friendship_passes,
        "isolation_swaps": total_isolation_swaps,
    }
