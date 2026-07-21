"""Unit tests for HabitTracker."""
import pytest

from habit_tracker.habit import Periodicity


def test_add_then_get(tracker):
    tracker.add_habit("water", "drink water", "daily")
    h = tracker.get_habit("water")
    assert h is not None
    assert h.periodicity is Periodicity.DAILY


def test_add_duplicate_raises(tracker):
    tracker.add_habit("water", "drink water", "daily")
    with pytest.raises(ValueError):
        tracker.add_habit("water", "anything", "weekly")


def test_check_off_creates_completion(tracker):
    tracker.add_habit("water", "drink water", "daily")
    h = tracker.check_off("water")
    assert len(h.completions) == 1


def test_check_off_unknown_raises(tracker):
    with pytest.raises(KeyError):
        tracker.check_off("does_not_exist")


def test_list_habits_after_seed(seeded_tracker):
    habits = seeded_tracker.list_habits()
    assert len(habits) == 5
    names = {h.name for h in habits}
    assert "drink_water" in names
    assert "workout" in names

def test_delete_habit_removes_it(tracker):
    tracker.add_habit("water", "drink water", "daily")
    assert tracker.delete_habit("water") is True
    assert tracker.get_habit("water") is None


def test_delete_unknown_habit_returns_false(tracker):
    assert tracker.delete_habit("does_not_exist") is False


def test_edit_habit_changes_task(tracker):
    tracker.add_habit("water", "drink water", "daily")
    tracker.check_off("water")
    updated = tracker.edit_habit("water", task="drink more water")
    assert updated.task == "drink more water"
    assert len(updated.completions) == 1  # history preserved


def test_edit_unknown_habit_raises(tracker):
    with pytest.raises(KeyError):
        tracker.edit_habit("does_not_exist", task="anything")