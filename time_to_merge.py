"""A module for measuring the time it takes to merge a GitHub pull request.

This module provides functions for measuring the time it takes to merge a GitHub pull
request, as well as calculating the average time to merge for a list of pull requests.

Functions:
    measure_time_to_merge(
        pull_request: github.PullRequest.PullRequest,
        ready_for_review_at: Union[datetime, None]
    ) -> Union[timedelta, None]:
        Measure the time it takes to merge a pull request.

"""

from datetime import datetime, timedelta
from typing import Union

from github.PullRequest import PullRequest


def measure_time_to_merge(
    pull_request: PullRequest, ready_for_review_at: Union[datetime, None]
) -> Union[timedelta, None]:
    """Measure the time it takes to merge a pull request.

    Args:
        pull_request (PullRequest): A GitHub pull request.
        ready_for_review_at (Union[datetime, None]): When the PR was marked as ready for review

    Returns:
        Union[datetime.timedelta, None]: The time it takes to close the issue.

    """
    merged_at = None
    if pull_request.merged_at is None:
        return None

    merged_at = pull_request.merged_at

    if ready_for_review_at:
        return merged_at - ready_for_review_at

    created_at = pull_request.created_at
    return merged_at - created_at
