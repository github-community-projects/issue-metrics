"""A module containing unit tests for the write_to_markdown function in the markdown_writer module.

Classes:
    TestWriteToMarkdown: A class to test the write_to_markdown function with mock data.
    TestWriteToMarkdownWithEnv: A class to test the write_to_markdown function with
        environment variables set.

"""

import os
import unittest
from datetime import timedelta
from unittest.mock import call, mock_open, patch

from classes import IssueWithMetrics
from markdown_writer import write_to_markdown


@patch.dict(
    os.environ,
    {
        "SEARCH_QUERY": "is:open repo:user/repo",
        "GH_TOKEN": "test_token",
        "DRAFT_PR_TRACKING": "True",
        "HIDE_CREATED_AT": "False",
        "HIDE_STATUS": "False",
    },
)
class TestWriteToMarkdown(unittest.TestCase):
    """Test the write_to_markdown function."""

    maxDiff = None

    def test_write_to_markdown(self):
        """Test that write_to_markdown writes the correct markdown file.

        This test creates a list of mock GitHub issues with time to first response
        attributes, calls write_to_markdown with the list and the average time to
        first response, time to close and checks that the function writes the correct
        markdown file.

        """
        # Create mock data
        issues_with_metrics = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
                assignee="charlie",
                assignees=["charlie"],
                created_at=timedelta(days=-5),
                time_to_first_response=timedelta(days=1),
                time_to_close=timedelta(days=2),
                time_to_answer=timedelta(days=3),
                time_in_draft=timedelta(days=1),
                labels_metrics={"bug": timedelta(days=4)},
            ),
            IssueWithMetrics(
                title="Issue 2\r",
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
                assignee=None,
                assignees=[],
                created_at=timedelta(days=-5),
                time_to_first_response=timedelta(days=3),
                time_to_close=timedelta(days=4),
                time_to_answer=timedelta(days=5),
                time_in_draft=timedelta(days=1),
                labels_metrics={"bug": timedelta(days=2)},
            ),
        ]
        time_to_first_response = {
            "avg": timedelta(days=2),
            "med": timedelta(days=2),
            "90p": timedelta(days=2),
        }
        time_to_close = {
            "avg": timedelta(days=3),
            "med": timedelta(days=3),
            "90p": timedelta(days=3),
        }
        time_to_answer = {
            "avg": timedelta(days=4),
            "med": timedelta(days=4),
            "90p": timedelta(days=4),
        }
        time_in_draft = {
            "avg": timedelta(days=1),
            "med": timedelta(days=1),
            "90p": timedelta(days=1),
        }
        time_in_labels = {
            "avg": {"bug": "1 day, 12:00:00"},
            "med": {"bug": "1 day, 12:00:00"},
            "90p": {"bug": "1 day, 12:00:00"},
        }

        num_issues_opened = 2
        num_issues_closed = 1
        num_mentor_count = 5

        # Call the function
        write_to_markdown(
            issues_with_metrics=issues_with_metrics,
            average_time_to_first_response=time_to_first_response,
            average_time_to_first_review=None,
            average_time_to_close=time_to_close,
            average_time_to_answer=time_to_answer,
            average_time_in_draft=time_in_draft,
            average_time_in_labels=time_in_labels,
            stats_pr_comments=None,
            num_issues_opened=num_issues_opened,
            num_issues_closed=num_issues_closed,
            num_mentor_count=num_mentor_count,
            labels=["bug"],
            search_query="is:issue is:open label:bug",
            report_title="Issue Metrics",
            output_file="issue_metrics.md",
            ghe="",
        )

        # Check that the function writes the correct markdown file
        with open("issue_metrics.md", "r", encoding="utf-8") as file:
            content = file.read()
        expected_content = (
            "# Issue Metrics\n\n"
            "| Metric | Average | Median | 90th percentile |\n"
            "| --- | --- | --- | ---: |\n"
            "| Time to first response | 2 days, 0:00:00 | 2 days, 0:00:00 | 2 days, 0:00:00 |\n"
            "| Time to first review | None | None | None |\n"
            "| Time to close | 3 days, 0:00:00 | 3 days, 0:00:00 | 3 days, 0:00:00 |\n"
            "| Time to answer | 4 days, 0:00:00 | 4 days, 0:00:00 | 4 days, 0:00:00 |\n"
            "| Time in draft | 1 day, 0:00:00 | 1 day, 0:00:00 | 1 day, 0:00:00 |\n"
            "| Time spent in bug | 1 day, 12:00:00 | 1 day, 12:00:00 | 1 day, 12:00:00 |\n"
            "| Status | | | |\n"
            "\n"
            "| Metric | Count |\n"
            "| --- | ---: |\n"
            "| Number of items that remain open | 2 |\n"
            "| Number of items closed | 1 |\n"
            "| Total number of items created | 2 |\n\n"
            "| Title | URL | Assignee | Author | Time to first response | Time to first review | Time to close | "
            "Time to answer | Time in draft | Time spent in bug | Created At | Status |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| Issue 1 | https://github.com/user/repo/issues/1 | [charlie](https://github.com/charlie) | "
            "[alice](https://github.com/alice) | 1 day, 0:00:00 | None | 2 days, 0:00:00 | 3 days, 0:00:00 | "
            "1 day, 0:00:00 | 4 days, 0:00:00 | -5 days, 0:00:00 | None |\n"
            "| Issue 2 | https://github.com/user/repo/issues/2 | None | [bob](https://github.com/bob) | 3 days, 0:00:00 | None | "
            "4 days, 0:00:00 | 5 days, 0:00:00 | 1 day, 0:00:00 | 2 days, 0:00:00 | -5 days, 0:00:00 | None |\n\n"
            "_This report was generated with the [Issue Metrics Action](https://github.com/github-community-projects/issue-metrics)_\n"
            "Search query used to find these items: `is:issue is:open label:bug`\n"
        )
        self.assertEqual(content, expected_content)
        os.remove("issue_metrics.md")

    def test_write_to_markdown_with_vertical_bar_in_title(self):
        """Test that write_to_markdown writes the correct markdown file when the title contains a vertical bar.

        This test creates a list of mock GitHub issues (one of which contains a vertical
        bar in the title) with time to first response attributes, calls write_to_markdown
        with the list and the average time to first response, time to close and checks
        that the function writes the correct markdown file.

        """
        # Create mock data
        issues_with_metrics = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://github.com/user/repo/issues/1",
                author="alice",
                assignee="charlie",
                assignees=["charlie"],
                created_at=timedelta(days=-5),
                time_to_first_response=timedelta(days=1),
                time_to_close=timedelta(days=2),
                time_to_answer=timedelta(days=3),
                time_in_draft=timedelta(days=1),
                labels_metrics={"bug": timedelta(days=1)},
            ),
            IssueWithMetrics(
                title="feat| Issue 2",  # title contains a vertical bar
                html_url="https://github.com/user/repo/issues/2",
                author="bob",
                assignee=None,
                assignees=[],
                created_at=timedelta(days=-5),
                time_to_first_response=timedelta(days=3),
                time_to_close=timedelta(days=4),
                time_to_answer=timedelta(days=5),
                time_in_draft=None,
                labels_metrics={"bug": timedelta(days=2)},
            ),
        ]
        average_time_to_first_response = {
            "avg": timedelta(days=2),
            "med": timedelta(days=2),
            "90p": timedelta(days=2),
        }
        average_time_to_close = {
            "avg": timedelta(days=3),
            "med": timedelta(days=3),
            "90p": timedelta(days=3),
        }
        average_time_to_answer = {
            "avg": timedelta(days=4),
            "med": timedelta(days=4),
            "90p": timedelta(days=4),
        }
        average_time_in_draft = {
            "avg": timedelta(days=1),
            "med": timedelta(days=1),
            "90p": timedelta(days=1),
        }
        average_time_in_labels = {
            "avg": {"bug": "1 day, 12:00:00"},
            "med": {"bug": "1 day, 12:00:00"},
            "90p": {"bug": "1 day, 12:00:00"},
        }

        num_issues_opened = 2
        num_issues_closed = 1
        num_mentor_count = 5

        # Call the function
        write_to_markdown(
            issues_with_metrics=issues_with_metrics,
            average_time_to_first_response=average_time_to_first_response,
            average_time_to_first_review=None,
            average_time_to_close=average_time_to_close,
            average_time_to_answer=average_time_to_answer,
            average_time_in_draft=average_time_in_draft,
            average_time_in_labels=average_time_in_labels,
            stats_pr_comments=None,
            num_issues_opened=num_issues_opened,
            num_issues_closed=num_issues_closed,
            num_mentor_count=num_mentor_count,
            labels=["bug"],
            report_title="Issue Metrics",
            output_file="issue_metrics.md",
        )

        # Check that the function writes the correct markdown file
        with open("issue_metrics.md", "r", encoding="utf-8") as file:
            content = file.read()
        expected_content = (
            "# Issue Metrics\n\n"
            "| Metric | Average | Median | 90th percentile |\n"
            "| --- | --- | --- | ---: |\n"
            "| Time to first response | 2 days, 0:00:00 | 2 days, 0:00:00 | 2 days, 0:00:00 |\n"
            "| Time to first review | None | None | None |\n"
            "| Time to close | 3 days, 0:00:00 | 3 days, 0:00:00 | 3 days, 0:00:00 |\n"
            "| Time to answer | 4 days, 0:00:00 | 4 days, 0:00:00 | 4 days, 0:00:00 |\n"
            "| Time in draft | 1 day, 0:00:00 | 1 day, 0:00:00 | 1 day, 0:00:00 |\n"
            "| Time spent in bug | 1 day, 12:00:00 | 1 day, 12:00:00 | 1 day, 12:00:00 |\n"
            "| Status | | | |\n"
            "\n"
            "| Metric | Count |\n"
            "| --- | ---: |\n"
            "| Number of items that remain open | 2 |\n"
            "| Number of items closed | 1 |\n"
            "| Total number of items created | 2 |\n\n"
            "| Title | URL | Assignee | Author | Time to first response | Time to first review | Time to close | "
            "Time to answer | Time in draft | Time spent in bug | Created At | Status |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| Issue 1 | https://github.com/user/repo/issues/1 | [charlie](https://github.com/charlie) | "
            "[alice](https://github.com/alice) | 1 day, 0:00:00 | None | 2 days, 0:00:00 | 3 days, 0:00:00 | "
            "1 day, 0:00:00 | 1 day, 0:00:00 | -5 days, 0:00:00 | None |\n"
            "| feat&#124; Issue 2 | https://github.com/user/repo/issues/2 | None | "
            "[bob](https://github.com/bob) | 3 days, 0:00:00 | None | "
            "4 days, 0:00:00 | 5 days, 0:00:00 | None | 2 days, 0:00:00 | -5 days, 0:00:00 | None |\n\n"
            "_This report was generated with the [Issue Metrics Action](https://github.com/github-community-projects/issue-metrics)_\n"
        )
        self.assertEqual(content, expected_content)
        os.remove("issue_metrics.md")

    def test_write_to_markdown_no_issues(self):
        """Test that write_to_markdown writes the correct markdown file when no issues are found."""
        # Call the function with no issues
        with patch("builtins.open", mock_open()) as mock_open_file:
            write_to_markdown(
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                report_title="Issue Metrics",
            )

        # Check that the file was written correctly
        expected_output = [
            "# Issue Metrics\n\n",
            "no issues found for the given search criteria\n\n",
            "\n_This report was generated with the [Issue Metrics Action](https://github.com/github-community-projects/issue-metrics)_\n",
        ]
        # Check that the markdown file was written with the three calls in expected output
        mock_open_file.assert_has_calls(
            [
                call().write(expected_output[0]),
                call().write(expected_output[1]),
                call().write(expected_output[2]),
            ]
        )


@patch.dict(
    os.environ,
    {
        "SEARCH_QUERY": "is:open repo:user/repo",
        "GH_TOKEN": "test_token",
        "HIDE_CREATED_AT": "False",
        "HIDE_TIME_TO_FIRST_RESPONSE": "True",
        "HIDE_TIME_TO_FIRST_REVIEW": "True",
        "HIDE_TIME_TO_CLOSE": "True",
        "HIDE_TIME_TO_ANSWER": "True",
        "HIDE_LABEL_METRICS": "True",
        "NON_MENTIONING_LINKS": "True",
        "GH_ENTERPRISE_URL": "https://ghe.com",
        "HIDE_STATUS": "False",
    },
)
class TestWriteToMarkdownWithEnv(unittest.TestCase):
    """Test the write_to_markdown function with the following environment variables set:
    - HIDE*,
    - NON_MENTIONING_LINKS
    - GH_ENTERPRISE_URL
    """

    def test_writes_markdown_file_with_non_hidden_columns_only(self):
        """
        Test that write_to_markdown writes the correct
        markdown file with non-hidden columns only.
        """

        # Create mock data
        issues_with_metrics = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://ghe.com/user/repo/issues/1",
                author="alice",
                assignee="charlie",
                assignees=["charlie"],
                created_at=timedelta(days=-5),
                time_to_first_response=timedelta(minutes=10),
                time_to_close=timedelta(days=1),
                time_to_answer=timedelta(hours=2),
                time_in_draft=timedelta(days=1),
                labels_metrics={
                    "label1": timedelta(days=1),
                },
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://ghe.com/user/repo/issues/2",
                author="bob",
                assignee=None,
                assignees=[],
                created_at=timedelta(days=-5),
                time_to_first_response=timedelta(minutes=20),
                time_to_close=timedelta(days=2),
                time_to_answer=timedelta(hours=4),
                labels_metrics={
                    "label1": timedelta(days=1),
                },
            ),
        ]
        average_time_to_first_response = timedelta(minutes=15)
        average_time_to_close = timedelta(days=1.5)
        average_time_to_answer = timedelta(hours=3)
        average_time_in_draft = timedelta(days=1)
        average_time_in_labels = {
            "label1": timedelta(days=1),
        }
        num_issues_opened = 2
        num_issues_closed = 2
        num_mentor_count = 5
        ghe = "https://ghe.com"

        # Call the function
        write_to_markdown(
            issues_with_metrics=issues_with_metrics,
            average_time_to_first_response=average_time_to_first_response,
            average_time_to_first_review=None,
            average_time_to_close=average_time_to_close,
            average_time_to_answer=average_time_to_answer,
            average_time_in_draft=average_time_in_draft,
            average_time_in_labels=average_time_in_labels,
            stats_pr_comments=None,
            num_issues_opened=num_issues_opened,
            num_issues_closed=num_issues_closed,
            num_mentor_count=num_mentor_count,
            labels=["label1"],
            search_query="repo:user/repo is:issue",
            hide_label_metrics=True,
            hide_items_closed_count=True,
            enable_mentor_count=True,
            non_mentioning_links=True,
            report_title="Issue Metrics",
            output_file="issue_metrics.md",
            ghe=ghe,
        )

        # Check that the function writes the correct markdown file
        with open("issue_metrics.md", "r", encoding="utf-8") as file:
            content = file.read()

        expected_content = (
            "# Issue Metrics\n\n"
            "| Metric | Count |\n"
            "| --- | ---: |\n"
            "| Number of items that remain open | 2 |\n"
            "| Number of most active mentors | 5 |\n"
            "| Total number of items created | 2 |\n\n"
            "| Title | URL | Assignee | Author | Created At | Status |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            "| Issue 1 | https://www.ghe.com/user/repo/issues/1 | [charlie](https://ghe.com/charlie) | "
            "[alice](https://ghe.com/alice) | -5 days, 0:00:00 | None |\n"
            "| Issue 2 | https://www.ghe.com/user/repo/issues/2 | None | "
            "[bob](https://ghe.com/bob) | -5 days, 0:00:00 | None |\n\n"
            "_This report was generated with the [Issue Metrics Action](https://github.com/github-community-projects/issue-metrics)_\n"
            "Search query used to find these items: `repo:user/repo is:issue`\n"
        )
        self.assertEqual(content, expected_content)
        os.remove("issue_metrics.md")

    @patch.dict(
        os.environ,
        {
            "SEARCH_QUERY": "is:open repo:user/repo",
            "GH_TOKEN": "test_token",
            "HIDE_CREATED_AT": "False",
            "HIDE_TIME_TO_FIRST_RESPONSE": "True",
            "HIDE_TIME_TO_FIRST_REVIEW": "True",
            "HIDE_TIME_TO_CLOSE": "True",
            "HIDE_TIME_TO_ANSWER": "True",
            "HIDE_LABEL_METRICS": "True",
            "NON_MENTIONING_LINKS": "True",
            "GH_ENTERPRISE_URL": "https://ghe.com",
            "HIDE_STATUS": "True",  # Status column should be hidden
        },
    )
    def test_writes_markdown_file_with_hidden_status_column(self):
        """
        Test that write_to_markdown writes the correct markdown file
        when HIDE_STATUS is set to True, ensuring the Status column
        is not present in the output.
        """
        # Create mock data
        issues_with_metrics = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://ghe.com/user/repo/issues/1",
                author="alice",
                assignee="charlie",
                assignees=["charlie"],
                created_at=timedelta(days=-5),
                time_to_first_response=timedelta(minutes=10),
                time_to_close=timedelta(days=1),
                time_to_answer=timedelta(hours=2),
                time_in_draft=timedelta(days=1),
                labels_metrics={
                    "label1": timedelta(days=1),
                },
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://ghe.com/user/repo/issues/2",
                author="bob",
                assignee=None,
                assignees=[],
                created_at=timedelta(days=-5),
                time_to_first_response=timedelta(minutes=20),
                time_to_close=timedelta(days=2),
                time_to_answer=timedelta(hours=4),
                labels_metrics={
                    "label1": timedelta(days=1),
                },
            ),
        ]
        average_time_to_first_response = timedelta(minutes=15)
        average_time_to_close = timedelta(days=1.5)
        average_time_to_answer = timedelta(hours=3)
        average_time_in_draft = timedelta(days=1)
        average_time_in_labels = {
            "label1": timedelta(days=1),
        }
        num_issues_opened = 2
        num_issues_closed = 2
        num_mentor_count = 5
        ghe = "https://ghe.com"

        # Call the function
        write_to_markdown(
            issues_with_metrics=issues_with_metrics,
            average_time_to_first_response=average_time_to_first_response,
            average_time_to_first_review=None,
            average_time_to_close=average_time_to_close,
            average_time_to_answer=average_time_to_answer,
            average_time_in_draft=average_time_in_draft,
            average_time_in_labels=average_time_in_labels,
            stats_pr_comments=None,
            num_issues_opened=num_issues_opened,
            num_issues_closed=num_issues_closed,
            num_mentor_count=num_mentor_count,
            labels=["label1"],
            search_query="repo:user/repo is:issue",
            hide_label_metrics=True,
            hide_items_closed_count=True,
            enable_mentor_count=True,
            non_mentioning_links=True,
            report_title="Issue Metrics",
            output_file="issue_metrics.md",
            ghe=ghe,
        )

        # Check that the function writes the correct markdown file
        with open("issue_metrics.md", "r", encoding="utf-8") as file:
            content = file.read()

        expected_content = (
            "# Issue Metrics\n\n"
            "| Metric | Count |\n"
            "| --- | ---: |\n"
            "| Number of items that remain open | 2 |\n"
            "| Number of most active mentors | 5 |\n"
            "| Total number of items created | 2 |\n\n"
            "| Title | URL | Assignee | Author | Created At |\n"  # Status column should be missing
            "| --- | --- | --- | --- | --- |\n"
            "| Issue 1 | https://www.ghe.com/user/repo/issues/1 | [charlie](https://ghe.com/charlie) | "
            "[alice](https://ghe.com/alice) | -5 days, 0:00:00 |\n"
            "| Issue 2 | https://www.ghe.com/user/repo/issues/2 | None | [bob](https://ghe.com/bob) | -5 days, 0:00:00 |\n\n"
            "_This report was generated with the [Issue Metrics Action](https://github.com/github-community-projects/issue-metrics)_\n"
            "Search query used to find these items: `repo:user/repo is:issue`\n"
        )
        self.assertEqual(content, expected_content)
        os.remove("issue_metrics.md")

    @patch.dict(
        os.environ,
        {
            "SEARCH_QUERY": "is:open repo:user/repo",
            "GH_TOKEN": "test_token",
            "HIDE_CREATED_AT": "False",
            "HIDE_TIME_TO_FIRST_RESPONSE": "True",
            "HIDE_TIME_TO_FIRST_REVIEW": "True",
            "HIDE_TIME_TO_CLOSE": "True",
            "HIDE_TIME_TO_ANSWER": "True",
            "HIDE_LABEL_METRICS": "True",
            "NON_MENTIONING_LINKS": "True",
            "GH_ENTERPRISE_URL": "https://ghe.com",
            "HIDE_STATUS": "True",  # Status column should be hidden
            "HIDE_ITEMS_LIST": "True",  # Hide the items list table
        },
    )
    def test_writes_markdown_file_with_hidden_items_list(self):
        """
        Test that write_to_markdown writes the correct markdown file
        when HIDE_ITEMS_LIST is set to True, ensuring the individual
        items table is not present in the output.
        """
        # Create mock data
        issues_with_metrics = [
            IssueWithMetrics(
                title="Issue 1",
                html_url="https://ghe.com/user/repo/issues/1",
                author="alice",
                assignee="charlie",
                assignees=["charlie"],
                created_at=timedelta(days=-5),
                time_to_first_response=timedelta(minutes=10),
                time_to_close=timedelta(days=1),
                time_to_answer=timedelta(hours=2),
                time_in_draft=timedelta(days=1),
                labels_metrics={
                    "label1": timedelta(days=1),
                },
            ),
            IssueWithMetrics(
                title="Issue 2",
                html_url="https://ghe.com/user/repo/issues/2",
                author="bob",
                assignee=None,
                assignees=[],
                created_at=timedelta(days=-5),
                time_to_first_response=timedelta(minutes=20),
                time_to_close=timedelta(days=2),
                time_to_answer=timedelta(hours=4),
                labels_metrics={
                    "label1": timedelta(days=1),
                },
            ),
        ]
        average_time_to_first_response = timedelta(minutes=15)
        average_time_to_close = timedelta(days=1.5)
        average_time_to_answer = timedelta(hours=3)
        average_time_in_draft = timedelta(days=1)
        average_time_in_labels = {
            "label1": timedelta(days=1),
        }
        num_issues_opened = 2
        num_issues_closed = 2
        num_mentor_count = 5
        ghe = "https://ghe.com"

        # Call the function
        write_to_markdown(
            issues_with_metrics=issues_with_metrics,
            average_time_to_first_response=average_time_to_first_response,
            average_time_to_first_review=None,
            average_time_to_close=average_time_to_close,
            average_time_to_answer=average_time_to_answer,
            average_time_in_draft=average_time_in_draft,
            average_time_in_labels=average_time_in_labels,
            stats_pr_comments=None,
            num_issues_opened=num_issues_opened,
            num_issues_closed=num_issues_closed,
            num_mentor_count=num_mentor_count,
            labels=["label1"],
            search_query="repo:user/repo is:issue",
            hide_label_metrics=True,
            hide_items_closed_count=True,
            enable_mentor_count=True,
            non_mentioning_links=True,
            report_title="Issue Metrics",
            output_file="issue_metrics.md",
            ghe=ghe,
        )

        # Check that the function writes the correct markdown file
        with open("issue_metrics.md", "r", encoding="utf-8") as file:
            content = file.read()

        # Expected content should not include the individual items table
        expected_content = (
            "# Issue Metrics\n\n"
            "| Metric | Count |\n"
            "| --- | ---: |\n"
            "| Number of items that remain open | 2 |\n"
            "| Number of most active mentors | 5 |\n"
            "| Total number of items created | 2 |\n\n"
            "_This report was generated with the [Issue Metrics Action](https://github.com/github-community-projects/issue-metrics)_\n"
            "Search query used to find these items: `repo:user/repo is:issue`\n"
        )
        self.assertEqual(content, expected_content)
        os.remove("issue_metrics.md")


if __name__ == "__main__":
    unittest.main()
