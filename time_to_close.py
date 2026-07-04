"""A module for measuring the time it takes to close a GitHub issue or discussion.

This module provides functions for measuring the time it takes to close a GitHub issue
or discussion, as well as calculating stats describing the time to close for a list of issues.

Functions:
    measure_time_to_close(
        issue: Union[github.Issue.Issue, None],
        discussion: Union[dict, None]
    ) -> Union[timedelta, None]:
        Measure the time it takes to close an issue or discussion.
    get_stats_time_to_close(
        issues_with_metrics: List[IssueWithMetrics]
    ) -> Union[timedelta, None]:
        Calculate stats describing the time to close for a list of issues with metrics.

"""

from datetime import datetime, timedelta
from typing import List, Union

import numpy
from classes import IssueWithMetrics
from github.Issue import Issue


def measure_time_to_close(
    issue: Union[Issue, None], discussion: Union[dict, None]
) -> Union[timedelta, None]:
    """Measure the time it takes to close an issue or discussion.

    Args:
        issue (Union[Issue, None]): A GitHub issue.
        discussion (Union[dict, None]): A GitHub discussion.

    Returns:
        Union[datetime.timedelta, None]: The time it takes to close the issue.

    """
    closed_at, created_at = None, None
    if issue:
        if issue.state != "closed":
            return None
        closed_at = issue.closed_at
        created_at = issue.created_at

    if discussion:
        if discussion["closedAt"] is None:
            return None
        closed_at = datetime.fromisoformat(discussion["closedAt"])
        created_at = datetime.fromisoformat(discussion["createdAt"])

    if closed_at and created_at:
        return closed_at - created_at
    return None


def get_stats_time_to_close(
    issues_with_metrics: List[IssueWithMetrics],
) -> Union[dict[str, timedelta], None]:
    """Calculate stats describing the time to close for a list of issues.

    Args:
        issues_with_metrics (List[IssueWithMetrics]): A list of issues with metrics.
            Each issue should be a issue_with_metrics tuple.

    Returns:
        Union[Dict{string: float}, None]: Stats describing the time to close for the issues.

    """
    # Filter out issues with no time to close
    issues_with_time_to_close = [
        issue for issue in issues_with_metrics if issue.time_to_close is not None
    ]

    # Calculate the total time to close for all issues
    close_times = []
    total_time_to_close = None
    if issues_with_time_to_close:
        total_time_to_close = 0
        for issue in issues_with_time_to_close:
            if issue.time_to_close:
                close_times.append(issue.time_to_close.total_seconds())

    # Calculate stats describing time to close
    num_issues_with_time_to_close = len(issues_with_time_to_close)
    if num_issues_with_time_to_close > 0 and total_time_to_close is not None:
        average_time_to_close = numpy.round(numpy.average(close_times))
        med_time_to_close = numpy.round(numpy.median(close_times))
        ninety_percentile_time_to_close = numpy.round(
            numpy.percentile(close_times, 90, axis=0)
        )
    else:
        return None

    stats = {
        "avg": timedelta(seconds=average_time_to_close),
        "med": timedelta(seconds=med_time_to_close),
        "90p": timedelta(seconds=ninety_percentile_time_to_close),
    }

    # Print the average time to close converting seconds to a readable time format
    print(f"Time to close: {timedelta(seconds=average_time_to_close)}")
    return stats
