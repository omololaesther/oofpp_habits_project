"""Interactive command-line interface for the habit tracker.

The CLI is intentionally kept *thin* — every menu branch calls exactly
one method on :class:`HabitTracker`.  This means a future Tkinter/Flask
front-end can re-use the same orchestrator without changes.
"""
from __future__ import annotations

from datetime import datetime

from . import analytics
from .habit import Periodicity
from .tracker import HabitTracker


MENU = """
┌──────────────────────────────────────────┐
│           HABIT TRACKER  v0.2            │
├──────────────────────────────────────────┤
│  1. Create a new habit                   │
│  2. Check off (complete) a habit         │
│  3. List all habits                      │
│  4. Delete a habit                       │
│  5. Analytics                            │
│  6. Edit a habit                         │
│  0. Exit                                 │
└──────────────────────────────────────────┘
"""


def _prompt(text: str) -> str:
    return input(text).strip()


class CLI:
    """Interactive REPL on top of a :class:`HabitTracker`."""

    def __init__(self, tracker: HabitTracker) -> None:
        self.tracker = tracker

    # ---------------------------------------------------------- main loop
    def run(self) -> None:
        while True:
            print(MENU)
            choice = _prompt("Select an option: ")
            actions = {
                "1": self.create_habit,
                "2": self.check_off_habit,
                "3": self.list_habits,
                "4": self.delete_habit,
                "5": self.analytics_menu,
                "6": self.edit_habit,
                "0": self.exit_app,
            }
            handler = actions.get(choice)
            if handler is None:
                print("⚠️  Invalid option.\n")
                continue
            try:
                if handler() == "exit":
                    return
            except Exception as exc:                          # noqa: BLE001
                print(f"❌ {exc}\n")

    # ----------------------------------------------------------- branches
    def create_habit(self):
        name = _prompt("  Name (one word, e.g. 'meditate'): ")
        task = _prompt("  Task description: ")
        period = _prompt("  Periodicity [daily/weekly]: ")
        habit = self.tracker.add_habit(name, task, period)
        print(f"✓ Created {habit}\n")

    def check_off_habit(self):
        name = _prompt("  Which habit did you complete? ")
        habit = self.tracker.check_off(name)
        print(f"✓ Logged completion for '{habit.name}' "
              f"at {datetime.now():%Y-%m-%d %H:%M}\n")

    def list_habits(self):
        habits = self.tracker.list_habits()
        if not habits:
            print("  (no habits tracked yet)\n")
            return
        print(f"\n  {'NAME':<20}{'PERIOD':<10}{'STREAK':<10}{'TASK'}")
        print(f"  {'-'*20}{'-'*10}{'-'*10}{'-'*30}")
        for h in habits:
            print(f"  {h.name:<20}{h.periodicity.value:<10}"
                  f"{h.current_streak():<10}{h.task}")
        print()

    def delete_habit(self):
        name = _prompt("  Habit to delete: ")
        if self.tracker.delete_habit(name):
            print(f"✓ Deleted '{name}'\n")
        else:
            print(f"⚠️  No habit named '{name}'\n")

    def edit_habit(self):
        name = _prompt("  Habit to edit: ")
        task = _prompt("  New task (leave blank to keep current): ").strip()
        period = _prompt("  New periodicity [daily/weekly] (leave blank to keep current): ").strip()
        habit = self.tracker.edit_habit(
            name,
            task=task or None,
            periodicity=period or None,
        )
        print(f"✓ Updated {habit}\n")

    def analytics_menu(self):
        habits = self.tracker.list_habits()
        if not habits:
            print("  (no habits to analyse)\n")
            return
        print("\n  ── ANALYTICS ──")
        print("  a) All currently tracked habits")
        print("  b) Habits with the same periodicity")
        print("  c) Longest run streak (all habits)")
        print("  d) Longest run streak for a given habit")
        print("  e) Habits you struggled most with (last 30 days)")
        choice = _prompt("  Choose: ").lower()
        if choice == "a":
            for h in analytics.list_all(habits):
                print(f"   • {h}")
        elif choice == "b":
            period = _prompt("  Periodicity [daily/weekly]: ")
            for h in analytics.filter_by_period(habits, period):
                print(f"   • {h}")
        elif choice == "c":
            name, streak = analytics.longest_streak_all(habits)
            print(f"   🏆 {name}: {streak} consecutive periods")
        elif choice == "d":
            name = _prompt("  Habit name: ")
            habit = self.tracker.get_habit(name)
            if habit is None:
                print(f"   ⚠️  No habit named {name!r}")
            else:
                print(f"   🏆 {name}: {analytics.longest_streak_for(habit)} periods")
        elif choice == "e":
            for name, misses in analytics.struggled_most(habits)[:5]:
                print(f"   • {name}: {misses} missed periods")
        else:
            print("  ⚠️  Invalid option.")
        print()

    def exit_app(self):
        print("Goodbye! 👋")
        return "exit"
