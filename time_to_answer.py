"""A module for measuring the time it takes to answer a GitHub discussion.

This module provides functions for measuring the time it takes to answer a GitHub
discussion, as well as calculating stats describing the time to answer for a list of discussions.

Functions:
    get_stats_time_to_answer(
        issues_with_metrics: List[IssueWithMetrics]
    ) -> Union[timedelta, None]:
        Calculate stats describing the time to answer for a list of issues with metrics.
    measure_time_to_answer(
        discussion: dict
    ) -> Union[timedelta, None]:
        Measure the time it takes to answer a GitHub discussion.

"""

from datetime import datetime, timedelta

import numpy

from classes import IssueWithMetrics


def get_stats_time_to_answer(
    issues_with_metrics: list[IssueWithMetrics],
) -> dict[str, timedelta] | None:
    """
    Calculate stats describing the time to answer for a list of issues.
    """
    # Filter out issues with no time to answer
    issues_with_time_to_answer = [
        issue for issue in issues_with_metrics if issue.time_to_answer is not None
    ]

    # Calculate the total time to answer for all issues
    answer_times = []
    if issues_with_time_to_answer:
        for issue in issues_with_time_to_answer:
            if issue.time_to_answer:
                answer_times.append(issue.time_to_answer.total_seconds())

    # Calculate stats describing time to answer
    num_issues_with_time_to_answer = len(issues_with_time_to_answer)
    if num_issues_with_time_to_answer > 0:
        average_time_to_answer = numpy.round(numpy.average(answer_times))
        med_time_to_answer = numpy.round(numpy.median(answer_times))
        ninety_percentile_time_to_answer = numpy.round(
            numpy.percentile(answer_times, 90, axis=0)
        )
    else:
        return None

    stats = {
        "avg": timedelta(seconds=average_time_to_answer),
        "med": timedelta(seconds=med_time_to_answer),
        "90p": timedelta(seconds=ninety_percentile_time_to_answer),
    }

    # Print the average time to answer converting seconds to a readable time format
    print(f"Average time to answer: {timedelta(seconds=average_time_to_answer)}")
    return stats


def measure_time_to_answer(discussion: dict) -> timedelta | None:
    """Measure the time to answer for a discussion.

    Args:
        discussion (dict): A discussion object from the GitHub API.

    Returns:
        Union[timedelta, None]: The time to answer for the discussion.

    """
    if not discussion["answerChosenAt"]:
        return None

    if not discussion["createdAt"]:
        return None

    # Get the time to answer
    answer_time = datetime.fromisoformat(discussion["answerChosenAt"])
    created_time = datetime.fromisoformat(discussion["createdAt"])

    return answer_time - created_time
