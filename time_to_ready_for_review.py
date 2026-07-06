"""A module for getting the time a pull request was marked as ready for review
after being in draft mode.

This module provides functions for getting the time a GitHub pull request was
marked as ready for review, if it was formerly in draft mode.

Functions:
    get_time_to_ready_for_review(
        issue: github.Issue.Issue,
        pull_request: github.PullRequest.PullRequest
    ) -> Union[datetime, None]:
        If a pull request was formerly a draft, get the time it was marked as
        ready for review.

"""

from datetime import datetime
from typing import Union

from github.Issue import Issue
from github.PullRequest import PullRequest


def get_time_to_ready_for_review(
    issue: Issue,
    pull_request: PullRequest,
) -> Union[datetime, None]:
    """If a pull request was formerly a draft, get the time it was marked as ready
    for review

    Args:
        issue (Issue): A GitHub issue.
        pull_request (PullRequest): A GitHub pull request.

    Returns:
        Union[datetime, None]: The time the pull request was marked as ready for review
    """
    if pull_request.draft:
        return None

    events = issue.get_events()
    try:
        for event in events:
            if event.event == "ready_for_review":
                return event.created_at
    except TypeError as e:
        print(
            f"An error occurred processing review events. Perhaps issue contains a ghost user. {e}"
        )
        return None

    return None
