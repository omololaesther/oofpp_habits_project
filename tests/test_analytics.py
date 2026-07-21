"""Unit tests for the functional analytics module."""
from habit_tracker import analytics
from habit_tracker.habit import Periodicity


def test_list_all_returns_all(seeded_tracker):
    habits = seeded_tracker.list_habits()
    assert len(analytics.list_all(habits)) == 5


def test_filter_by_period_daily(seeded_tracker):
    habits = seeded_tracker.list_habits()
    daily = analytics.filter_by_period(habits, Periodicity.DAILY)
    assert len(daily) == 3
    assert all(h.periodicity is Periodicity.DAILY for h in daily)


def test_filter_by_period_weekly(seeded_tracker):
    habits = seeded_tracker.list_habits()
    weekly = analytics.filter_by_period(habits, "weekly")
    assert len(weekly) == 2
    assert {h.name for h in weekly} == {"workout", "review_finances"}


def test_longest_streak_all_picks_perfect(seeded_tracker):
    habits = seeded_tracker.list_habits()
    name, streak = analytics.longest_streak_all(habits)
    # drink_water has the perfect 28-day streak
    assert name == "drink_water"
    assert streak == 28


def test_longest_streak_for_single(seeded_tracker):
    habits = {h.name: h for h in seeded_tracker.list_habits()}
    assert analytics.longest_streak_for(habits["drink_water"]) == 28
    # 'read' missed days 5 and 12, so the longest run is 7 days (day 6..12 broken,
    # but day 13..28 minus skips form longer runs)
    assert analytics.longest_streak_for(habits["read"]) >= 5


def test_summary_dashboard(seeded_tracker):
    habits = seeded_tracker.list_habits()
    s = analytics.summary(habits)
    assert s["total"] == 5
    assert s["daily"] == 3
    assert s["weekly"] == 2
    assert s["longest"][1] == 28


def test_analytics_on_empty():
    assert analytics.list_all([]) == []
    assert analytics.longest_streak_all([]) == ("", 0)

def test_struggled_most_sorts_by_misses(seeded_tracker):
    habits = seeded_tracker.list_habits()
    results = analytics.struggled_most(habits, within_days=28)
    assert len(results) == 5
    # Results must be sorted with the most-missed habit first.
    misses = [count for _, count in results]
    assert misses == sorted(misses, reverse=True)
    # 'meditate' skips every other day in the fixture data, so it should
    # have more missed periods than any other predefined habit.
    assert results[0][0] == "meditate"
