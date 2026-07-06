"""A module for measuring the time it takes to get the first response to a GitHub issue.

This module provides functions for measuring the time it takes to get the first response
to a GitHub issue, as well as calculating the average time to first response for a list
of issues.

Functions:
    measure_time_to_first_response(
        issue: Union[github.Issue.Issue, None],
        discussion: Union[dict, None]
        pull_request: Union[github.PullRequest.PullRequest, None],
    ) -> Union[timedelta, None]:
        Measure the time to first response for a single issue or a discussion.
    get_stats_time_to_first_response(
        issues: List[IssueWithMetrics]
    ) -> Union[timedelta, None]:
        Calculate stats describing time to first response for a list of issues with metrics.

"""

from datetime import datetime, timedelta
from typing import List, Union

import numpy
from classes import IssueWithMetrics
from github.Issue import Issue
from github.PullRequest import PullRequest


def measure_time_to_first_response(
    issue: Union[Issue, None],
    discussion: Union[dict, None],
    pull_request: Union[PullRequest, None] = None,
    ready_for_review_at: Union[datetime, None] = None,
    ignore_users: Union[List[str], None] = None,
) -> Union[timedelta, None]:
    """Measure the time to first response for a single issue, pull request, or a discussion.

    Args:
        issue (Union[Issue, None]): A GitHub issue.
        discussion (Union[dict, None]): A GitHub discussion.
        pull_request (Union[PullRequest, None]): A GitHub pull request.
        ignore_users (List[str]): A list of GitHub usernames to ignore.

    Returns:
        Union[timedelta, None]: The time to first response for the issue/discussion.

    """
    first_review_comment_time = None
    first_comment_time = None
    earliest_response = None
    issue_time = None
    if ignore_users is None:
        ignore_users = []

    # Get the first comment time
    if issue:
        comments = issue.get_comments()
        for comment in comments:
            if ignore_comment(
                issue.user,
                comment.user,
                ignore_users,
                comment.created_at,
                ready_for_review_at,
            ):
                continue
            first_comment_time = comment.created_at
            break

        # Check if the issue is actually a pull request
        # so we may also get the first review comment time
        if pull_request:
            review_comments = pull_request.get_reviews()
            try:
                for review_comment in review_comments:
                    if ignore_comment(
                        issue.user,
                        review_comment.user,
                        ignore_users,
                        review_comment.submitted_at,
                        ready_for_review_at,
                    ):
                        continue
                    first_review_comment_time = review_comment.submitted_at
                    break
            except TypeError as e:
                print(
                    f"An error occurred processing review comments. Perhaps the review contains a ghost user. {e}"
                )

        # Figure out the earliest response timestamp
        if first_comment_time and first_review_comment_time:
            earliest_response = min(first_comment_time, first_review_comment_time)
        elif first_comment_time:
            earliest_response = first_comment_time
        elif first_review_comment_time:
            earliest_response = first_review_comment_time
        else:
            return None

        # Get the created_at time for the issue so we can calculate the time to first response
        if ready_for_review_at:
            issue_time = ready_for_review_at
        else:
            issue_time = issue.created_at

    if discussion and len(discussion["comments"]["nodes"]) > 0:
        earliest_response = datetime.fromisoformat(
            discussion["comments"]["nodes"][0]["createdAt"]
        )
        issue_time = datetime.fromisoformat(discussion["createdAt"])

    if earliest_response and issue_time:
        time_between_issue_and_first_comment: timedelta | None = (
            earliest_response - issue_time
        )
        return time_between_issue_and_first_comment

    return None


def ignore_comment(
    issue_user,
    comment_user,
    ignore_users: List[str],
    comment_created_at: datetime,
    ready_for_review_at: Union[datetime, None],
) -> bool:
    """Check if a comment should be ignored."""

    # PyGithub returns None for ghost (deleted) users
    if comment_user is None:
        return True

    user_is_ignored: bool = comment_user.login in ignore_users
    user_is_a_bot: bool = str(comment_user.type.lower()) == "bot"
    user_is_issue_creator: bool = str(comment_user.login) == str(issue_user.login)
    issue_was_created_before_ready_for_review: bool = False
    is_pending_comment: bool = not isinstance(comment_created_at, datetime)
    if ready_for_review_at and not is_pending_comment:
        issue_was_created_before_ready_for_review = (
            comment_created_at < ready_for_review_at
        )
    result: bool = (
        user_is_ignored
        or user_is_a_bot
        or user_is_issue_creator
        or is_pending_comment
        or issue_was_created_before_ready_for_review
    )
    return result


def get_stats_time_to_first_response(
    issues: List[IssueWithMetrics],
) -> Union[dict[str, timedelta], None]:
    """Calculate the stats describing time to first response for a list of issues.

    Args:
        issues (List[IssueWithMetrics]): A list of GitHub issues with metrics attached.

    Returns:
        Union[Dict{String: datetime.timedelta}, None]: The stats describing time to first response for the issues in seconds.

    """
    response_times = []
    none_count = 0
    for issue in issues:
        if issue.time_to_first_response:
            response_times.append(issue.time_to_first_response.total_seconds())
        else:
            none_count += 1

    if len(issues) - none_count <= 0:
        return None

    average_seconds_to_first_response = numpy.round(numpy.average(response_times))
    med_seconds_to_first_response = numpy.round(numpy.median(response_times))
    ninety_percentile_seconds_to_first_response = numpy.round(
        numpy.percentile(response_times, 90, axis=0)
    )

    stats = {
        "avg": timedelta(seconds=average_seconds_to_first_response),
        "med": timedelta(seconds=med_seconds_to_first_response),
        "90p": timedelta(seconds=ninety_percentile_seconds_to_first_response),
    }

    # Print the average time to first response converting seconds to a readable time format
    print(
        f"Average time to first response: {timedelta(seconds=average_seconds_to_first_response)}"
    )

    return stats
