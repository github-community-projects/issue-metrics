"""Tests for the write_to_json function in json_writer.py."""

import json
import os
import unittest
from datetime import timedelta
from unittest.mock import patch

from classes import IssueWithMetrics
from json_writer import write_to_json


class TestWriteToJson(unittest.TestCase):
    """Tests for the write_to_json function."""

    # Show differences without omission in assertion
    maxDiff = None

    def test_write_to_json(self):
        """Test that write_to_json writes the correct JSON file."""
        issues_with_metrics = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/owner/repo/issues/1",
                author="alice",
                assignee="charlie",
                assignees=["charlie"],
                time_to_first_response=timedelta(days=3),
                time_to_close=timedelta(days=6),
                time_to_answer=None,
                time_in_draft=timedelta(days=1),
                labels_metrics={
                    "bug": timedelta(days=1, hours=16, minutes=24, seconds=12)
                },
                created_at=timedelta(days=-5),
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/owner/repo/issues/2",
                author="bob",
                assignee=None,
                assignees=[],
                time_to_first_response=timedelta(days=2),
                time_to_close=timedelta(days=4),
                time_to_answer=timedelta(days=1),
                labels_metrics={},
                created_at=timedelta(days=-5),
            ),
        ]

        stats_time_to_first_response = {
            "avg": timedelta(days=2.5),
            "med": timedelta(days=2.5),
            "90p": timedelta(days=1.5),
        }
        stats_time_to_close = {
            "avg": timedelta(days=5),
            "med": timedelta(days=4),
            "90p": timedelta(days=3),
        }
        stats_time_to_answer = {
            "avg": timedelta(days=1),
            "med": timedelta(days=2),
            "90p": timedelta(days=3),
        }
        stats_time_in_draft = {
            "avg": timedelta(days=1),
            "med": timedelta(days=1),
            "90p": timedelta(days=1),
        }
        stats_time_in_labels = {
            "avg": {"bug": timedelta(days=1, hours=16, minutes=24, seconds=12)},
            "med": {"bug": timedelta(days=1, hours=16, minutes=24, seconds=12)},
            "90p": {"bug": timedelta(days=1, hours=16, minutes=24, seconds=12)},
        }
        num_issues_opened = 2
        num_issues_closed = 1
        num_mentor_count = 5

        expected_output = {
            "average_time_to_first_response": "2 days, 12:00:00",
            "average_time_to_first_review": "None",
            "average_time_to_close": "5 days, 0:00:00",
            "average_time_to_answer": "1 day, 0:00:00",
            "average_time_in_draft": "1 day, 0:00:00",
            "average_time_in_labels": {"bug": "1 day, 16:24:12"},
            "median_time_to_first_response": "2 days, 12:00:00",
            "median_time_to_first_review": "None",
            "median_time_to_close": "4 days, 0:00:00",
            "median_time_to_answer": "2 days, 0:00:00",
            "median_time_in_draft": "1 day, 0:00:00",
            "median_time_in_labels": {"bug": "1 day, 16:24:12"},
            "90_percentile_time_to_first_response": "1 day, 12:00:00",
            "90_percentile_time_to_first_review": "None",
            "90_percentile_time_to_close": "3 days, 0:00:00",
            "90_percentile_time_to_answer": "3 days, 0:00:00",
            "90_percentile_time_in_draft": "1 day, 0:00:00",
            "90_percentile_time_in_labels": {"bug": "1 day, 16:24:12"},
            "average_pr_comments": None,
            "median_pr_comments": None,
            "90_percentile_pr_comments": None,
            "num_items_opened": 2,
            "num_items_closed": 1,
            "num_mentor_count": 5,
            "total_item_count": 2,
            "issues": [
                {
                    "title": "Issue 1",
                    "html_url": "https://github.com/owner/repo/issues/1",
                    "author": "alice",
                    "assignee": "charlie",
                    "assignees": ["charlie"],
                    "time_to_first_response": "3 days, 0:00:00",
                    "time_to_first_review": "None",
                    "time_to_close": "6 days, 0:00:00",
                    "time_to_answer": "None",
                    "time_in_draft": "1 day, 0:00:00",
                    "label_metrics": {"bug": "1 day, 16:24:12"},
                    "pr_comment_count": None,
                    "created_at": "-5 days, 0:00:00",
                },
                {
                    "title": "Issue 2",
                    "html_url": "https://github.com/owner/repo/issues/2",
                    "author": "bob",
                    "assignee": None,
                    "assignees": [],
                    "time_to_first_response": "2 days, 0:00:00",
                    "time_to_first_review": "None",
                    "time_to_close": "4 days, 0:00:00",
                    "time_to_answer": "1 day, 0:00:00",
                    "time_in_draft": "None",
                    "label_metrics": {},
                    "pr_comment_count": None,
                    "created_at": "-5 days, 0:00:00",
                },
            ],
            "search_query": "is:issue repo:owner/repo",
        }

        # Call the function and check the output
        self.assertEqual(
            write_to_json(
                issues_with_metrics=issues_with_metrics,
                stats_time_to_first_response=stats_time_to_first_response,
                stats_time_to_first_review=None,
                stats_time_to_close=stats_time_to_close,
                stats_time_to_answer=stats_time_to_answer,
                stats_time_in_draft=stats_time_in_draft,
                stats_time_in_labels=stats_time_in_labels,
                stats_pr_comments=None,
                num_issues_opened=num_issues_opened,
                num_issues_closed=num_issues_closed,
                num_mentor_count=num_mentor_count,
                search_query="is:issue repo:owner/repo",
                output_file="issue_metrics.json",
            ),
            json.dumps(expected_output),
        )

    def test_write_to_json_with_no_response(self):
        """Test where there is no answer to a issue."""
        issues_with_metrics = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/owner/repo/issues/1",
                author="alice",
                assignee=None,
                assignees=[],
                time_to_first_response=None,
                time_to_close=None,
                time_to_answer=None,
                labels_metrics={},
                created_at=None,
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/owner/repo/issues/2",
                author="bob",
                assignee=None,
                assignees=[],
                time_to_first_response=None,
                time_to_close=None,
                time_to_answer=None,
                labels_metrics={},
                created_at=None,
            ),
        ]

        stats_time_to_first_response = None
        stats_time_to_close = None
        stats_time_to_answer = None
        stats_time_in_labels = {
            "avg": {},
            "med": {},
            "90p": {},
        }
        stats_time_in_draft = None
        num_issues_opened = 2
        num_issues_closed = 0
        num_mentor_count = 5

        expected_output = {
            "average_time_to_first_response": "None",
            "average_time_to_first_review": "None",
            "average_time_to_close": "None",
            "average_time_to_answer": "None",
            "average_time_in_draft": "None",
            "average_time_in_labels": {},
            "median_time_to_first_response": "None",
            "median_time_to_first_review": "None",
            "median_time_to_close": "None",
            "median_time_to_answer": "None",
            "median_time_in_draft": "None",
            "median_time_in_labels": {},
            "90_percentile_time_to_first_response": "None",
            "90_percentile_time_to_first_review": "None",
            "90_percentile_time_to_close": "None",
            "90_percentile_time_to_answer": "None",
            "90_percentile_time_in_draft": "None",
            "90_percentile_time_in_labels": {},
            "average_pr_comments": None,
            "median_pr_comments": None,
            "90_percentile_pr_comments": None,
            "num_items_opened": 2,
            "num_items_closed": 0,
            "num_mentor_count": 5,
            "total_item_count": 2,
            "issues": [
                {
                    "title": "Issue 1",
                    "html_url": "https://github.com/owner/repo/issues/1",
                    "author": "alice",
                    "assignee": None,
                    "assignees": [],
                    "time_to_first_response": "None",
                    "time_to_first_review": "None",
                    "time_to_close": "None",
                    "time_to_answer": "None",
                    "time_in_draft": "None",
                    "label_metrics": {},
                    "pr_comment_count": None,
                    "created_at": "None",
                },
                {
                    "title": "Issue 2",
                    "html_url": "https://github.com/owner/repo/issues/2",
                    "author": "bob",
                    "assignee": None,
                    "assignees": [],
                    "time_to_first_response": "None",
                    "time_to_first_review": "None",
                    "time_to_close": "None",
                    "time_to_answer": "None",
                    "time_in_draft": "None",
                    "label_metrics": {},
                    "pr_comment_count": None,
                    "created_at": "None",
                },
            ],
            "search_query": "is:issue repo:owner/repo",
        }

        # Call the function and check the output
        self.assertEqual(
            write_to_json(
                issues_with_metrics=issues_with_metrics,
                stats_time_to_first_response=stats_time_to_first_response,
                stats_time_to_first_review=None,
                stats_time_to_close=stats_time_to_close,
                stats_time_to_answer=stats_time_to_answer,
                stats_time_in_draft=stats_time_in_draft,
                stats_time_in_labels=stats_time_in_labels,
                stats_pr_comments=None,
                num_issues_opened=num_issues_opened,
                num_issues_closed=num_issues_closed,
                num_mentor_count=num_mentor_count,
                search_query="is:issue repo:owner/repo",
                output_file="issue_metrics.json",
            ),
            json.dumps(expected_output),
        )


class TestJsonWriterExtraBranches(unittest.TestCase):
    """Covers json_writer.py extra branches."""

    def test_returns_empty_string_when_no_issues(self):
        """Empty input returns an empty string."""

        result = write_to_json(
            issues_with_metrics=None,
            stats_time_to_first_response=None,
            stats_time_to_first_review=None,
            stats_time_to_close=None,
            stats_time_to_answer=None,
            stats_time_in_draft=None,
            stats_time_in_labels=None,
            stats_pr_comments=None,
            num_issues_opened=0,
            num_issues_closed=0,
            num_mentor_count=0,
            search_query="is:issue repo:user/repo",
            output_file="",
        )
        self.assertEqual(result, "")

    def test_includes_time_to_first_review_and_pr_comments(self):
        """Review stats and PR comments stats are written to JSON output."""

        issue = IssueWithMetrics(
            title="PR 1",
            html_url="https://github.com/owner/repo/pull/1",
            author="alice",
            assignee=None,
            assignees=[],
            pr_comment_count=3,
        )
        # time_to_first_review is not a constructor arg; set it directly.
        issue.time_to_first_review = timedelta(hours=4)
        issues = [issue]

        stats_review = {
            "avg": timedelta(hours=4),
            "med": timedelta(hours=4),
            "90p": timedelta(hours=4),
        }
        stats_pr_comments = {"avg": 3.0, "med": 3.0, "90p": 3.0}

        out = write_to_json(
            issues_with_metrics=issues,
            stats_time_to_first_response=None,
            stats_time_to_first_review=stats_review,
            stats_time_to_close=None,
            stats_time_to_answer=None,
            stats_time_in_draft=None,
            stats_time_in_labels=None,
            stats_pr_comments=stats_pr_comments,
            num_issues_opened=1,
            num_issues_closed=0,
            num_mentor_count=0,
            search_query="is:pr repo:owner/repo",
            output_file="coverage_test.json",
        )

        self.assertIn("4:00:00", out)
        self.assertIn('"average_pr_comments": 3.0', out)

        # Clean up the file the writer created so the test leaves no artifacts.
        try:
            os.remove("coverage_test.json")
        except OSError:
            pass

    def test_writes_github_output_when_env_var_present(self):
        """write_to_json writes to GITHUB_OUTPUT when the env var is set."""

        github_output_path = "coverage_github_output.txt"
        try:
            with patch.dict(os.environ, {"GITHUB_OUTPUT": github_output_path}):
                write_to_json(
                    issues_with_metrics=[
                        IssueWithMetrics(
                            title="I1",
                            html_url="https://x/1",
                            author="a",
                            assignee=None,
                            assignees=[],
                        )
                    ],
                    stats_time_to_first_response=None,
                    stats_time_to_first_review=None,
                    stats_time_to_close=None,
                    stats_time_to_answer=None,
                    stats_time_in_draft=None,
                    stats_time_in_labels=None,
                    stats_pr_comments=None,
                    num_issues_opened=1,
                    num_issues_closed=0,
                    num_mentor_count=0,
                    search_query="is:issue repo:user/repo",
                    output_file="coverage_test_gh.json",
                )

            with open(github_output_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("metrics=", content)
        finally:
            for path in (github_output_path, "coverage_test_gh.json"):
                try:
                    os.remove(path)
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main()
