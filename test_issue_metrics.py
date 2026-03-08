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
        mock_issue1 = MagicMock(
            title="Issue 1",
            html_url="https://github.com/user/repo/issues/1",
            user={"login": "alice"},
            state="open",
            comments=1,
            created_at="2023-01-01T00:00:00Z",
        )

        mock_comment1 = MagicMock()
        mock_comment1.created_at = datetime.fromisoformat("2023-01-02T00:00:00Z")
        mock_issue1.issue.comments.return_value = [mock_comment1]
        mock_issue1.issue.pull_request_urls = None

        mock_issue2 = MagicMock(
            title="Issue 2",
            html_url="https://github.com/user/repo/issues/2",
            user={"login": "bob"},
            state="closed",
            comments=1,
            created_at="2023-01-01T00:00:00Z",
            closed_at="2023-01-04T00:00:00Z",
        )

        mock_comment2 = MagicMock()
        mock_comment2.created_at = datetime.fromisoformat("2023-01-03T00:00:00Z")
        mock_issue2.issue.comments.return_value = [mock_comment2]
        mock_issue2.issue.pull_request_urls = None

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
        mock_issue1 = MagicMock(
            title="Issue 1",
            html_url="https://github.com/user/repo/issues/1",
            user={"login": "alice"},
            state="open",
            comments=1,
            created_at="2023-01-01T00:00:00Z",
        )

        mock_comment1 = MagicMock()
        mock_comment1.created_at = datetime.fromisoformat("2023-01-02T00:00:00Z")
        mock_issue1.issue.comments.return_value = [mock_comment1]
        mock_issue1.issue.pull_request_urls = None

        mock_issue2 = MagicMock(
            title="Issue 2",
            html_url="https://github.com/user/repo/issues/2",
            user={"login": "bob"},
            state="closed",
            comments=1,
            created_at="2023-01-01T00:00:00Z",
            closed_at="2023-01-04T00:00:00Z",
        )

        mock_comment2 = MagicMock()
        mock_comment2.created_at = datetime.fromisoformat("2023-01-03T00:00:00Z")
        mock_issue2.issue.comments.return_value = [mock_comment2]
        mock_issue2.issue.pull_request_urls = None

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
        mock_issue1 = MagicMock(
            title="Issue 1",
            html_url="https://github.com/user/repo/issues/1",
            user={"login": "alice"},
            state="open",
            comments=1,
            created_at="2023-01-01T00:00:00Z",
        )

        mock_comment1 = MagicMock()
        mock_comment1.created_at = datetime.fromisoformat("2023-01-02T00:00:00Z")
        mock_issue1.issue.comments.return_value = [mock_comment1]
        mock_issue1.issue.pull_request_urls = None

        mock_issue2 = MagicMock(
            title="Issue 2",
            html_url="https://github.com/user/repo/issues/2",
            user={"login": "bob"},
            state="closed",
            comments=1,
            created_at="2023-01-01T00:00:00Z",
            closed_at="2023-01-04T00:00:00Z",
        )

        mock_comment2 = MagicMock()
        mock_comment2.created_at = datetime.fromisoformat("2023-01-03T00:00:00Z")
        mock_issue2.issue.comments.return_value = [mock_comment2]
        mock_issue2.issue.pull_request_urls = None

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
        # Create mock data for a pull request that will cause TypeError on pull_request()
        mock_issue = MagicMock(
            title="PR with Ghost User",
            html_url="https://github.com/user/repo/pull/1",
            user={"login": "existing_user"},
            state="open",
            comments=0,
            created_at="2023-01-01T00:00:00Z",
            closed_at=None,
        )

        # Mock the issue to have pull_request_urls (indicating it's a PR)
        mock_issue.issue.pull_request_urls = [
            "https://api.github.com/repos/user/repo/pulls/1"
        ]

        # Make pull_request() raise TypeError (simulating ghost user scenario)
        mock_issue.issue.pull_request.side_effect = TypeError(
            "'NoneType' object is not subscriptable"
        )
        mock_issue.issue.comments.return_value = []
        mock_issue.issue.assignee = None
        mock_issue.issue.assignees = None

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


if __name__ == "__main__":
    unittest.main()
