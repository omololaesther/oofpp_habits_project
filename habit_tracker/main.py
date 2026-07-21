"""Application entry point.

Run with::

    python -m habit_tracker.main
"""
from .cli import CLI
from .database import DatabaseManager
from .fixtures import seed_if_empty
from .tracker import HabitTracker


def main() -> None:
    db = DatabaseManager("habits.db")
    tracker = HabitTracker(db)
    inserted = seed_if_empty(tracker)
    if inserted:
        print(f"🌱 Seeded database with {inserted} predefined habits.")
    try:
        CLI(tracker).run()
    finally:
        db.close()


if __name__ == "__main__":
    main()
