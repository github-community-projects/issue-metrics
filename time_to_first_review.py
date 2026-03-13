"""Utilities for measuring time to first review for pull requests."""

from datetime import datetime, timedelta
from typing import List, Union

import github3
import numpy
from classes import IssueWithMetrics
from time_to_first_response import ignore_comment


def measure_time_to_first_review(
    issue: Union[github3.issues.Issue, None],
    pull_request: Union[github3.pulls.PullRequest, None],
    ready_for_review_at: Union[datetime, None] = None,
    ignore_users: Union[List[str], None] = None,
) -> Union[timedelta, None]:
    """Measures duration between pull request creation time and the timestamp when the first review is submitted"""

    if not issue or not pull_request:
        return None

    if ignore_users is None:
        ignore_users = []

    first_review_time = None

    try:
        reviews = pull_request.reviews(number=50)
        for review in reviews:
            if ignore_comment(
                issue.issue.user,
                review.user,
                ignore_users,
                review.submitted_at,
                ready_for_review_at,
            ):
                continue

            first_review_time = review.submitted_at
            break

    except TypeError as e:
        print(
            f"An error occurred processing review comments. Perhaps the review contains a ghost user. {e}"
        )
        return None

    if first_review_time is None:
        return None

    if ready_for_review_at:
        pr_created_time = ready_for_review_at
    else:
        pr_created_time = datetime.fromisoformat(issue.created_at)

    return first_review_time - pr_created_time


def get_stats_time_to_first_review(
    issues: List[IssueWithMetrics],
) -> Union[dict[str, timedelta], None]:
    """Compute statistics (average, median, 90th percentile) for time to first review."""
    review_times = []
    none_count = 0
    for issue in issues:
        if issue.time_to_first_review:
            review_times.append(issue.time_to_first_review.total_seconds())
        else:
            none_count += 1

    if len(issues) - none_count <= 0:
        return None

    average_seconds_to_first_review = numpy.round(numpy.average(review_times))
    med_seconds_to_first_review = numpy.round(numpy.median(review_times))
    ninety_percentile_seconds_to_first_review = numpy.round(
        numpy.percentile(review_times, 90, axis=0)
    )

    stats = {
        "avg": timedelta(seconds=average_seconds_to_first_review),
        "med": timedelta(seconds=med_seconds_to_first_review),
        "90p": timedelta(seconds=ninety_percentile_seconds_to_first_review),
    }

    # Print the average time to first review converting seconds to a readable time format
    print(
        f"Average time to first review: {timedelta(seconds=average_seconds_to_first_review)}"
    )

    return stats
