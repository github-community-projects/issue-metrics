"""Tests for the pr_comments module.

This module contains tests for the count_pr_comments and get_stats_pr_comments
functions.
"""

import unittest
from unittest.mock import MagicMock

from classes import IssueWithMetrics
from pr_comments import count_pr_comments, get_stats_pr_comments


class TestCountPRComments(unittest.TestCase):
    """Test the count_pr_comments function."""

    def test_count_pr_comments_with_comments(self):
        """Test counting PR comments with actual comments."""
        # Mock issue with comments
        mock_issue = MagicMock()
        mock_comment1 = MagicMock()
        mock_comment1.user.type = "User"
        mock_comment1.user.login = "user1"
        mock_comment2 = MagicMock()
        mock_comment2.user.type = "User"
        mock_comment2.user.login = "user2"
        mock_issue.get_comments.return_value = [mock_comment1, mock_comment2]

        # Mock pull request with review comments
        mock_pull_request = MagicMock()
        mock_review_comment1 = MagicMock()
        mock_review_comment1.user.type = "User"
        mock_review_comment1.user.login = "user3"
        mock_pull_request.get_review_comments.return_value = [mock_review_comment1]

        result = count_pr_comments(mock_issue, mock_pull_request, [])
        self.assertEqual(result, 3)

    def test_count_pr_comments_with_bots_ignored(self):
        """Test that bot comments are ignored."""
        # Mock issue with bot comment
        mock_issue = MagicMock()
        mock_bot_comment = MagicMock()
        mock_bot_comment.user.type = "Bot"
        mock_bot_comment.user.login = "github-actions[bot]"
        mock_user_comment = MagicMock()
        mock_user_comment.user.type = "User"
        mock_user_comment.user.login = "user1"
        mock_issue.get_comments.return_value = [mock_bot_comment, mock_user_comment]

        mock_pull_request = MagicMock()
        mock_pull_request.get_review_comments.return_value = []

        result = count_pr_comments(mock_issue, mock_pull_request, [])
        self.assertEqual(result, 1)

    def test_count_pr_comments_with_ignored_users(self):
        """Test that ignored users are not counted."""
        # Mock issue with comments from ignored user
        mock_issue = MagicMock()
        mock_comment1 = MagicMock()
        mock_comment1.user.type = "User"
        mock_comment1.user.login = "ignored_user"
        mock_comment2 = MagicMock()
        mock_comment2.user.type = "User"
        mock_comment2.user.login = "regular_user"
        mock_issue.get_comments.return_value = [mock_comment1, mock_comment2]

        mock_pull_request = MagicMock()
        mock_pull_request.get_review_comments.return_value = []

        result = count_pr_comments(mock_issue, mock_pull_request, ["ignored_user"])
        self.assertEqual(result, 1)

    def test_count_pr_comments_no_pull_request(self):
        """Test that None is returned when no pull request is provided."""
        mock_issue = MagicMock()
        result = count_pr_comments(mock_issue, None, [])
        self.assertIsNone(result)

    def test_count_pr_comments_no_issue(self):
        """Test that None is returned when no issue is provided."""
        mock_pull_request = MagicMock()
        result = count_pr_comments(None, mock_pull_request, [])
        self.assertIsNone(result)

    def test_count_pr_comments_exception_handling(self):
        """Test that exceptions are handled gracefully."""
        # Mock issue that raises exception
        mock_issue = MagicMock()
        mock_issue.get_comments.side_effect = AttributeError("No comments")

        mock_pull_request = MagicMock()
        mock_pull_request.get_review_comments.side_effect = AttributeError(
            "No review comments"
        )

        result = count_pr_comments(mock_issue, mock_pull_request, [])
        self.assertEqual(result, 0)


class TestGetStatsPRComments(unittest.TestCase):
    """Test the get_stats_pr_comments function."""

    def test_get_stats_pr_comments_with_data(self):
        """Test calculating PR comment statistics with data."""
        issues_with_metrics = [
            IssueWithMetrics("PR 1", "url1", "user1", pr_comment_count=5),
            IssueWithMetrics("PR 2", "url2", "user2", pr_comment_count=10),
            IssueWithMetrics("PR 3", "url3", "user3", pr_comment_count=3),
            IssueWithMetrics("Issue 1", "url4", "user4"),  # No comment count (not a PR)
        ]

        result = get_stats_pr_comments(issues_with_metrics)

        self.assertIsNotNone(result)
        self.assertEqual(result["avg"], 6.0)  # (5+10+3)/3
        self.assertEqual(result["med"], 5.0)
        self.assertEqual(result["90p"], 9.0)  # 90th percentile

    def test_get_stats_pr_comments_no_data(self):
        """Test calculating PR comment statistics with no PR data."""
        issues_with_metrics = [
            IssueWithMetrics("Issue 1", "url1", "user1"),  # No comment count
            IssueWithMetrics("Issue 2", "url2", "user2"),  # No comment count
        ]

        result = get_stats_pr_comments(issues_with_metrics)
        self.assertIsNone(result)

    def test_get_stats_pr_comments_empty_list(self):
        """Test calculating PR comment statistics with empty list."""
        result = get_stats_pr_comments([])
        self.assertIsNone(result)


class TestPRCommentsIgnoreUsersDefault(unittest.TestCase):
    """Covers pr_comments.py ignore_users default."""

    def test_count_pr_comments_with_default_ignore_users(self):
        """Default ignore_users falls back to an empty list."""

        mock_comment = MagicMock()
        mock_comment.user.type = "User"
        mock_comment.user.login = "alice"

        mock_issue = MagicMock()
        mock_issue.get_comments.return_value = [mock_comment]

        mock_pr = MagicMock()
        mock_pr.get_review_comments.return_value = []

        result = count_pr_comments(mock_issue, mock_pr)
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
