"""A module for measuring the number of comments on pull requests.

This module provides functions for counting comments on GitHub pull requests,
excluding bot comments, and calculating statistics about comment counts.

Functions:
    count_pr_comments(
        issue: Union[github.Issue.Issue, None],
        pull_request: Union[github.PullRequest.PullRequest, None],
        ignore_users: Union[List[str], None] = None,
    ) -> Union[int, None]:
        Count the number of comments on a pull request, excluding bot comments.
    get_stats_pr_comments(
        issues_with_metrics: List[IssueWithMetrics],
    ) -> Union[dict[str, float], None]:
        Calculate stats describing the comment count for a list of pull requests.
"""

from typing import List, Union

import numpy
from classes import IssueWithMetrics
from github.Issue import Issue
from github.PullRequest import PullRequest


def count_pr_comments(
    issue: Union[Issue, None],
    pull_request: Union[PullRequest, None] = None,
    ignore_users: Union[List[str], None] = None,
) -> Union[int, None]:
    """Count the number of comments on a pull request, excluding bot comments.

    Args:
        issue (Union[Issue, None]): A GitHub issue.
        pull_request (Union[PullRequest, None]): A GitHub pull request.
        ignore_users (Union[List[str], None]): A list of GitHub usernames to ignore.

    Returns:
        Union[int, None]: The number of comments on the pull request, excluding bots.
                         Returns None if not a pull request.
    """
    if not pull_request or not issue:
        return None

    if ignore_users is None:
        ignore_users = []

    comment_count = 0

    # Count issue comments
    try:
        comments = issue.get_comments()
        for comment in comments:
            # Skip bot comments and ignored users
            if (
                str(comment.user.type.lower()) != "bot"
                and comment.user.login not in ignore_users
            ):
                comment_count += 1
    except (AttributeError, TypeError):
        # If we can't get comments, just continue
        pass

    # Count pull request review comments
    try:
        review_comments = pull_request.get_review_comments()
        for review_comment in review_comments:
            # Skip bot comments and ignored users
            if (
                str(review_comment.user.type.lower()) != "bot"
                and review_comment.user.login not in ignore_users
            ):
                comment_count += 1
    except (AttributeError, TypeError):
        # If we can't get review comments, just continue
        pass

    return comment_count


def get_stats_pr_comments(
    issues_with_metrics: List[IssueWithMetrics],
) -> Union[dict[str, float], None]:
    """Calculate stats describing the comment count for a list of pull requests.

    Args:
        issues_with_metrics (List[IssueWithMetrics]): A list of GitHub issues with metrics attached.

    Returns:
        Union[Dict[str, float], None]: The stats describing comment counts for PRs.
    """
    # Filter out issues that are not pull requests or have no comment count
    prs_with_comment_counts = [
        issue.pr_comment_count
        for issue in issues_with_metrics
        if issue.pr_comment_count is not None
    ]

    if not prs_with_comment_counts:
        return None

    # Calculate statistics
    average_comment_count = numpy.round(numpy.average(prs_with_comment_counts), 1)
    median_comment_count = numpy.round(numpy.median(prs_with_comment_counts), 1)
    ninety_percentile_comment_count = numpy.round(
        numpy.percentile(prs_with_comment_counts, 90), 1
    )

    stats = {
        "avg": average_comment_count,
        "med": median_comment_count,
        "90p": ninety_percentile_comment_count,
    }

    return stats
