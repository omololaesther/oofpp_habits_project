"""Predefined habits + four weeks of completion fixture data.

This module fulfils two acceptance criteria at once:

* It seeds the database with at least 5 predefined habits (mix of daily
  and weekly) on first launch.
* It exposes the same data as a test fixture for the unit-test suite.

Keeping the dummy data in one place means production seeding and tests
can never drift apart.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from .habit import Habit, Periodicity
from .tracker import HabitTracker

# Anchor "today" four weeks ago so the seeded data spans exactly the
# required 28-day window ending at the import moment.
_TODAY = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
_WEEKS = 4
_DAYS = _WEEKS * 7  # 28


def _daily_completions(skip_days=()):
    """28 daily timestamps, optionally with some days skipped to make the
    streak data realistic."""
    return [
        _TODAY - timedelta(days=d)
        for d in range(_DAYS)
        if d not in skip_days
    ]


def _weekly_completions(skip_weeks=()):
    """4 weekly timestamps (one per week of the 28-day window)."""
    return [
        _TODAY - timedelta(days=7 * w)
        for w in range(_WEEKS)
        if w not in skip_weeks
    ]


# ----------------------------------------------------------- definitions
def predefined_habits() -> List[Habit]:
    """Return the five predefined habits with attached fixture data."""
    habits: List[Habit] = []

    # 1. Drink water — perfect daily streak (28 days)
    h = Habit("drink_water", "Drink 2 litres of water",
              Periodicity.DAILY,
              created_at=_TODAY - timedelta(days=_DAYS))
    h.completions = _daily_completions()
    habits.append(h)

    # 2. Read — daily, with two missed days (broke streak)
    h = Habit("read", "Read for 20 minutes",
              Periodicity.DAILY,
              created_at=_TODAY - timedelta(days=_DAYS))
    h.completions = _daily_completions(skip_days=(5, 12))
    habits.append(h)

    # 3. Meditate — daily, sporadic (every other day)
    h = Habit("meditate", "Meditate for 10 minutes",
              Periodicity.DAILY,
              created_at=_TODAY - timedelta(days=_DAYS))
    h.completions = _daily_completions(skip_days=tuple(range(1, _DAYS, 2)))
    habits.append(h)

    # 4. Workout — weekly, perfect 4-week streak
    h = Habit("workout", "Go to the gym",
              Periodicity.WEEKLY,
              created_at=_TODAY - timedelta(days=_DAYS))
    h.completions = _weekly_completions()
    habits.append(h)

    # 5. Review finances — weekly, missed one week
    h = Habit("review_finances", "Review monthly budget and expenses",
              Periodicity.WEEKLY,
              created_at=_TODAY - timedelta(days=_DAYS))
    h.completions = _weekly_completions(skip_weeks=(2,))
    habits.append(h)

    return habits


def seed_if_empty(tracker: HabitTracker) -> int:
    """Insert the predefined habits into the database iff it is empty.

    Returns the number of habits inserted.
    """
    if not tracker.db.is_empty():
        return 0
    for habit in predefined_habits():
        tracker.db.insert_habit(habit)
    return 5
