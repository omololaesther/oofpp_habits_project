"""High-level orchestrator: glues :class:`Habit` to :class:`DatabaseManager`.

This is the only public API the UI layers (CLI, future GUI/web) need to
know about.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from .database import DatabaseManager
from .habit import Habit, Periodicity


class HabitTracker:
    """User-facing API for creating, checking off, and inspecting habits."""

    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    # ------------------------------------------------------------- CRUD
    def add_habit(self, name: str, task: str, periodicity) -> Habit:
        """Create a new habit and persist it.

        ``periodicity`` may be either a :class:`Periodicity` value or a
        string ("daily" / "weekly") — both forms are accepted to keep the
        CLI code small.
        """
        if isinstance(periodicity, str):
            periodicity = Periodicity.from_str(periodicity)
        if self.db.get_habit_by_name(name) is not None:
            raise ValueError(f"A habit named {name!r} already exists.")
        habit = Habit(name=name, task=task, periodicity=periodicity)
        self.db.insert_habit(habit)
        return habit

    def delete_habit(self, name: str) -> bool:
        return self.db.delete_habit_by_name(name)

    def edit_habit(self, name: str, task: Optional[str] = None,
                   periodicity: Optional[str] = None) -> Habit:
        """Update an existing habit's task and/or periodicity."""
        if isinstance(periodicity, str):
            Periodicity.from_str(periodicity)  # raises if the value is invalid
        if self.get_habit(name) is None:
            raise KeyError(f"No habit named {name!r}.")
        self.db.update_habit(name, task=task, periodicity=periodicity)
        return self.get_habit(name)

    def get_habit(self, name: str) -> Optional[Habit]:
        return self.db.get_habit_by_name(name)

    def list_habits(self) -> List[Habit]:
        return self.db.fetch_all_habits()

    # ---------------------------------------------------------- behaviour
    def check_off(self, name: str, when: Optional[datetime] = None) -> Habit:
        """Mark a habit as completed and persist the new event."""
        habit = self.get_habit(name)
        if habit is None:
            raise KeyError(f"No habit named {name!r}.")
        ts = habit.complete_task(when)
        self.db.insert_completion(habit.habit_id, ts)
        return habit
