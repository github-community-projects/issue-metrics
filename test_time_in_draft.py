"""A test suite for the measure_time_in_draft function."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytz
from time_in_draft import get_stats_time_in_draft, measure_time_in_draft


class TestMeasureTimeInDraft(unittest.TestCase):
    """
    Unit tests for the measure_time_in_draft function.
    """

    def setUp(self):
        """
        Setup common test data and mocks.
        """
        self.issue = MagicMock()
        self.issue.state = "open"

    def test_time_in_draft_with_ready_for_review(self):
        """
        Test measure_time_in_draft with one draft and review interval.
        """
        self.issue.get_events.return_value = [
            MagicMock(
                event="convert_to_draft",
                created_at=datetime(2021, 1, 1, tzinfo=pytz.utc),
            ),
            MagicMock(
                event="ready_for_review",
                created_at=datetime(2021, 1, 3, tzinfo=pytz.utc),
            ),
        ]
        result = measure_time_in_draft(self.issue)
        expected = timedelta(days=2)
        self.assertEqual(result, expected, "The time in draft should be 2 days.")

    def test_time_in_draft_without_ready_for_review(self):
        """
        Test measure_time_in_draft when ready_for_review_at is not provided and issue is still open.
        """
        self.issue.get_events.return_value = [
            MagicMock(
                event="convert_to_draft",
                created_at=datetime(2021, 1, 1, tzinfo=pytz.utc),
            ),
        ]
        now = datetime(2021, 1, 4, tzinfo=pytz.utc)
        with unittest.mock.patch("time_in_draft.datetime") as mock_datetime:
            mock_datetime.now.return_value = now
            result = measure_time_in_draft(self.issue)
            expected = timedelta(days=3)
            self.assertEqual(result, expected, "The time in draft should be 3 days.")

    def test_time_in_draft_multiple_intervals(self):
        """
        Test measure_time_in_draft with multiple draft intervals.
        """
        self.issue.get_events.return_value = [
            MagicMock(
                event="convert_to_draft",
                created_at=datetime(2021, 1, 1, tzinfo=pytz.utc),
            ),
            MagicMock(
                event="ready_for_review",
                created_at=datetime(2021, 1, 3, tzinfo=pytz.utc),
            ),
            MagicMock(
                event="convert_to_draft",
                created_at=datetime(2021, 1, 5, tzinfo=pytz.utc),
            ),
            MagicMock(
                event="ready_for_review",
                created_at=datetime(2021, 1, 7, tzinfo=pytz.utc),
            ),
        ]
        result = measure_time_in_draft(self.issue)
        expected = timedelta(days=4)
        self.assertEqual(result, expected, "The total time in draft should be 4 days.")

    def test_time_in_draft_ongoing_draft(self):
        """
        Test measure_time_in_draft with an ongoing draft interval.
        """
        self.issue.get_events.return_value = [
            MagicMock(
                event="convert_to_draft",
                created_at=datetime(2021, 1, 1, tzinfo=pytz.utc),
            ),
        ]
        with unittest.mock.patch("time_in_draft.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2021, 1, 4, tzinfo=pytz.utc)
            result = measure_time_in_draft(self.issue)
            expected = timedelta(days=3)
            self.assertEqual(
                result, expected, "The ongoing draft time should be 3 days."
            )

    def test_time_in_draft_no_draft_events(self):
        """
        Test measure_time_in_draft with no draft-related events.
        """
        self.issue.get_events.return_value = []
        self.issue.as_pull_request.return_value.draft = False
        result = measure_time_in_draft(self.issue)
        self.assertIsNone(
            result, "The result should be None when there are no draft events."
        )

    def test_time_in_draft_without_ready_for_review_and_closed(self):
        """
        Test measure_time_in_draft for a closed issue with an ongoing draft and ready_for_review_at is not provided.
        """
        self.issue.get_events.return_value = [
            MagicMock(
                event="convert_to_draft",
                created_at=datetime(2021, 1, 1, tzinfo=pytz.utc),
            ),
        ]
        self.issue.state = "closed"
        result = measure_time_in_draft(self.issue)
        self.assertIsNone(
            result,
            "The result should be None for a closed issue with an ongoing draft.",
        )

    def test_time_in_draft_initially_created_as_draft(self):
        """
        Test measure_time_in_draft with a PR initially created as draft.
        """
        # Set up issue created_at time
        self.issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.utc)

        # Mock events with only ready_for_review (no convert_to_draft)
        self.issue.get_events.return_value = [
            MagicMock(
                event="ready_for_review",
                created_at=datetime(2021, 1, 3, tzinfo=pytz.utc),
            ),
        ]

        # Mock pull request object
        mock_pull_request = MagicMock()

        result = measure_time_in_draft(self.issue, mock_pull_request)
        expected = timedelta(days=2)
        self.assertEqual(
            result,
            expected,
            "The time in draft should be 2 days for initially draft PR.",
        )

    def test_time_in_draft_initially_created_as_draft_still_open(self):
        """
        Test measure_time_in_draft with a PR initially created as draft and still in draft.
        """
        # Set up issue created_at time
        self.issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.utc)

        # Mock events with no ready_for_review events (still draft)
        self.issue.get_events.return_value = []

        # Mock pull request object indicating it's currently draft
        mock_pull_request = MagicMock()
        mock_pull_request.draft = True

        with unittest.mock.patch("time_in_draft.datetime") as mock_datetime:
            # Keep the real datetime class but only mock the now() method
            mock_datetime.fromisoformat = datetime.fromisoformat
            mock_datetime.now.return_value = datetime(2021, 1, 4, tzinfo=pytz.utc)
            result = measure_time_in_draft(self.issue, mock_pull_request)
            expected = timedelta(days=3)
            self.assertEqual(
                result,
                expected,
                "The time in draft should be 3 days for initially draft PR still in draft.",
            )

    def test_time_in_draft_with_attribute_error_scenario(self):
        """
        Test measure_time_in_draft to ensure it doesn't raise AttributeError when called
        with issue structure similar to what get_per_issue_metrics passes.
        This test reproduces the original bug scenario.
        """
        # This simulates the actual issue structure passed from get_per_issue_metrics
        issue = MagicMock()
        issue.state = "open"
        issue.get_events.return_value = [
            MagicMock(
                event="convert_to_draft",
                created_at=datetime(2021, 1, 1, tzinfo=pytz.utc),
            ),
        ]

        # This should NOT raise AttributeError: events
        with unittest.mock.patch("time_in_draft.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2021, 1, 4, tzinfo=pytz.utc)
            result = measure_time_in_draft(issue)
            expected = timedelta(days=3)
            self.assertEqual(result, expected, "The time in draft should be 3 days.")

    def test_time_in_draft_with_iterator_events(self):
        """
        Test measure_time_in_draft with events() returning an iterator instead of a list.
        This test ensures the function works correctly when get_events() returns an iterator
        (as it does in the real GitHub API), which can only be consumed once.
        """
        # Set up issue created_at time
        self.issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.utc)

        # Create an iterator of events (simulating real GitHub API behavior)
        def events_iterator():
            return iter(
                [
                    MagicMock(
                        event="convert_to_draft",
                        created_at=datetime(2021, 1, 1, tzinfo=pytz.utc),
                    ),
                    MagicMock(
                        event="ready_for_review",
                        created_at=datetime(2021, 1, 3, tzinfo=pytz.utc),
                    ),
                ]
            )

        self.issue.get_events = events_iterator

        result = measure_time_in_draft(self.issue)
        expected = timedelta(days=2)
        self.assertEqual(
            result,
            expected,
            "The time in draft should be 2 days when get_events() returns an iterator.",
        )

    def test_time_in_draft_attribute_error_in_pr_detection(self):
        """
        Test measure_time_in_draft when as_pull_request raises AttributeError.
        Falls back to event-based logic only.
        """
        self.issue.get_events.return_value = [
            MagicMock(
                event="convert_to_draft",
                created_at=datetime(2021, 1, 1, tzinfo=pytz.utc),
            ),
            MagicMock(
                event="ready_for_review",
                created_at=datetime(2021, 1, 3, tzinfo=pytz.utc),
            ),
        ]
        self.issue.as_pull_request.side_effect = AttributeError("no PR")

        result = measure_time_in_draft(self.issue)
        expected = timedelta(days=2)
        self.assertEqual(result, expected)


class TestGetStatsTimeInDraft(unittest.TestCase):
    """
    Unit tests for the get_stats_time_in_draft function.
    """

    def test_get_stats_time_in_draft_with_data(self):
        """
        Test get_stats_time_in_draft with valid draft times.
        """
        issues = [
            MagicMock(time_in_draft=timedelta(days=1)),
            MagicMock(time_in_draft=timedelta(days=2)),
            MagicMock(time_in_draft=timedelta(days=3)),
        ]

        result = get_stats_time_in_draft(issues)
        expected = {
            "avg": timedelta(days=2),
            "med": timedelta(days=2),
            "90p": timedelta(days=2, seconds=69120),
        }

        self.assertEqual(
            result, expected, "The statistics for time in draft are incorrect."
        )

    def test_get_stats_time_in_draft_no_data(self):
        """
        Test get_stats_time_in_draft with no draft times.
        """
        issues = [
            MagicMock(time_in_draft=None),
            MagicMock(time_in_draft=None),
        ]

        result = get_stats_time_in_draft(issues)
        self.assertIsNone(
            result, "The result should be None when there are no draft times."
        )

    def test_get_stats_time_in_draft_empty_list(self):
        """
        Test get_stats_time_in_draft with an empty list of issues.
        """
        issues = []

        result = get_stats_time_in_draft(issues)
        self.assertIsNone(
            result, "The result should be None when the list of issues is empty."
        )


if __name__ == "__main__":
    unittest.main()
