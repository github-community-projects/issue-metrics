"""A module for writing GitHub issue metrics to a json file.

Functions:
    write_to_json(
        issues_with_metrics: Union[List[IssueWithMetrics], None],
        stats_time_to_first_response: Union[dict[str, timedelta], None],
        stats_time_to_first_review: Union[dict[str, timedelta], None],
        stats_time_to_close: Union[dict[str, timedelta], None],
        stats_time_to_answer: Union[dict[str, timedelta], None],
        stats_time_in_draft: Union[dict[str, timedelta], None],
        stats_time_in_labels: Union[dict[str, dict[str, timedelta]], None],
        num_issues_opened: Union[int, None],
        num_issues_closed: Union[int, None],
        num_mentor_count: Union[int, None],
        search_query: str,
        output_file: str,
    ) -> str:
        Write the issues with metrics to a json file.

"""

import json
import os
from datetime import timedelta
from typing import Any, Dict, List, Union

from classes import IssueWithMetrics


def write_to_json(
    issues_with_metrics: Union[List[IssueWithMetrics], None],
    stats_time_to_first_response: Union[dict[str, timedelta], None],
    stats_time_to_first_review: Union[dict[str, timedelta], None],
    stats_time_to_close: Union[dict[str, timedelta], None],
    stats_time_to_answer: Union[dict[str, timedelta], None],
    stats_time_in_draft: Union[dict[str, timedelta], None],
    stats_time_in_labels: Union[dict[str, dict[str, timedelta]], None],
    stats_pr_comments: Union[Dict[str, float], None],
    num_issues_opened: Union[int, None],
    num_issues_closed: Union[int, None],
    num_mentor_count: Union[int, None],
    search_query: str,
    output_file: str,
) -> str:
    """
    Write the issues with metrics to a JSON file called issue_metrics.json.

    json structure is like following
    {
        "average_time_to_first_response": "None",
        "average_time_to_close": "None",
        "average_time_to_answer": "None",
        "average_time_in_draft": "None",
        "average_time_in_labels": {},
        "median_time_to_first_response": "None",
        "median_time_to_close": "None",
        "median_time_to_answer": "None",
        "median_time_in_draft": "None",
        "median_time_in_labels": {},
        "90_percentile_time_to_first_response": "None",
        "90_percentile_time_to_close": "None",
        "90_percentile_time_to_answer": "None",
        "90_percentile_time_in_draft": "None",
        "90_percentile_time_in_labels": {},
        "num_items_opened": 2,
        "num_items_closed": 0,
        "num_mentor_count": 5,
        "total_item_count": 2,
        "issues": [
            {
                "title": "Issue 1",
                "html_url": "https://github.com/owner/repo/issues/1",
                "author": "alice",
                "time_to_first_response": "None",
                "time_to_close": "None",
                "time_to_answer": "None",
                "time_in_draft": "None",
                "label_metrics": {}
            },
            {
                "title": "Issue 2",
                "html_url": "https://github.com/owner/repo/issues/2",
                "author": "bob",
                "time_to_first_response": "None",
                "time_to_close": "None",
                "time_to_answer": "None",
                "time_in_draft": "None",
                "label_metrics": {}
            }
        ],
        "search_query": "is:issue repo:owner/repo"
    }

    """

    # Ensure issues_with_metrics is not None
    if not issues_with_metrics:
        return ""

    # time to first response
    average_time_to_first_response = None
    med_time_to_first_response = None
    p90_time_to_first_response = None
    if stats_time_to_first_response is not None:
        average_time_to_first_response = stats_time_to_first_response["avg"]
        med_time_to_first_response = stats_time_to_first_response["med"]
        p90_time_to_first_response = stats_time_to_first_response["90p"]

    # time to first review
    average_time_to_first_review = None
    med_time_to_first_review = None
    p90_time_to_first_review = None
    if stats_time_to_first_review is not None:
        average_time_to_first_review = stats_time_to_first_review["avg"]
        med_time_to_first_review = stats_time_to_first_review["med"]
        p90_time_to_first_review = stats_time_to_first_review["90p"]

    # time to close
    average_time_to_close = None
    med_time_to_close = None
    p90_time_to_close = None
    if stats_time_to_close is not None:
        average_time_to_close = stats_time_to_close["avg"]
        med_time_to_close = stats_time_to_close["med"]
        p90_time_to_close = stats_time_to_close["90p"]

    # time to answer
    average_time_to_answer = None
    med_time_to_answer = None
    p90_time_to_answer = None
    if stats_time_to_answer is not None:
        average_time_to_answer = stats_time_to_answer["avg"]
        med_time_to_answer = stats_time_to_answer["med"]
        p90_time_to_answer = stats_time_to_answer["90p"]

    # time in draft
    average_time_in_draft = None
    med_time_in_draft = None
    p90_time_in_draft = None
    if stats_time_in_draft is not None:
        average_time_in_draft = stats_time_in_draft["avg"]
        med_time_in_draft = stats_time_in_draft["med"]
        p90_time_in_draft = stats_time_in_draft["90p"]

    # time in labels
    average_time_in_labels = {}
    med_time_in_labels = {}
    p90_time_in_labels = {}
    if stats_time_in_labels is not None:
        for label, time in stats_time_in_labels["avg"].items():
            average_time_in_labels[label] = str(time)
        for label, time in stats_time_in_labels["med"].items():
            med_time_in_labels[label] = str(time)
        for label, time in stats_time_in_labels["90p"].items():
            p90_time_in_labels[label] = str(time)

    # PR comments statistics
    average_pr_comments = None
    med_pr_comments = None
    p90_pr_comments = None
    if stats_pr_comments is not None:
        average_pr_comments = stats_pr_comments["avg"]
        med_pr_comments = stats_pr_comments["med"]
        p90_pr_comments = stats_pr_comments["90p"]

    # Create a dictionary with the metrics
    metrics: dict[str, Any] = {
        "average_time_to_first_response": str(average_time_to_first_response),
        "average_time_to_first_review": str(average_time_to_first_review),
        "average_time_to_close": str(average_time_to_close),
        "average_time_to_answer": str(average_time_to_answer),
        "average_time_in_draft": str(average_time_in_draft),
        "average_time_in_labels": average_time_in_labels,
        "median_time_to_first_response": str(med_time_to_first_response),
        "median_time_to_first_review": str(med_time_to_first_review),
        "median_time_to_close": str(med_time_to_close),
        "median_time_to_answer": str(med_time_to_answer),
        "median_time_in_draft": str(med_time_in_draft),
        "median_time_in_labels": med_time_in_labels,
        "90_percentile_time_to_first_response": str(p90_time_to_first_response),
        "90_percentile_time_to_first_review": str(p90_time_to_first_review),
        "90_percentile_time_to_close": str(p90_time_to_close),
        "90_percentile_time_to_answer": str(p90_time_to_answer),
        "90_percentile_time_in_draft": str(p90_time_in_draft),
        "90_percentile_time_in_labels": p90_time_in_labels,
        "average_pr_comments": average_pr_comments,
        "median_pr_comments": med_pr_comments,
        "90_percentile_pr_comments": p90_pr_comments,
        "num_items_opened": num_issues_opened,
        "num_items_closed": num_issues_closed,
        "num_mentor_count": num_mentor_count,
        "total_item_count": len(issues_with_metrics),
    }

    # Create a list of dictionaries with the issues and metrics
    issues = []
    for issue in issues_with_metrics:
        formatted_label_metrics = {}
        if issue.label_metrics:
            for label, time in issue.label_metrics.items():
                formatted_label_metrics[label] = str(time)
        issues.append(
            {
                "title": issue.title,
                "html_url": issue.html_url,
                "author": issue.author,
                "assignee": issue.assignee,
                "assignees": issue.assignees,
                "time_to_first_response": str(issue.time_to_first_response),
                "time_to_first_review": str(issue.time_to_first_review),
                "time_to_close": str(issue.time_to_close),
                "time_to_answer": str(issue.time_to_answer),
                "time_in_draft": str(issue.time_in_draft),
                "label_metrics": formatted_label_metrics,
                "pr_comment_count": issue.pr_comment_count,
                "created_at": str(issue.created_at),
            }
        )

    # Add the issues to the metrics dictionary
    metrics["issues"] = issues

    # Add the search query to the metrics dictionary
    metrics["search_query"] = search_query

    # add output to github action output
    # pylint: disable=unspecified-encoding
    metrics_json = json.dumps(metrics)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as file_handle:
            print(f"metrics={metrics_json}", file=file_handle)

    # Write the metrics to a JSON file
    output_file_name = output_file if output_file else "issue_metrics.json"
    with open(output_file_name, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=4)

    return metrics_json
