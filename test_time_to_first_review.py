"""Unit tests for the time_to_first_review module."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from time_to_first_review import (
    get_stats_time_to_first_review,
    measure_time_to_first_review,
)


class TestMeasureTimeToFirstReview(unittest.TestCase):
    """Test the measure_time_to_first_review function."""

    def test_measure_time_to_first_review_basic(self):
        """Test that the function calculates correct review time."""
        mock_issue = MagicMock()
        mock_issue.created_at = "2023-01-01T00:00:00Z"

        mock_review = MagicMock()
        mock_review.submitted_at = datetime.fromisoformat("2023-01-02T00:00:00Z")

        mock_pull_request = MagicMock()
        mock_pull_request.reviews.return_value = [mock_review]

        result = measure_time_to_first_review(mock_issue, mock_pull_request, None, [])
        expected = timedelta(days=1)
        self.assertEqual(result, expected)

    def test_measure_time_to_first_review_no_reviews(self):
        """Test that function returns None if there are no reviews."""
        mock_issue = MagicMock()
        mock_issue.created_at = "2023-01-01T00:00:00Z"

        mock_pull_request = MagicMock()
        mock_pull_request.reviews.return_value = []

        result = measure_time_to_first_review(mock_issue, mock_pull_request, None, [])
        self.assertEqual(result, None)

    def test_measure_time_to_first_review_ignore_pending(self):
        """Test that pending reviews are ignored."""
        mock_issue = MagicMock()
        mock_issue.created_at = "2023-01-01T00:00:00Z"

        pending_review = MagicMock()
        pending_review.submitted_at = None

        valid_review = MagicMock()
        valid_review.submitted_at = datetime.fromisoformat("2023-01-03T00:00:00Z")

        mock_pull_request = MagicMock()
        mock_pull_request.reviews.return_value = [pending_review, valid_review]

        result = measure_time_to_first_review(mock_issue, mock_pull_request, None, [])
        expected = timedelta(days=2)
        self.assertEqual(result, expected)

    def test_get_stats_time_to_first_review_normal(self):
        """Test a normal list of issues with review times."""
        issue1 = MagicMock()
        issue1.time_to_first_review = timedelta(days=1)
        issue2 = MagicMock()
        issue2.time_to_first_review = timedelta(days=3)

        stats = get_stats_time_to_first_review([issue1, issue2])
        self.assertIsNotNone(stats)
        self.assertEqual(stats["avg"], timedelta(days=2))

    def test_get_stats_time_to_first_review_all_none(self):
        """Test a list where all review times are None."""
        issue = MagicMock()
        issue.time_to_first_review = None
        self.assertIsNone(get_stats_time_to_first_review([issue]))

    def test_get_stats_time_to_first_review_empty(self):
        """Test an empty list."""
        self.assertIsNone(get_stats_time_to_first_review([]))

    def test_measure_time_to_first_review_ready_for_review_path(self):
        """Test the ready_for_review_at path (Start time logic)."""
        mock_issue = MagicMock()
        mock_issue.created_at = "2023-01-01T00:00:00Z"
        ready_at = datetime.fromisoformat("2023-01-01T12:00:00Z")

        mock_review = MagicMock()
        mock_review.submitted_at = datetime.fromisoformat("2023-01-01T13:00:00Z")

        mock_pr = MagicMock()
        mock_pr.reviews.return_value = [mock_review]

        result = measure_time_to_first_review(mock_issue, mock_pr, ready_at, [])
        self.assertEqual(result, timedelta(hours=1))

    def test_measure_time_to_first_review_ignore_users(self):
        """Test filtering out a matching reviewer from ignore_users."""
        mock_issue = MagicMock()
        mock_issue.created_at = "2023-01-01T10:00:00Z"

        bad_review = MagicMock()
        bad_review.user.login = "bot-user"
        bad_review.submitted_at = datetime.fromisoformat("2023-01-01T11:00:00Z")

        good_review = MagicMock()
        good_review.user.login = "human-user"
        good_review.submitted_at = datetime.fromisoformat("2023-01-01T12:00:00Z")

        mock_pr = MagicMock()
        mock_pr.reviews.return_value = [bad_review, good_review]

        result = measure_time_to_first_review(mock_issue, mock_pr, None, ["bot-user"])
        self.assertEqual(result, timedelta(hours=2))

    def test_measure_time_to_first_review_type_error_path(self):
        """Test the except TypeError error handling path."""
        mock_issue = MagicMock()
        mock_issue.created_at = "2023-01-01T00:00:00Z"

        mock_pr = MagicMock()
        mock_pr.reviews.side_effect = TypeError("ghost user")

        result = measure_time_to_first_review(mock_issue, mock_pr, None, [])
        self.assertIsNone(result)
