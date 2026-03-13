#!/usr/bin/env python3

"""
Test to verify that the Status and Created At columns have their content aligned with headers.

This test specifically validates the fix for issue #568 where the Status and Created At
columns had their data swapped.
"""

import os
import unittest
from datetime import timedelta
from unittest.mock import patch

from classes import IssueWithMetrics
from markdown_writer import get_non_hidden_columns, write_to_markdown


@patch.dict(
    os.environ,
    {
        "SEARCH_QUERY": "is:open repo:user/repo",
        "GH_TOKEN": "test_token",
        "HIDE_CREATED_AT": "False",
        "HIDE_STATUS": "False",
    },
)
class TestColumnOrderFix(unittest.TestCase):
    """Test that Status and Created At columns have correct data."""

    def test_status_and_created_at_columns_alignment(self):
        """Test that Status and Created At columns show correct data values.

        This test specifically validates that:
        1. The Status column contains actual status values (not dates)
        2. The Created At column contains actual date values (not status)
        """
        # Create test data with clearly distinguishable Status and Created At values
        issues_with_metrics = [
            IssueWithMetrics(
                title="Test Issue",
                html_url="https://github.com/user/repo/issues/1",
                author="testuser",
                assignee="assignee1",
                assignees=["assignee1"],
                created_at="2023-01-01T00:00:00Z",  # This should appear in Created At column
                status="open",  # This should appear in Status column
                time_to_first_response=timedelta(days=1),
                time_to_close=timedelta(days=2),
                time_to_answer=timedelta(days=3),
            )
        ]

        # Call the function
        write_to_markdown(
            issues_with_metrics=issues_with_metrics,
            average_time_to_first_response=None,
            average_time_to_first_review=None,
            average_time_to_close=None,
            average_time_to_answer=None,
            average_time_in_draft=None,
            average_time_in_labels=None,
            stats_pr_comments=None,
            num_issues_opened=1,
            num_issues_closed=0,
            num_mentor_count=0,
            labels=None,
            search_query="is:issue is:open repo:user/repo",
            hide_label_metrics=True,
            hide_items_closed_count=False,
            enable_mentor_count=False,
            non_mentioning_links=False,
            report_title="Test Report",
            output_file="test_column_order.md",
        )

        # Read the generated markdown
        with open("test_column_order.md", "r", encoding="utf-8") as file:
            content = file.read()

        # The table should have the columns in the correct order
        # and the data should be properly aligned
        expected_header = (
            "| Title | URL | Assignee | Author | Time to first response | Time to first review | "
            "Time to close | Time to answer | Created At | Status |"
        )
        self.assertIn(expected_header, content)

        # Verify the data row has correct values in correct positions
        # The Created At column should contain the date value
        # The Status column should contain the status value
        expected_row = (
            "| Test Issue | https://github.com/user/repo/issues/1 | "
            "[assignee1](https://github.com/assignee1) | "
            "[testuser](https://github.com/testuser) | 1 day, 0:00:00 | "
            "None | 2 days, 0:00:00 | 3 days, 0:00:00 | 2023-01-01T00:00:00Z | open |"
        )
        self.assertIn(expected_row, content)

        # Clean up
        os.remove("test_column_order.md")

    def test_get_non_hidden_columns_order(self):
        """Test that get_non_hidden_columns returns columns in the correct order."""
        columns = get_non_hidden_columns(labels=None)

        # Find the indices of the Status and Created At columns
        try:
            created_at_index = columns.index("Created At")
            status_index = columns.index("Status")

            # Status should come after Created At
            self.assertGreater(
                status_index,
                created_at_index,
                "Status column should come after Created At column",
            )
        except ValueError:
            # If one of the columns is hidden, that's fine, but we shouldn't get here
            # given our environment variables
            self.fail("Both Status and Created At columns should be present")


if __name__ == "__main__":
    unittest.main()
