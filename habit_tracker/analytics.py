"""Functional analytics over a list of :class:`Habit` objects.

Every function in this module is a *pure function*: it takes the data it
needs as arguments and returns a value, with no side-effects.  This is
deliberate — it makes the analytics layer trivially testable and lets
us compose new analyses out of existing ones.

The implementation leans on :func:`filter`, :func:`map`,
:func:`functools.reduce`, :func:`max` (with a ``key`` callable) and
lambdas to keep the functional-programming paradigm explicit.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from functools import reduce
from typing import Iterable, List, Tuple, Union

from .habit import Habit, Periodicity


# ----------------------------------------------------------------- listings
def list_all(habits: Iterable[Habit]) -> List[Habit]:
    """Return all currently tracked habits as a list."""
    return list(habits)


def filter_by_period(habits: Iterable[Habit],
                     periodicity: Union[Periodicity, str]) -> List[Habit]:
    """Return only the habits matching the given periodicity."""
    if isinstance(periodicity, str):
        periodicity = Periodicity.from_str(periodicity)
    return list(filter(lambda h: h.periodicity is periodicity, habits))


# --------------------------------------------------------------- streaks
def longest_streak_all(habits: Iterable[Habit]) -> Tuple[str, int]:
    """Return the (habit_name, streak_length) pair with the longest streak.

    Implemented with ``reduce`` for the explicit FP demonstration.
    """
    pairs = list(map(lambda h: (h.name, h.longest_streak()), habits))
    if not pairs:
        return ("", 0)
    return reduce(lambda acc, x: x if x[1] > acc[1] else acc, pairs)


def longest_streak_for(habit: Habit) -> int:
    """Return the longest run streak for a single habit."""
    return habit.longest_streak()


# --------------------------------------------------------------- struggles
def struggled_most(habits: Iterable[Habit],
                   within_days: int = 30) -> List[Tuple[str, int]]:
    """Habits the user struggled with most recently.

    "Struggle" is defined as the number of *missed* periods in the
    trailing ``within_days`` window.  The list is sorted descending.
    """
    cutoff = datetime.now() - timedelta(days=within_days)

    def missed(h: Habit) -> int:
        # Count expected periods since the cutoff that have no completion.
        completed_keys = {h._period_key(ts) for ts in h.completions
                          if ts >= cutoff}
        step = h.periodicity.delta()
        ref = cutoff
        expected = 0
        misses = 0
        now = datetime.now()
        while ref <= now:
            expected += 1
            if h._period_key(ref) not in completed_keys:
                misses += 1
            ref += step
        return misses

    scored = list(map(lambda h: (h.name, missed(h)), habits))
    return sorted(scored, key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------- summary
def summary(habits: Iterable[Habit]) -> dict:
    """One-shot dashboard summary built entirely from the pure functions above."""
    habits = list(habits)
    return {
        "total":   len(list_all(habits)),
        "daily":   len(filter_by_period(habits, Periodicity.DAILY)),
        "weekly":  len(filter_by_period(habits, Periodicity.WEEKLY)),
        "longest": longest_streak_all(habits),
    }
