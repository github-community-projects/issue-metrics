"""A module containing unit tests for the issue_metrics module.

This module contains unit tests for the functions in the issue_metrics module
that measure and analyze metrics of GitHub issues. The tests use mock GitHub
issues and comments to test the functions' behavior.

Classes:
    TestSearchIssues: A class to test the search_issues function.
    TestGetPerIssueMetrics: A class to test the get_per_issue_metrics function.
    TestGetEnvVars: A class to test the get_env_vars function.
    TestEvaluateMarkdownFileSize: A class to test the evaluate_markdown_file_size function.
"""

import os
import runpy
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

from issue_metrics import (
    IssueWithMetrics,
    evaluate_markdown_file_size,
    get_env_vars,
    get_per_issue_metrics,
    measure_time_to_close,
    measure_time_to_first_response,
)


class TestGetEnvVars(unittest.TestCase):
    """Test suite for the get_env_vars function."""

    @patch.dict(
        os.environ,
        {"GH_TOKEN": "test_token", "SEARCH_QUERY": "is:issue is:open repo:user/repo"},
    )
    def test_get_env_vars(self):
        """Test that the function correctly retrieves the environment variables."""

        # Call the function and check the result
        search_query = get_env_vars(test=True).search_query
        gh_token = get_env_vars(test=True).gh_token
        gh_token_expected_result = "test_token"
        search_query_expected_result = "is:issue is:open repo:user/repo"
        self.assertEqual(gh_token, gh_token_expected_result)
        self.assertEqual(search_query, search_query_expected_result)

    def test_get_env_vars_missing_query(self):
        """Test that the function raises a ValueError
        if the SEARCH_QUERY environment variable is not set."""
        # Unset the SEARCH_QUERY environment variable
        os.environ.pop("SEARCH_QUERY", None)

        # Call the function and check that it raises a ValueError
        with self.assertRaises(ValueError):
            get_env_vars(test=True)


class TestGetPerIssueMetrics(unittest.TestCase):
    """Test suite for the get_per_issue_metrics function."""

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:issue is:open repo:user/repo",
            "HIDE_AUTHOR": "true",
            "HIDE_LABEL_METRICS": "true",
            "HIDE_TIME_TO_ANSWER": "true",
            "HIDE_TIME_TO_CLOSE": "true",
            "HIDE_TIME_TO_FIRST_RESPONSE": "true",
        },
    )
    def test_get_per_issue_metrics_with_hide_envs(self):
        """
        Test that the function correctly calculates the metrics for
        a list of GitHub issues where HIDE_* envs are set true
        """

        # Create mock data
        mock_user1 = MagicMock()
        mock_user1.login = "alice"
        mock_issue1 = MagicMock(
            title="Issue 1",
            html_url="https://github.com/user/repo/issues/1",
            user=mock_user1,
            state="open",
            comments=1,
            created_at=datetime.fromisoformat("2023-01-01T00:00:00Z"),
            assignee=None,
            assignees=[],
        )

        mock_comment1 = MagicMock()
        mock_comment1.created_at = datetime.fromisoformat("2023-01-02T00:00:00Z")
        mock_issue1.get_comments.return_value = [mock_comment1]
        mock_issue1.pull_request = None

        mock_user2 = MagicMock()
        mock_user2.login = "bob"
        mock_issue2 = MagicMock(
            title="Issue 2",
            html_url="https://github.com/user/repo/issues/2",
            user=mock_user2,
            state="closed",
            comments=1,
            created_at=datetime.fromisoformat("2023-01-01T00:00:00Z"),
            closed_at=datetime.fromisoformat("2023-01-04T00:00:00Z"),
            assignee=None,
            assignees=[],
        )

        mock_comment2 = MagicMock()
        mock_comment2.created_at = datetime.fromisoformat("2023-01-03T00:00:00Z")
        mock_issue2.get_comments.return_value = [mock_comment2]
        mock_issue2.pull_request = None

        issues = [
            mock_issue1,
            mock_issue2,
        ]

        # Call the function and check the result
        with (
            unittest.mock.patch(  # type: ignore
                "issue_metrics.measure_time_to_first_response",
                measure_time_to_first_response,
            ),
            unittest.mock.patch(  # type: ignore
                "issue_metrics.measure_time_to_close", measure_time_to_close
            ),
        ):
            (
                result_issues_with_metrics,
                result_num_issues_open,
                result_num_issues_closed,
            ) = get_per_issue_metrics(
                issues,
                env_vars=get_env_vars(test=True),
            )
        expected_issues_with_metrics = [
            IssueWithMetrics(
                "Issue 1",
                "https://github.com/user/repo/issues/1",
                "alice",
                None,
                None,
                None,
                None,
            ),
            IssueWithMetrics(
                "Issue 2",
                "https://github.com/user/repo/issues/2",
                "bob",
                None,
                None,
                None,
                None,
            ),
        ]
        expected_num_issues_open = 1
        expected_num_issues_closed = 1
        self.assertEqual(result_num_issues_open, expected_num_issues_open)
        self.assertEqual(result_num_issues_closed, expected_num_issues_closed)
        self.assertEqual(
            result_issues_with_metrics[0].time_to_first_response,
            expected_issues_with_metrics[0].time_to_first_response,
        )
        self.assertEqual(
            result_issues_with_metrics[0].time_to_close,
            expected_issues_with_metrics[0].time_to_close,
        )
        self.assertEqual(
            result_issues_with_metrics[1].time_to_first_response,
            expected_issues_with_metrics[1].time_to_first_response,
        )
        self.assertEqual(
            result_issues_with_metrics[1].time_to_close,
            expected_issues_with_metrics[1].time_to_close,
        )

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:issue is:open repo:user/repo",
            "HIDE_AUTHOR": "false",
            "HIDE_LABEL_METRICS": "false",
            "HIDE_TIME_TO_ANSWER": "false",
            "HIDE_TIME_TO_CLOSE": "false",
            "HIDE_TIME_TO_FIRST_RESPONSE": "false",
        },
    )
    def test_get_per_issue_metrics_without_hide_envs(self):
        """
        Test that the function correctly calculates the metrics for
        a list of GitHub issues where HIDE_* envs are set false
        """

        # Create mock data
        mock_user1 = MagicMock()
        mock_user1.login = "alice"
        mock_issue1 = MagicMock(
            title="Issue 1",
            html_url="https://github.com/user/repo/issues/1",
            user=mock_user1,
            state="open",
            comments=1,
            created_at=datetime.fromisoformat("2023-01-01T00:00:00Z"),
            assignee=None,
            assignees=[],
        )

        mock_comment1 = MagicMock()
        mock_comment1.created_at = datetime.fromisoformat("2023-01-02T00:00:00Z")
        mock_issue1.get_comments.return_value = [mock_comment1]
        mock_issue1.pull_request = None

        mock_user2 = MagicMock()
        mock_user2.login = "bob"
        mock_issue2 = MagicMock(
            title="Issue 2",
            html_url="https://github.com/user/repo/issues/2",
            user=mock_user2,
            state="closed",
            comments=1,
            created_at=datetime.fromisoformat("2023-01-01T00:00:00Z"),
            closed_at=datetime.fromisoformat("2023-01-04T00:00:00Z"),
            state_reason="completed",
            assignee=None,
            assignees=[],
        )

        mock_comment2 = MagicMock()
        mock_comment2.created_at = datetime.fromisoformat("2023-01-03T00:00:00Z")
        mock_issue2.get_comments.return_value = [mock_comment2]
        mock_issue2.pull_request = None

        issues = [
            mock_issue1,
            mock_issue2,
        ]

        # Call the function and check the result
        with (
            unittest.mock.patch(  # type: ignore
                "issue_metrics.measure_time_to_first_response",
                measure_time_to_first_response,
            ),
            unittest.mock.patch(  # type: ignore
                "issue_metrics.measure_time_to_close", measure_time_to_close
            ),
        ):
            (
                result_issues_with_metrics,
                result_num_issues_open,
                result_num_issues_closed,
            ) = get_per_issue_metrics(
                issues,
                env_vars=get_env_vars(test=True),
            )
        expected_issues_with_metrics = [
            IssueWithMetrics(
                "Issue 1",
                "https://github.com/user/repo/issues/1",
                "alice",
                timedelta(days=1),
                None,
                None,
                None,
            ),
            IssueWithMetrics(
                "Issue 2",
                "https://github.com/user/repo/issues/2",
                "bob",
                timedelta(days=2),
                timedelta(days=3),
                None,
                None,
            ),
        ]
        expected_num_issues_open = 1
        expected_num_issues_closed = 1
        self.assertEqual(result_num_issues_open, expected_num_issues_open)
        self.assertEqual(result_num_issues_closed, expected_num_issues_closed)
        self.assertEqual(
            result_issues_with_metrics[0].time_to_first_response,
            expected_issues_with_metrics[0].time_to_first_response,
        )
        self.assertEqual(
            result_issues_with_metrics[0].time_to_close,
            expected_issues_with_metrics[0].time_to_close,
        )
        self.assertEqual(
            result_issues_with_metrics[1].time_to_first_response,
            expected_issues_with_metrics[1].time_to_first_response,
        )
        self.assertEqual(
            result_issues_with_metrics[1].time_to_close,
            expected_issues_with_metrics[1].time_to_close,
        )

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:issue is:open repo:user/repo",
            "IGNORE_USERS": "alice",
        },
    )
    def test_get_per_issue_metrics_with_ignore_users(self):
        """
        Test that the function correctly filters out issues
        with authors in the IGNORE_USERS variable
        """

        # Create mock data
        mock_user1 = MagicMock()
        mock_user1.login = "alice"
        mock_issue1 = MagicMock(
            title="Issue 1",
            html_url="https://github.com/user/repo/issues/1",
            user=mock_user1,
            state="open",
            comments=1,
            created_at=datetime.fromisoformat("2023-01-01T00:00:00Z"),
            assignee=None,
            assignees=[],
        )

        mock_comment1 = MagicMock()
        mock_comment1.created_at = datetime.fromisoformat("2023-01-02T00:00:00Z")
        mock_issue1.get_comments.return_value = [mock_comment1]
        mock_issue1.pull_request = None

        mock_user2 = MagicMock()
        mock_user2.login = "bob"
        mock_issue2 = MagicMock(
            title="Issue 2",
            html_url="https://github.com/user/repo/issues/2",
            user=mock_user2,
            state="closed",
            comments=1,
            created_at=datetime.fromisoformat("2023-01-01T00:00:00Z"),
            closed_at=datetime.fromisoformat("2023-01-04T00:00:00Z"),
            assignee=None,
            assignees=[],
        )

        mock_comment2 = MagicMock()
        mock_comment2.created_at = datetime.fromisoformat("2023-01-03T00:00:00Z")
        mock_issue2.get_comments.return_value = [mock_comment2]
        mock_issue2.pull_request = None

        issues = [
            mock_issue1,
            mock_issue2,
        ]

        # Call the function and check the result
        with (
            unittest.mock.patch(  # type: ignore
                "issue_metrics.measure_time_to_first_response",
                measure_time_to_first_response,
            ),
            unittest.mock.patch(  # type: ignore
                "issue_metrics.measure_time_to_close", measure_time_to_close
            ),
        ):
            (
                result_issues_with_metrics,
                result_num_issues_open,
                result_num_issues_closed,
            ) = get_per_issue_metrics(
                issues,
                env_vars=get_env_vars(test=True),
                ignore_users=["alice"],
            )
        expected_issues_with_metrics = [
            IssueWithMetrics(
                "Issue 2",
                "https://github.com/user/repo/issues/2",
                "bob",
                timedelta(days=2),
                timedelta(days=3),
                None,
                None,
            ),
        ]
        expected_num_issues_open = 0
        expected_num_issues_closed = 1
        self.assertEqual(result_num_issues_open, expected_num_issues_open)
        self.assertEqual(result_num_issues_closed, expected_num_issues_closed)
        self.assertEqual(
            result_issues_with_metrics[0].time_to_first_response,
            expected_issues_with_metrics[0].time_to_first_response,
        )
        self.assertEqual(
            result_issues_with_metrics[0].time_to_close,
            expected_issues_with_metrics[0].time_to_close,
        )

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:pr is:open repo:user/repo",
        },
    )
    def test_get_per_issue_metrics_with_ghost_user_pull_request(self):
        """
        Test that the function handles TypeError when a pull request
        contains a ghost user (deleted account) gracefully.
        """
        # Create mock data for a pull request that will cause TypeError on as_pull_request()
        mock_user = MagicMock()
        mock_user.login = "existing_user"
        mock_issue = MagicMock(
            title="PR with Ghost User",
            html_url="https://github.com/user/repo/pull/1",
            user=mock_user,
            state="open",
            comments=0,
            created_at=datetime.fromisoformat("2023-01-01T00:00:00Z"),
            closed_at=None,
            assignee=None,
            assignees=[],
        )

        # Mock the issue to have pull_request (indicating it's a PR)
        mock_issue.pull_request = MagicMock()

        # Make as_pull_request() raise TypeError (simulating ghost user scenario)
        mock_issue.as_pull_request.side_effect = TypeError(
            "'NoneType' object is not subscriptable"
        )
        mock_issue.get_comments.return_value = []

        issues = [mock_issue]

        # Mock the measure functions to avoid additional complexities
        with (
            unittest.mock.patch(  # type: ignore
                "issue_metrics.measure_time_to_first_response",
                return_value=timedelta(days=1),
            ),
            unittest.mock.patch(  # type: ignore
                "issue_metrics.measure_time_to_close", return_value=None
            ),
        ):
            # Call the function and verify it doesn't crash
            (
                result_issues_with_metrics,
                result_num_issues_open,
                result_num_issues_closed,
            ) = get_per_issue_metrics(
                issues,
                env_vars=get_env_vars(test=True),
            )

        # Verify the function completed successfully despite the TypeError
        self.assertEqual(len(result_issues_with_metrics), 1)
        self.assertEqual(result_num_issues_open, 1)
        self.assertEqual(result_num_issues_closed, 0)

        # Verify the issue was processed with pull_request as None
        issue_metric = result_issues_with_metrics[0]
        self.assertEqual(issue_metric.title, "PR with Ghost User")
        self.assertEqual(issue_metric.author, "existing_user")


class TestDiscussionMetrics(unittest.TestCase):
    """Test suite for the discussion_metrics function."""

    def setUp(self):
        # Mock a discussion dictionary
        self.issue1 = {
            "title": "Issue 1",
            "url": "github.com/user/repo/issues/1",
            "user": {"login": "alice"},
            "createdAt": "2023-01-01T00:00:00Z",
            "comments": {
                "nodes": [
                    {
                        "createdAt": "2023-01-02T00:00:00Z",
                    }
                ]
            },
            "answerChosenAt": "2023-01-04T00:00:00Z",
            "closedAt": "2023-01-05T00:00:00Z",
        }

        self.issue2 = {
            "title": "Issue 2",
            "url": "github.com/user/repo/issues/2",
            "user": {"login": "bob"},
            "createdAt": "2023-01-01T00:00:00Z",
            "comments": {"nodes": [{"createdAt": "2023-01-03T00:00:00Z"}]},
            "answerChosenAt": "2023-01-05T00:00:00Z",
            "closedAt": "2023-01-07T00:00:00Z",
        }

    @patch.dict(
        os.environ,
        {"GH_TOKEN": "test_token", "SEARCH_QUERY": "is:issue is:open repo:user/repo"},
    )
    def test_get_per_issue_metrics_with_discussion(self):
        """
        Test that the function correctly calculates
        the metrics for a list of GitHub issues with discussions.
        """

        issues = [self.issue1, self.issue2]
        metrics = get_per_issue_metrics(
            issues, discussions=True, env_vars=get_env_vars(test=True)
        )

        # get_per_issue_metrics returns a tuple of
        # (issues_with_metrics, num_issues_open, num_issues_closed)
        self.assertEqual(len(metrics), 3)

        # Check that the metrics are correct, 0 issues open, 2 issues closed
        self.assertEqual(metrics[1], 0)
        self.assertEqual(metrics[2], 2)

        # Check that the issues_with_metrics has 2 issues in it
        self.assertEqual(len(metrics[0]), 2)

        # Check that the issues_with_metrics has the correct metrics,
        self.assertEqual(metrics[0][0].time_to_answer, timedelta(days=3))
        self.assertEqual(metrics[0][0].time_to_close, timedelta(days=4))
        self.assertEqual(metrics[0][0].time_to_first_response, timedelta(days=1))
        self.assertEqual(metrics[0][1].time_to_answer, timedelta(days=4))
        self.assertEqual(metrics[0][1].time_to_close, timedelta(days=6))
        self.assertEqual(metrics[0][1].time_to_first_response, timedelta(days=2))

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:issue is:open repo:user/repo",
            "HIDE_AUTHOR": "true",
            "HIDE_CREATED_AT": "false",
            "HIDE_LABEL_METRICS": "true",
            "HIDE_TIME_TO_ANSWER": "true",
            "HIDE_TIME_TO_CLOSE": "true",
            "HIDE_TIME_TO_FIRST_RESPONSE": "true",
        },
    )
    def test_get_per_issue_metrics_with_discussion_with_hide_envs(self):
        """
        Test that the function correctly calculates
        the metrics for a list of GitHub issues with discussions
        and HIDE_* env vars set to True
        """

        issues = [self.issue1, self.issue2]
        metrics = get_per_issue_metrics(
            issues, discussions=True, env_vars=get_env_vars(test=True)
        )

        # get_per_issue_metrics returns a tuple of
        # (issues_with_metrics, num_issues_open, num_issues_closed)
        self.assertEqual(len(metrics), 3)

        # Check that the metrics are correct, 0 issues open, 2 issues closed
        self.assertEqual(metrics[1], 0)
        self.assertEqual(metrics[2], 2)

        # Check that the issues_with_metrics has 2 issues in it
        self.assertEqual(len(metrics[0]), 2)

        # Check that the issues_with_metrics has the correct metrics,
        self.assertEqual(metrics[0][0].time_to_answer, None)
        self.assertEqual(metrics[0][0].time_to_close, None)
        self.assertEqual(metrics[0][0].time_to_first_response, None)
        self.assertEqual(metrics[0][1].time_to_answer, None)
        self.assertEqual(metrics[0][1].time_to_close, None)
        self.assertEqual(metrics[0][1].time_to_first_response, None)


class TestEvaluateMarkdownFileSize(unittest.TestCase):
    """Test suite for the evaluate_markdown_file_size function."""

    @patch("issue_metrics.markdown_too_large_for_issue_body")
    def test_markdown_too_large_for_issue_body_called_with_empty_output_file(
        self, mock_evaluate
    ):
        """
        Test that the function uses the output_file.
        """
        mock_evaluate.return_value = False
        evaluate_markdown_file_size("")

        mock_evaluate.assert_called_with("issue_metrics.md", 65535)

    @patch("issue_metrics.markdown_too_large_for_issue_body")
    def test_markdown_too_large_for_issue_body_called_with_output_file(
        self, mock_evaluate
    ):
        """
        Test that the function uses the output_file.
        """
        mock_evaluate.return_value = False
        evaluate_markdown_file_size("test_issue_metrics.md")

        mock_evaluate.assert_called_with("test_issue_metrics.md", 65535)

    @patch("issue_metrics.print")
    @patch("shutil.move")
    @patch("issue_metrics.split_markdown_file")
    @patch("issue_metrics.markdown_too_large_for_issue_body")
    def test_split_markdown_file_when_file_size_too_large(
        self, mock_evaluate, mock_split, mock_move, mock_print
    ):
        """
        Test that the function is called with the output_file
        environment variable.
        """
        mock_evaluate.return_value = True
        evaluate_markdown_file_size("test_issue_metrics.md")

        mock_split.assert_called_with("test_issue_metrics.md", 65535)
        mock_move.assert_has_calls(
            [
                call("test_issue_metrics.md", "test_issue_metrics_full.md"),
                call("test_issue_metrics_0.md", "test_issue_metrics.md"),
            ]
        )
        mock_print.assert_called_with(
            "Issue metrics markdown file is too large for GitHub issue body and has been \
split into multiple files. ie. test_issue_metrics.md, test_issue_metrics_1.md, etc. \
The full file is saved as test_issue_metrics_full.md\n\
See https://github.com/github-community-projects/issue-metrics/blob/main/docs/dealing-with-large-issue-metrics.md"
        )


def _make_pr_search_result(
    *,
    title="PR 1",
    url="https://github.com/owner/repo/pull/1",
    login="alice",
    state="open",
    created_at="2023-01-01T00:00:00Z",
    closed_at=None,
    state_reason="completed",
    is_pull_request=True,
    pull_request=None,
):
    """Build a MagicMock that matches PyGithub Issue shape."""
    mock_user = MagicMock()
    mock_user.login = login

    mock_assignee = MagicMock()
    mock_assignee.login = login

    mock = MagicMock()
    mock.title = title
    mock.html_url = url
    mock.user = mock_user
    mock.state = state
    mock.created_at = datetime.fromisoformat(created_at)
    mock.closed_at = datetime.fromisoformat(closed_at) if closed_at else None
    mock.state_reason = state_reason

    mock.assignee = mock_assignee
    mock.assignees = [mock_assignee]

    mock.pull_request = MagicMock() if is_pull_request else None
    mock.as_pull_request.return_value = pull_request
    return mock


class TestIssueMetricsExtraBranches(unittest.TestCase):
    """Covers get_per_issue_metrics branches for discussions and pull requests."""

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:issue repo:user/repo",
            "ENABLE_MENTOR_COUNT": "true",
        },
    )
    def test_discussion_open_and_enable_mentor_count(self):
        """Open discussions count mentor activity when ENABLE_MENTOR_COUNT is set."""

        # Open discussion (closedAt None) plus enabled mentor counting.
        discussion = {
            "title": "D1",
            "url": "https://example.com/d/1",
            "createdAt": "2023-01-01T00:00:00Z",
            "comments": {"nodes": [{"createdAt": "2023-01-02T00:00:00Z"}]},
            "answerChosenAt": None,
            "closedAt": None,
        }

        with patch("issue_metrics.count_comments_per_user", return_value={"u": 1}):
            metrics, num_open, num_closed = get_per_issue_metrics(
                [discussion],
                discussions=True,
                env_vars=get_env_vars(test=True),
            )
        self.assertEqual(num_open, 1)
        self.assertEqual(num_closed, 0)
        self.assertEqual(metrics[0].mentor_activity, {"u": 1})

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:pr repo:owner/repo",
            "DRAFT_PR_TRACKING": "true",
            "HIDE_PR_STATISTICS": "false",
            "ENABLE_MENTOR_COUNT": "true",
            "HIDE_LABEL_METRICS": "false",
            "HIDE_TIME_TO_FIRST_REVIEW": "false",
            "HIDE_STATUS": "false",
            "HIDE_CREATED_AT": "false",
            "LABELS_TO_MEASURE": "bug",
        },
    )
    def test_pull_request_branches_with_status_and_created_at(self):
        """Cover the PR branches for time_in_draft, count_pr_comments,
        time_to_first_review, count_comments_per_user, get_label_metrics,
        measure_time_to_merge, status (open and closed), and created_at.
        """

        mock_pr_obj = MagicMock()

        # Closed PR exercises measure_time_to_merge and the closed status form.
        closed_pr = _make_pr_search_result(
            title="Closed PR",
            url="https://github.com/owner/repo/pull/2",
            state="closed",
            closed_at="2023-01-05T00:00:00Z",
            state_reason="completed",
            pull_request=mock_pr_obj,
        )
        # Open PR exercises the open status branch.
        open_pr = _make_pr_search_result(
            title="Open PR",
            url="https://github.com/owner/repo/pull/3",
            state="open",
            pull_request=mock_pr_obj,
        )

        with (
            patch("issue_metrics.get_time_to_ready_for_review", return_value=None),
            patch(
                "issue_metrics.measure_time_in_draft",
                return_value=timedelta(hours=2),
            ),
            patch("issue_metrics.count_pr_comments", return_value=4),
            patch(
                "issue_metrics.measure_time_to_first_review",
                return_value=timedelta(hours=1),
            ),
            patch(
                "issue_metrics.measure_time_to_first_response",
                return_value=timedelta(hours=3),
            ),
            patch(
                "issue_metrics.count_comments_per_user",
                return_value={"reviewer": 2},
            ),
            patch(
                "issue_metrics.get_label_metrics",
                return_value={"bug": timedelta(days=1)},
            ),
            patch(
                "issue_metrics.measure_time_to_merge",
                return_value=timedelta(days=4),
            ),
        ):
            env_vars = get_env_vars(test=True)
            metrics, num_open, num_closed = get_per_issue_metrics(
                [closed_pr, open_pr],
                env_vars=env_vars,
                labels=env_vars.labels_to_measure,
                ignore_users=[],
            )

        self.assertEqual(num_open, 1)
        self.assertEqual(num_closed, 1)
        # Closed PR uses measure_time_to_merge.
        self.assertEqual(metrics[0].time_to_close, timedelta(days=4))
        # Closed status uses the "as state_reason" form.
        self.assertIn("as", metrics[0].status)
        # Open status uses just the state value.
        self.assertEqual(metrics[1].status, "open")
        # created_at is populated from issue.created_at.
        self.assertIsNotNone(metrics[0].created_at)

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:pr repo:owner/repo",
            "DRAFT_PR_TRACKING": "true",
        },
    )
    def test_pull_request_with_ready_for_review_path(self):
        """Cover the ready_for_review and time_in_draft branches."""

        mock_pr_obj = MagicMock()
        pr = _make_pr_search_result(pull_request=mock_pr_obj)

        with (
            patch(
                "issue_metrics.get_time_to_ready_for_review",
                return_value=datetime.fromisoformat("2023-01-02T00:00:00Z"),
            ),
            patch(
                "issue_metrics.measure_time_in_draft",
                return_value=timedelta(days=1),
            ),
            patch("issue_metrics.measure_time_to_first_review", return_value=None),
            patch("issue_metrics.measure_time_to_first_response", return_value=None),
        ):
            metrics, _open, _closed = get_per_issue_metrics(
                [pr],
                env_vars=get_env_vars(test=True),
            )
        self.assertEqual(metrics[0].time_in_draft, timedelta(days=1))


class TestIssueMetricsMainGuard(unittest.TestCase):
    """Covers the `if __name__ == "__main__": main()` guard in issue_metrics."""

    def test_main_guard_invokes_main(self):
        """Executes issue_metrics as __main__ to cover the if-name guard."""

        original_module = sys.modules.get("issue_metrics")
        try:
            sys.modules.pop("issue_metrics", None)
            # Patch get_env_vars at import-time so main() raises immediately
            # without doing any real GitHub work. We only need the
            # `if __name__ == "__main__": main()` line itself to execute
            # for coverage to register the guard.
            with patch(
                "config.get_env_vars",
                side_effect=SystemExit(0),
            ):
                with self.assertRaises(SystemExit):
                    runpy.run_module("issue_metrics", run_name="__main__")
        finally:
            # Restore the originally imported module so other tests see the
            # same identity for any patches they have applied.
            if original_module is not None:
                sys.modules["issue_metrics"] = original_module
            else:
                sys.modules.pop("issue_metrics", None)


if __name__ == "__main__":
    unittest.main()
