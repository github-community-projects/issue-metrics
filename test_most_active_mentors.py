"""A module containing unit tests for the most_active_mentors module.

This module contains unit tests for the count_comments_per_user and
get_mentor_count functions in the most_active_mentors module.
The tests use mock GitHub issues and comments to test the functions' behavior.

Classes:
    TestCountCommentsPerUser: A class testing count_comments_per_user.
    TestGetMentorCount: A class to test the
        get_mentor_count function.

"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from classes import IssueWithMetrics
from most_active_mentors import count_comments_per_user, get_mentor_count


class TestCountCommentsPerUser(unittest.TestCase):
    """Test the count_comments_per_user function."""

    def test_count_comments_per_user_limit(self):
        """Test that count_comments_per_user correctly counts user comments.

        This test mocks the GitHub connection and issue comments, and checks
        that count_comments_per_user correctly considers user comments for
        counting.

        """
        # Set up the mock GitHub issues
        mock_issue1 = MagicMock()
        mock_issue1.comments = 2
        mock_issue1.issue.user.login = "issue_owner"
        mock_issue1.created_at = "2023-01-01T00:00:00Z"

        # Set up 21 mock GitHub issue comments - only 20 should be counted
        mock_issue1.issue.comments.return_value = []
        for i in range(22):
            mock_comment1 = MagicMock()
            mock_comment1.user.login = "very_active_user"
            mock_comment1.created_at = datetime.fromisoformat(
                f"2023-01-02T{i:02d}:00:00Z"
            )
            # pylint: disable=maybe-no-member
            mock_issue1.issue.comments.return_value.append(mock_comment1)

        # Call the function
        result = count_comments_per_user(mock_issue1)
        expected_result = {"very_active_user": 3}

        # Check the results
        self.assertEqual(result, expected_result)

    def test_count_comments_per_user_with_ignores(self):
        """Test that count_comments_per_user correctly counts user comments with some users ignored."""
        # Set up the mock GitHub issues
        mock_issue1 = MagicMock()
        mock_issue1.comments = 2
        mock_issue1.issue.user.login = "issue_owner"
        mock_issue1.created_at = "2023-01-01T00:00:00Z"

        # Set up mock GitHub issue comments by several users
        mock_issue1.issue.comments.return_value = []
        for i in range(5):
            mock_comment1 = MagicMock()
            mock_comment1.user.login = "very_active_user"
            mock_comment1.created_at = datetime.fromisoformat(
                f"2023-01-02T{i:02d}:00:00Z"
            )
            # pylint: disable=maybe-no-member
            mock_issue1.issue.comments.return_value.append(mock_comment1)
        for i in range(5):
            mock_comment1 = MagicMock()
            mock_comment1.user.login = "very_active_user_ignored"
            mock_comment1.created_at = datetime.fromisoformat(
                f"2023-01-02T{i:02d}:00:00Z"
            )
            # pylint: disable=maybe-no-member
            mock_issue1.issue.comments.return_value.append(mock_comment1)

        # Call the function
        result = count_comments_per_user(
            mock_issue1, ignore_users=["very_active_user_ignored"]
        )
        # Only the comments by "very_active_user" should be counted,
        # so the count should be 3 since that is the threshold for heavily involved
        expected_result = {"very_active_user": 3}

        # Check the results
        self.assertEqual(result, expected_result)
        self.assertNotIn("very_active_user_ignored", result)

    def test_get_mentor_count(self):
        """Test that get_mentor_count correctly counts comments per user."""
        mentor_activity = {"sue": 15, "bob": 10}

        # Create mock data
        issues_with_metrics = [
            IssueWithMetrics(
                "Issue 1",
                "https://github.com/user/repo/issues/1",
                "alice",
                None,
                mentor_activity=mentor_activity,
            ),
            IssueWithMetrics(
                "Issue 2",
                "https://github.com/user/repo/issues/2",
                "bob",
                None,
                mentor_activity=mentor_activity,
            ),
        ]

        # Call the function and check the result
        result = get_mentor_count(issues_with_metrics, 2)
        expected_result = 2
        self.assertEqual(result, expected_result)


class TestMostActiveMentorsExtraBranches(unittest.TestCase):
    """Covers most_active_mentors review-comments path."""

    def _make_issue(self, owner_login="issue_owner"):
        mock_issue = MagicMock()
        mock_issue.issue.user.login = owner_login
        mock_issue.issue.comments.return_value = []
        return mock_issue

    def test_count_comments_per_user_with_pr_reviews(self):
        """Reviews from a human reviewer are counted; bots are ignored."""

        mock_issue = self._make_issue()

        # Two reviews from the same human reviewer.
        review_a = MagicMock()
        review_a.user.login = "reviewer"
        review_a.user.type = "User"
        review_a.submitted_at = datetime.fromisoformat("2023-01-02T00:00:00Z")

        review_b = MagicMock()
        review_b.user.login = "reviewer"
        review_b.user.type = "User"
        review_b.submitted_at = datetime.fromisoformat("2023-01-03T00:00:00Z")

        # One review from a bot (must be ignored by ignore_comment).
        bot_review = MagicMock()
        bot_review.user.login = "dependabot"
        bot_review.user.type = "Bot"
        bot_review.submitted_at = datetime.fromisoformat("2023-01-04T00:00:00Z")

        mock_pr = MagicMock()
        mock_pr.reviews.return_value = [review_a, review_b, bot_review]

        result = count_comments_per_user(mock_issue, pull_request=mock_pr)
        self.assertEqual(result, {"reviewer": 2})


class TestCountCommentsDiscussions(unittest.TestCase):
    """Covers the discussion branch of count_comments_per_user.

    Before the fix for #774 this branch was dead code because:
      1. The GraphQL query fetched no comment author data.
      2. Attribute access on dict nodes would raise AttributeError.
      3. The ignore_comment call passed comment.user as both issue_user
         and comment_user, so every comment was silently skipped.
    """

    def _make_discussion(self, author_login, comments):
        """Return a minimal discussion dict as returned by get_discussions."""
        return {
            "title": "Test discussion",
            "url": "https://github.com/org/repo/discussions/1",
            "createdAt": "2024-01-01T00:00:00Z",
            "author": {"login": author_login, "__typename": "User"},
            "comments": {"nodes": comments},
            "answerChosenAt": None,
            "closedAt": None,
        }

    def test_counts_commenter(self):
        """A comment by a user other than the author is counted."""
        discussion = self._make_discussion(
            "op",
            [
                {
                    "createdAt": "2024-01-02T00:00:00Z",
                    "author": {"login": "mentor", "__typename": "User"},
                },
            ],
        )
        result = count_comments_per_user(None, discussion=discussion)
        self.assertEqual(result, {"mentor": 1})

    def test_ignores_discussion_author_self_comment(self):
        """Comments by the discussion author are not counted."""
        discussion = self._make_discussion(
            "op",
            [
                {
                    "createdAt": "2024-01-02T00:00:00Z",
                    "author": {"login": "op", "__typename": "User"},
                },
            ],
        )
        result = count_comments_per_user(None, discussion=discussion)
        self.assertEqual(result, {})

    def test_ignores_bot_commenter(self):
        """Comments from Bot actors are not counted."""
        discussion = self._make_discussion(
            "op",
            [
                {
                    "createdAt": "2024-01-02T00:00:00Z",
                    "author": {"login": "github-actions", "__typename": "Bot"},
                },
            ],
        )
        result = count_comments_per_user(None, discussion=discussion)
        self.assertEqual(result, {})

    def test_ignores_user_in_ignore_list(self):
        """Comments by explicitly ignored users are not counted."""
        discussion = self._make_discussion(
            "op",
            [
                {
                    "createdAt": "2024-01-02T00:00:00Z",
                    "author": {"login": "spammer", "__typename": "User"},
                },
            ],
        )
        result = count_comments_per_user(
            None, discussion=discussion, ignore_users=["spammer"]
        )
        self.assertEqual(result, {})

    def test_multiple_commenters(self):
        """Multiple distinct commenters each get their own count."""
        discussion = self._make_discussion(
            "op",
            [
                {
                    "createdAt": "2024-01-02T00:00:00Z",
                    "author": {"login": "alice", "__typename": "User"},
                },
                {
                    "createdAt": "2024-01-03T00:00:00Z",
                    "author": {"login": "bob", "__typename": "User"},
                },
                {
                    "createdAt": "2024-01-04T00:00:00Z",
                    "author": {"login": "alice", "__typename": "User"},
                },
            ],
        )
        result = count_comments_per_user(None, discussion=discussion)
        self.assertEqual(result, {"alice": 2, "bob": 1})

    def test_no_comments(self):
        """A discussion with an empty comments list returns an empty dict."""
        discussion = self._make_discussion("op", [])
        result = count_comments_per_user(None, discussion=discussion)
        self.assertEqual(result, {})

    def test_null_author_skipped(self):
        """A comment with a null author (deleted account) is skipped gracefully."""
        discussion = self._make_discussion(
            "op",
            [
                {
                    "createdAt": "2024-01-02T00:00:00Z",
                    "author": None,
                },
            ],
        )
        result = count_comments_per_user(None, discussion=discussion)
        self.assertEqual(result, {})
