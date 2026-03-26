from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Student:
    enrollment: str
    name: str
    cgpa: float

    # Set by ranker
    rank: int = 0
    tier: int = 0          # tier number (1-based)
    rank_points: float = 0.0

    # Set by survey
    preferences: Dict[str, int] = field(default_factory=dict)
    # preferences = {enrollment: priority(1-10)}
    # priority 1 = most wanted, weight = 11 - priority

    # Set by allocator
    section: Optional[str] = None

    def preference_weight(self, other_enrollment: str) -> float:
        """Weight for wanting to be with another student. Higher = stronger."""
        p = self.preferences.get(other_enrollment)
        return (11 - p) if p is not None else 0.0

    def to_dict(self) -> dict:
        return {
            "enrollment": self.enrollment,
            "name": self.name,
            "cgpa": self.cgpa,
            "rank": self.rank,
            "tier": self.tier,
            "rank_points": self.rank_points,
            "section": self.section,
            "preferences": self.preferences,
        }
