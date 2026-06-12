"""A module containing unit tests for the time_to_close module.

This module contains unit tests for the measure_time_to_close and
get_stats_time_to_close functions in the time_to_close module.
The tests use mock GitHub issues to test the functions' behavior.

Classes:
    TestMeasureTimeToClose: A class to test the measure_time_to_close function.
    TestGetStatsTimeToClose: A class to test the get_stats_time_to_close function.

"""

import unittest
from datetime import timedelta
from unittest.mock import MagicMock

from classes import IssueWithMetrics
from time_to_close import get_stats_time_to_close, measure_time_to_close


class TestGetAverageTimeToClose(unittest.TestCase):
    """Test suite for the get_stats_time_to_close function."""

    def test_get_stats_time_to_close(self):
        """Test that the function correctly calculates the average time to close."""
        # Create mock data
        issues_with_metrics = [
            IssueWithMetrics(
                "Issue 1",
                "https://github.com/user/repo/issues/1",
                "alice",
                None,
                timedelta(days=2),
            ),
            IssueWithMetrics(
                "Issue 2",
                "https://github.com/user/repo/issues/2",
                "bob",
                None,
                timedelta(days=4),
            ),
            IssueWithMetrics(
                "Issue 3", "https://github.com/user/repo/issues/3", "carol", None, None
            ),
        ]

        # Call the function and check the result
        result = get_stats_time_to_close(issues_with_metrics)["avg"]
        expected_result = timedelta(days=3)
        self.assertEqual(result, expected_result)

    def test_get_stats_time_to_close_no_issues(self):
        """Test that the function returns None if there are no issues with time to close."""
        # Create mock data
        issues_with_metrics = [
            IssueWithMetrics(
                "Issue 1", "https://github.com/user/repo/issues/1", "alice", None, None
            ),
            IssueWithMetrics(
                "Issue 2", "https://github.com/user/repo/issues/2", "bob", None, None
            ),
            IssueWithMetrics(
                "Issue 3", "https://github.com/user/repo/issues/3", "carol", None, None
            ),
        ]

        # Call the function and check the result
        result = get_stats_time_to_close(issues_with_metrics)
        expected_result = None
        self.assertEqual(result, expected_result)


class TestMeasureTimeToClose(unittest.TestCase):
    """Test suite for the measure_time_to_close function."""

    def test_measure_time_to_close(self):
        """Test that the function correctly measures the time to close an issue."""
        # Create a mock issue object
        issue = MagicMock()
        issue.state = "closed"
        issue.created_at = "2021-01-01T00:00:00Z"
        issue.closed_at = "2021-01-03T00:00:00Z"

        # Call the function and check the result
        result = measure_time_to_close(issue, None)
        expected_result = timedelta(days=2)
        self.assertEqual(result, expected_result)

    def test_measure_time_to_close_returns_none(self):
        """Test that the function returns None if the issue is not closed."""
        # Create a mock issue object
        issue = MagicMock()
        issue.state = "open"

        # Call the function and check that it returns None
        self.assertEqual(None, measure_time_to_close(issue, None))

    def test_measure_time_to_close_discussion(self):
        """
        Test that the function correctly measures the time to close for a discussion.
        """
        # Create an issue dictionary with createdAt and closedAt fields
        issue = {}
        issue["createdAt"] = "2021-01-01T00:00:00Z"
        issue["closedAt"] = "2021-01-03T00:00:00Z"

        # Call the function and check the result
        result = measure_time_to_close(None, issue)
        expected_result = timedelta(days=2)
        self.assertEqual(result, expected_result)


class TestTimeToCloseEdgeCases(unittest.TestCase):
    """Covers measure_time_to_close edge-case returns."""

    def test_discussion_with_no_closed_at_returns_none(self):
        """Discussion with closedAt=None returns None."""

        discussion = {"closedAt": None, "createdAt": "2021-01-01T00:00:00Z"}
        self.assertIsNone(measure_time_to_close(None, discussion))

    def test_neither_issue_nor_discussion_returns_none(self):
        """Final fallback return None when neither input is provided."""

        self.assertIsNone(measure_time_to_close(None, None))
