"""Shared pytest fixtures."""
from __future__ import annotations

import pytest

from habit_tracker.database import DatabaseManager
from habit_tracker.fixtures import predefined_habits
from habit_tracker.tracker import HabitTracker


@pytest.fixture()
def in_memory_db():
    """Fresh in-memory SQLite database for each test."""
    db = DatabaseManager(":memory:")
    yield db
    db.close()


@pytest.fixture()
def tracker(in_memory_db):
    return HabitTracker(in_memory_db)


@pytest.fixture()
def seeded_tracker(tracker):
    """Tracker pre-loaded with the five predefined habits + 4 weeks of data."""
    for habit in predefined_habits():
        tracker.db.insert_habit(habit)
    return tracker
