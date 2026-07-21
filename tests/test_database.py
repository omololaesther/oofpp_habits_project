"""Unit tests for DatabaseManager persistence."""
from datetime import datetime

from habit_tracker.habit import Habit, Periodicity


def test_insert_and_fetch_round_trip(in_memory_db):
    h = Habit("water", "drink water", Periodicity.DAILY)
    h.complete_task(datetime(2025, 1, 1, 9, 0))
    in_memory_db.insert_habit(h)

    fetched = in_memory_db.get_habit_by_name("water")
    assert fetched is not None
    assert fetched.name == "water"
    assert fetched.periodicity is Periodicity.DAILY
    assert len(fetched.completions) == 1


def test_unique_name_constraint(in_memory_db):
    import sqlite3
    h1 = Habit("water", "drink water", Periodicity.DAILY)
    in_memory_db.insert_habit(h1)
    h2 = Habit("water", "another", Periodicity.WEEKLY)
    try:
        in_memory_db.insert_habit(h2)
    except sqlite3.IntegrityError:
        return
    assert False, "Expected IntegrityError on duplicate name"


def test_delete_habit_cascades_completions(in_memory_db):
    h = Habit("water", "drink water", Periodicity.DAILY)
    h.complete_task()
    in_memory_db.insert_habit(h)
    assert in_memory_db.delete_habit_by_name("water") is True
    assert in_memory_db.get_habit_by_name("water") is None


def test_is_empty(in_memory_db):
    assert in_memory_db.is_empty() is True
    in_memory_db.insert_habit(Habit("x", "y", Periodicity.DAILY))
    assert in_memory_db.is_empty() is False
