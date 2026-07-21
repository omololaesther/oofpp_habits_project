"""Domain model: the Habit class and the Periodicity enum.

This module is intentionally independent of storage and UI layers, so the
domain logic can be unit-tested in isolation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from enum import Enum
from typing import List, Optional


class Periodicity(Enum):
    """Allowed habit periodicities.

    Using an enum (rather than free-form strings) prevents typos at the
    boundary and gives us a single place to attach period-related helpers.
    """
    DAILY = "daily"
    WEEKLY = "weekly"

    def delta(self) -> timedelta:
        """Length of a single period as a timedelta."""
        return timedelta(days=1) if self is Periodicity.DAILY else timedelta(days=7)

    @classmethod
    def from_str(cls, value: str) -> "Periodicity":
        """Parse a periodicity from a (case-insensitive) string."""
        try:
            return cls(value.lower().strip())
        except ValueError as exc:
            raise ValueError(
                f"Unknown periodicity {value!r}. "
                f"Expected one of: {[p.value for p in cls]}"
            ) from exc


@dataclass
class Habit:
    """A habit a user wants to track.

    A habit owns its identity (``name``), a human-readable ``task``,
    a ``periodicity`` and the ``completions`` event log — the list of
    timestamps at which the task was checked off.

    Attributes
    ----------
    name : str
        Short, unique name used as the habit's user-facing identifier.
    task : str
        Free-form description of what the user has to do.
    periodicity : Periodicity
        How often the habit must be completed.
    created_at : datetime
        When the habit was added to the system.
    completions : list[datetime]
        Event log of every check-off, ordered by insertion.
    habit_id : int | None
        Database primary key (None until persisted).
    """

    name: str
    task: str
    periodicity: Periodicity
    created_at: datetime = field(default_factory=datetime.now)
    completions: List[datetime] = field(default_factory=list)
    habit_id: Optional[int] = None

    # ---------------------------------------------------------------- mutation
    def complete_task(self, when: Optional[datetime] = None) -> datetime:
        """Mark this habit as completed.

        Parameters
        ----------
        when : datetime, optional
            Timestamp for the completion; defaults to "now".

        Returns
        -------
        datetime
            The timestamp that was actually appended to the event log.
        """
        ts = when or datetime.now()
        self.completions.append(ts)
        return ts

    # --------------------------------------------------------------- inspection
    def _period_key(self, ts: datetime):
        """Return a hashable key identifying which period ``ts`` falls in.

        For daily habits this is the calendar date; for weekly habits this
        is an ISO (year, week) pair.
        """
        if self.periodicity is Periodicity.DAILY:
            return ts.date()
        iso = ts.isocalendar()
        return (iso[0], iso[1])  # (iso_year, iso_week)

    def completed_periods(self) -> List:
        """Sorted, de-duplicated list of period-keys in which the habit was checked off."""
        return sorted({self._period_key(ts) for ts in self.completions})

    def is_completed_in_period(self, ref: Optional[datetime] = None) -> bool:
        """Was the habit checked off in the period containing ``ref``?"""
        ref = ref or datetime.now()
        return self._period_key(ref) in {self._period_key(ts) for ts in self.completions}

    def is_broken(self, ref: Optional[datetime] = None) -> bool:
        """A habit is "broken" if its previous period had no completion.

        We deliberately do not check the *current* period — the user may
        still complete it before the period ends.
        """
        ref = ref or datetime.now()
        prev = ref - self.periodicity.delta()
        return not self.is_completed_in_period(prev) and len(self.completions) > 0

    # ---------------------------------------------------------- streak analysis
    def _expected_next(self, period_key):
        """Given a period key, return the key of the period immediately after it."""
        if self.periodicity is Periodicity.DAILY:
            return period_key + timedelta(days=1)
        # ISO week tuple — advance via a real date one week later.
        y, w = period_key
        anchor = date.fromisocalendar(y, w, 1) + timedelta(days=7)
        iso = anchor.isocalendar()
        return (iso[0], iso[1])

    def longest_streak(self) -> int:
        """Longest run of consecutive completed periods, ever."""
        periods = self.completed_periods()
        if not periods:
            return 0
        best = current = 1
        for i in range(1, len(periods)):
            if periods[i] == self._expected_next(periods[i - 1]):
                current += 1
                best = max(best, current)
            else:
                current = 1
        return best

    def current_streak(self, ref: Optional[datetime] = None) -> int:
        """Current ongoing streak, counted backwards from the latest period."""
        ref = ref or datetime.now()
        periods = set(self.completed_periods())
        if not periods:
            return 0
        # Walk backwards from the current period.
        key = self._period_key(ref)
        if key not in periods:
            # Maybe user hasn't done it this period yet — start from previous.
            key = self._previous_key(key)
            if key not in periods:
                return 0
        streak = 0
        while key in periods:
            streak += 1
            key = self._previous_key(key)
        return streak

    def _previous_key(self, period_key):
        if self.periodicity is Periodicity.DAILY:
            return period_key - timedelta(days=1)
        y, w = period_key
        anchor = date.fromisocalendar(y, w, 1) - timedelta(days=7)
        iso = anchor.isocalendar()
        return (iso[0], iso[1])

    # -------------------------------------------------------------- serialise
    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"{self.name} ({self.periodicity.value}) — {len(self.completions)} check-offs"
