"""Unit tests for the time_to_first_review module."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from time_to_first_review import measure_time_to_first_review


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
