"""Unit tests for the Habit domain class."""
from datetime import datetime, timedelta

import pytest

from habit_tracker.habit import Habit, Periodicity


def test_periodicity_from_string():
    assert Periodicity.from_str("DAILY") is Periodicity.DAILY
    assert Periodicity.from_str("weekly") is Periodicity.WEEKLY


def test_periodicity_invalid_raises():
    with pytest.raises(ValueError):
        Periodicity.from_str("yearly")


def test_complete_task_records_timestamp():
    h = Habit("water", "drink water", Periodicity.DAILY)
    ts = h.complete_task()
    assert ts in h.completions
    assert len(h.completions) == 1


def test_is_completed_in_period():
    h = Habit("water", "drink water", Periodicity.DAILY)
    now = datetime(2025, 1, 10, 9, 0)
    h.complete_task(now)
    assert h.is_completed_in_period(now)
    assert not h.is_completed_in_period(now + timedelta(days=1))


def test_longest_streak_perfect_week():
    h = Habit("water", "drink water", Periodicity.DAILY)
    base = datetime(2025, 1, 1)
    for d in range(7):
        h.complete_task(base + timedelta(days=d))
    assert h.longest_streak() == 7


def test_longest_streak_with_gap():
    h = Habit("water", "drink water", Periodicity.DAILY)
    base = datetime(2025, 1, 1)
    # 3-day streak, gap, then 2-day streak
    for d in [0, 1, 2, 5, 6]:
        h.complete_task(base + timedelta(days=d))
    assert h.longest_streak() == 3


def test_longest_streak_weekly():
    h = Habit("gym", "go to gym", Periodicity.WEEKLY)
    base = datetime(2025, 1, 6)  # a Monday
    for w in range(4):
        h.complete_task(base + timedelta(weeks=w))
    assert h.longest_streak() == 4


def test_no_completions_means_zero_streak():
    h = Habit("water", "drink water", Periodicity.DAILY)
    assert h.longest_streak() == 0
    assert h.current_streak() == 0


def test_is_broken_when_previous_period_missed():
    h = Habit("water", "drink water", Periodicity.DAILY)
    # Completed only 3 days ago, never since
    h.complete_task(datetime.now() - timedelta(days=3))
    assert h.is_broken() is True
