"""Unit tests for the sorting and grouping functionality in markdown_writer module.

Classes:
    TestSortIssues: Tests for the sort_issues function.
    TestGroupIssues: Tests for the group_issues function.
    TestWriteToMarkdownWithSorting: Tests for write_to_markdown with sorting.
    TestWriteToMarkdownWithGrouping: Tests for write_to_markdown with grouping.
"""

import os
import unittest
from datetime import timedelta
from unittest.mock import patch

from classes import IssueWithMetrics
from markdown_writer import group_issues, sort_issues, write_to_markdown


class TestSortIssues(unittest.TestCase):
    """Test the sort_issues function."""

    def test_sort_by_time_to_close_asc(self):
        """Test sorting by time_to_close in ascending order."""
        issues = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
                time_to_close=timedelta(days=5),
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
                time_to_close=timedelta(days=2),
            ),
            IssueWithMetrics(
                title="Issue 3",
                html_url="https://github.com/user/repo/issues/3",
                author="charlie",
                time_to_close=timedelta(days=7),
            ),
        ]

        sorted_issues = sort_issues(issues, "time_to_close", "asc")

        self.assertEqual(sorted_issues[0].title, "Issue 2")
        self.assertEqual(sorted_issues[1].title, "Issue 1")
        self.assertEqual(sorted_issues[2].title, "Issue 3")

    def test_sort_by_time_to_close_desc(self):
        """Test sorting by time_to_close in descending order."""
        issues = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
                time_to_close=timedelta(days=5),
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
                time_to_close=timedelta(days=2),
            ),
            IssueWithMetrics(
                title="Issue 3",
                html_url="https://github.com/user/repo/issues/3",
                author="charlie",
                time_to_close=timedelta(days=7),
            ),
        ]

        sorted_issues = sort_issues(issues, "time_to_close", "desc")

        self.assertEqual(sorted_issues[0].title, "Issue 3")
        self.assertEqual(sorted_issues[1].title, "Issue 1")
        self.assertEqual(sorted_issues[2].title, "Issue 2")

    def test_sort_with_none_values(self):
        """Test that None values are placed at the end regardless of sort order."""
        issues = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
                time_to_close=timedelta(days=5),
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
                time_to_close=None,
            ),
            IssueWithMetrics(
                title="Issue 3",
                html_url="https://github.com/user/repo/issues/3",
                author="charlie",
                time_to_close=timedelta(days=2),
            ),
        ]

        sorted_issues = sort_issues(issues, "time_to_close", "asc")

        self.assertEqual(sorted_issues[0].title, "Issue 3")
        self.assertEqual(sorted_issues[1].title, "Issue 1")
        self.assertEqual(sorted_issues[2].title, "Issue 2")

        # Verify descending order also places None values at the end
        sorted_issues_desc = sort_issues(issues, "time_to_close", "desc")

        self.assertEqual(sorted_issues_desc[0].title, "Issue 1")
        self.assertEqual(sorted_issues_desc[1].title, "Issue 3")
        self.assertEqual(sorted_issues_desc[2].title, "Issue 2")

    def test_sort_by_invalid_field(self):
        """Test that sorting by an invalid field returns the original list."""
        issues = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
            ),
        ]

        sorted_issues = sort_issues(issues, "invalid_field", "asc")

        self.assertEqual(sorted_issues, issues)

    def test_sort_empty_list(self):
        """Test sorting an empty list."""
        issues = []
        sorted_issues = sort_issues(issues, "time_to_close", "asc")
        self.assertEqual(sorted_issues, [])

    def test_sort_none_sort_by(self):
        """Test sorting with None as sort_by parameter."""
        issues = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
            ),
        ]
        sorted_issues = sort_issues(issues, None, "asc")
        self.assertEqual(sorted_issues, issues)


class TestGroupIssues(unittest.TestCase):
    """Test the group_issues function."""

    def test_group_by_author(self):
        """Test grouping by author."""
        issues = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
            ),
            IssueWithMetrics(
                title="Issue 3",
                html_url="https://github.com/user/repo/issues/3",
                author="alice",
            ),
        ]

        grouped_issues = group_issues(issues, "author")

        self.assertIn("alice", grouped_issues)
        self.assertIn("bob", grouped_issues)
        self.assertEqual(len(grouped_issues["alice"]), 2)
        self.assertEqual(len(grouped_issues["bob"]), 1)

    def test_group_by_assignee(self):
        """Test grouping by assignee."""
        issues = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
                assignees=["charlie"],
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
                assignees=["david"],
            ),
            IssueWithMetrics(
                title="Issue 3",
                html_url="https://github.com/user/repo/issues/3",
                author="alice",
                assignees=["charlie"],
            ),
            IssueWithMetrics(
                title="Issue 4",
                html_url="https://github.com/user/repo/issues/4",
                author="bob",
                assignees=[],
            ),
        ]

        grouped_issues = group_issues(issues, "assignee")

        self.assertIn("charlie", grouped_issues)
        self.assertIn("david", grouped_issues)
        self.assertIn("Unassigned", grouped_issues)
        self.assertEqual(len(grouped_issues["charlie"]), 2)
        self.assertEqual(len(grouped_issues["david"]), 1)
        self.assertEqual(len(grouped_issues["Unassigned"]), 1)

    def test_group_by_invalid_field(self):
        """Test that grouping by an invalid field returns all issues in one group."""
        issues = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
            ),
        ]

        grouped_issues = group_issues(issues, "invalid_field")

        self.assertEqual(len(grouped_issues), 1)
        self.assertIn("", grouped_issues)
        self.assertEqual(len(grouped_issues[""]), 2)

    def test_group_empty_list(self):
        """Test grouping an empty list."""
        issues = []
        grouped_issues = group_issues(issues, "author")
        self.assertEqual(grouped_issues, {"": []})

    def test_group_none_group_by(self):
        """Test grouping with None as group_by parameter."""
        issues = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
            ),
        ]
        grouped_issues = group_issues(issues, None)
        self.assertEqual(grouped_issues, {"": issues})


@patch.dict(
    os.environ,
    {
        "SEARCH_QUERY": "is:open repo:user/repo",
        "GH_TOKEN": "test_token",
        "SORT_BY": "time_to_close",
        "SORT_ORDER": "asc",
    },
)
class TestWriteToMarkdownWithSorting(unittest.TestCase):
    """Test the write_to_markdown function with sorting enabled."""

    def test_write_to_markdown_with_sorting(self):
        """Test that write_to_markdown sorts issues correctly."""
        issues_with_metrics = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
                time_to_close=timedelta(days=5),
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
                time_to_close=timedelta(days=2),
            ),
            IssueWithMetrics(
                title="Issue 3",
                html_url="https://github.com/user/repo/issues/3",
                author="charlie",
                time_to_close=timedelta(days=7),
            ),
        ]

        write_to_markdown(
            issues_with_metrics=issues_with_metrics,
            average_time_to_first_response=None,
            average_time_to_first_review=None,
            average_time_to_close=None,
            average_time_to_answer=None,
            average_time_in_draft=None,
            average_time_in_labels=None,
            stats_pr_comments=None,
            num_issues_opened=3,
            num_issues_closed=0,
            num_mentor_count=0,
            report_title="Issue Metrics",
            output_file="issue_metrics.md",
        )

        with open("issue_metrics.md", "r", encoding="utf-8") as file:
            content = file.read()

        # Check that issues appear in the correct order
        issue_2_pos = content.find("Issue 2")
        issue_1_pos = content.find("Issue 1")
        issue_3_pos = content.find("Issue 3")

        self.assertLess(issue_2_pos, issue_1_pos)
        self.assertLess(issue_1_pos, issue_3_pos)

        os.remove("issue_metrics.md")


@patch.dict(
    os.environ,
    {
        "SEARCH_QUERY": "is:open repo:user/repo",
        "GH_TOKEN": "test_token",
        "GROUP_BY": "author",
    },
)
class TestWriteToMarkdownWithGrouping(unittest.TestCase):
    """Test the write_to_markdown function with grouping enabled."""

    def test_write_to_markdown_with_grouping(self):
        """Test that write_to_markdown groups issues correctly."""
        issues_with_metrics = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
            ),
            IssueWithMetrics(
                title="Issue 3",
                html_url="https://github.com/user/repo/issues/3",
                author="alice",
            ),
        ]

        write_to_markdown(
            issues_with_metrics=issues_with_metrics,
            average_time_to_first_response=None,
            average_time_to_first_review=None,
            average_time_to_close=None,
            average_time_to_answer=None,
            average_time_in_draft=None,
            average_time_in_labels=None,
            stats_pr_comments=None,
            num_issues_opened=3,
            num_issues_closed=0,
            num_mentor_count=0,
            report_title="Issue Metrics",
            output_file="issue_metrics.md",
        )

        with open("issue_metrics.md", "r", encoding="utf-8") as file:
            content = file.read()

        # Check that group headers are present
        self.assertIn("### alice", content)
        self.assertIn("### bob", content)

        os.remove("issue_metrics.md")


if __name__ == "__main__":
    unittest.main()
