"""SQLite persistence layer.

The :class:`DatabaseManager` is the only place in the codebase that issues
SQL.  Every other layer talks to it through plain Python objects, which
keeps the domain model free of storage concerns.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .habit import Habit, Periodicity

ISO_FMT = "%Y-%m-%d %H:%M:%S"


class DatabaseManager:
    """Thin wrapper around an SQLite database storing habits + completions."""

    def __init__(self, db_path: str = "habits.db") -> None:
        self.db_path = db_path
        # ``check_same_thread=False`` keeps the same connection usable from
        # the test suite as well as a future GUI/Flask app.
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    # ------------------------------------------------------------- schema
    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS habits (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL UNIQUE,
                task        TEXT NOT NULL,
                periodicity TEXT NOT NULL,
                created_at  TEXT NOT NULL
            )"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS completions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id      INTEGER NOT NULL,
                completed_at  TEXT NOT NULL,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
            )"""
        )
        self.conn.commit()

    # ------------------------------------------------------------ habits
    def insert_habit(self, habit: Habit) -> int:
        """Persist a habit and return its new primary key."""
        cur = self.conn.execute(
            "INSERT INTO habits(name, task, periodicity, created_at) VALUES (?,?,?,?)",
            (habit.name, habit.task, habit.periodicity.value,
             habit.created_at.strftime(ISO_FMT)),
        )
        self.conn.commit()
        habit.habit_id = cur.lastrowid
        # Re-persist any completions already attached to the in-memory object.
        for ts in habit.completions:
            self.insert_completion(habit.habit_id, ts)
        return habit.habit_id

    def delete_habit_by_name(self, name: str) -> bool:
        cur = self.conn.execute("DELETE FROM habits WHERE name = ?", (name,))
        self.conn.commit()
        return cur.rowcount > 0

    def update_habit(self, name: str, task: Optional[str] = None,
                     periodicity: Optional[str] = None) -> bool:
        """Update a habit's task and/or periodicity, leaving its completions untouched.

        Only the fields passed in (not ``None``) are changed.
        """
        habit = self.get_habit_by_name(name)
        if habit is None:
            return False
        new_task = task if task is not None else habit.task
        new_period = periodicity if periodicity is not None else habit.periodicity.value
        self.conn.execute(
            "UPDATE habits SET task = ?, periodicity = ? WHERE name = ?",
            (new_task, new_period, name),
        )
        self.conn.commit()
        return True

    def fetch_all_habits(self) -> List[Habit]:
        rows = self.conn.execute(
            "SELECT id, name, task, periodicity, created_at FROM habits"
        ).fetchall()
        habits: List[Habit] = []
        for hid, name, task, period, created in rows:
            h = Habit(
                name=name,
                task=task,
                periodicity=Periodicity.from_str(period),
                created_at=datetime.strptime(created, ISO_FMT),
                habit_id=hid,
            )
            h.completions = self.fetch_completions(hid)
            habits.append(h)
        return habits

    def get_habit_by_name(self, name: str) -> Optional[Habit]:
        row = self.conn.execute(
            "SELECT id, name, task, periodicity, created_at FROM habits WHERE name = ?",
            (name,),
        ).fetchone()
        if not row:
            return None
        hid, name, task, period, created = row
        h = Habit(
            name=name, task=task,
            periodicity=Periodicity.from_str(period),
            created_at=datetime.strptime(created, ISO_FMT),
            habit_id=hid,
        )
        h.completions = self.fetch_completions(hid)
        return h

    # ------------------------------------------------------- completions
    def insert_completion(self, habit_id: int, when: datetime) -> None:
        self.conn.execute(
            "INSERT INTO completions(habit_id, completed_at) VALUES (?,?)",
            (habit_id, when.strftime(ISO_FMT)),
        )
        self.conn.commit()

    def fetch_completions(self, habit_id: int) -> List[datetime]:
        rows = self.conn.execute(
            "SELECT completed_at FROM completions WHERE habit_id = ? ORDER BY completed_at",
            (habit_id,),
        ).fetchall()
        return [datetime.strptime(r[0], ISO_FMT) for r in rows]

    # ------------------------------------------------------------- lifecycle
    def is_empty(self) -> bool:
        (n,) = self.conn.execute("SELECT COUNT(*) FROM habits").fetchone()
        return n == 0

    def close(self) -> None:
        self.conn.close()
