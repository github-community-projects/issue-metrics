"""Integration test for assignee functionality."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from classes import IssueWithMetrics
from json_writer import write_to_json
from markdown_writer import write_to_markdown


class TestAssigneeIntegration(unittest.TestCase):
    """Integration test for assignee functionality."""

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "repo:test/repo is:issue",
        },
        clear=True,
    )
    def test_assignee_in_markdown_output(self):
        """Test that assignee information appears correctly in markdown output."""
        issues_with_metrics = [
            IssueWithMetrics(
                title="Test Issue 1",
                html_url="https://github.com/test/repo/issues/1",
                author="john",
                assignee="alice",
                assignees=["alice"],
                time_to_first_response=timedelta(hours=2),
                time_to_close=timedelta(days=1),
                created_at=datetime.now() - timedelta(days=2),
            ),
            IssueWithMetrics(
                title="Test Issue 2",
                html_url="https://github.com/test/repo/issues/2",
                author="jane",
                assignee=None,
                assignees=[],
                time_to_first_response=timedelta(hours=4),
                time_to_close=None,
                created_at=datetime.now() - timedelta(days=1),
            ),
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_file = f.name

        try:
            write_to_markdown(
                issues_with_metrics=issues_with_metrics,
                average_time_to_first_review=None,
                average_time_to_first_response={
                    "avg": timedelta(hours=3),
                    "med": timedelta(hours=3),
                    "90p": timedelta(hours=4),
                },
                average_time_to_close={
                    "avg": timedelta(days=1),
                    "med": timedelta(days=1),
                    "90p": timedelta(days=1),
                },
                average_time_to_answer=None,
                average_time_in_draft=None,
                average_time_in_labels=None,
                stats_pr_comments=None,
                num_issues_opened=2,
                num_issues_closed=1,
                num_mentor_count=0,
                labels=None,
                search_query="repo:test/repo is:issue",
                hide_label_metrics=True,
                hide_items_closed_count=False,
                enable_mentor_count=False,
                non_mentioning_links=False,
                report_title="Test Issue Metrics",
                output_file=output_file,
                ghe="",
            )

            # Read and verify the markdown content
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for assignee column header
            self.assertIn("| Assignee |", content)

            # Check for assignee data - alice should be linked
            self.assertIn("[alice](https://github.com/alice)", content)

            # Check for None assignee
            self.assertIn("| None |", content)

            # Check that both assignee and author columns are present
            self.assertIn("| Author |", content)

        finally:
            os.unlink(output_file)

    def test_assignee_in_json_output(self):
        """Test that assignee information appears correctly in JSON output."""
        issues_with_metrics = [
            IssueWithMetrics(
                title="Test Issue 1",
                html_url="https://github.com/test/repo/issues/1",
                author="john",
                assignee="alice",
                assignees=["alice", "bob"],
                time_to_first_response=timedelta(hours=2),
                time_to_close=timedelta(days=1),
                created_at=datetime.now() - timedelta(days=2),
            ),
            IssueWithMetrics(
                title="Test Issue 2",
                html_url="https://github.com/test/repo/issues/2",
                author="jane",
                assignee=None,
                assignees=[],
                time_to_first_response=timedelta(hours=4),
                time_to_close=None,
                created_at=datetime.now() - timedelta(days=1),
            ),
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            json_output = write_to_json(
                issues_with_metrics=issues_with_metrics,
                stats_time_to_first_review=None,
                stats_time_to_first_response={
                    "avg": timedelta(hours=3),
                    "med": timedelta(hours=3),
                    "90p": timedelta(hours=4),
                },
                stats_time_to_close={
                    "avg": timedelta(days=1),
                    "med": timedelta(days=1),
                    "90p": timedelta(days=1),
                },
                stats_time_to_answer=None,
                stats_time_in_draft=None,
                stats_time_in_labels=None,
                stats_pr_comments=None,
                num_issues_opened=2,
                num_issues_closed=1,
                num_mentor_count=0,
                search_query="repo:test/repo is:issue",
                output_file=output_file,
            )

            # Parse the JSON output
            data = json.loads(json_output)

            # Check that assignee fields are present
            issue1 = data["issues"][0]
            self.assertEqual(issue1["assignee"], "alice")
            self.assertEqual(issue1["assignees"], ["alice", "bob"])
            self.assertEqual(issue1["author"], "john")

            issue2 = data["issues"][1]
            self.assertIsNone(issue2["assignee"])
            self.assertEqual(issue2["assignees"], [])
            self.assertEqual(issue2["author"], "jane")

        finally:
            os.unlink(output_file)


if __name__ == "__main__":
    unittest.main()
