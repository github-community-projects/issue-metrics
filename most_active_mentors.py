"""A module for measuring the number of very active mentors

This module provides functions for measuring the number of active mentors on a
project.

This is measured by number of PR comments. We are working under the assumption
that PR comments are left in good faith to move contributors further instead of
nitpicking and discouraging them.

Open questions:
   - should there be an option to limit this to certain users, e.g. core
     maintainers?
   - should there be a limit to how many comments per PR we consider to avoid
     having the statistic dominated by contested PRs?
   - should this metric count consecutive comments coming from the same user as
     only one to avoid people unnecessarily splitting their comments to game the
     metric?
   - instead of PR comments should we count PRs on which a username was seen as
     commenter?

Functions:
    collect_response_usernames(
        issue: Union[github.Issue.Issue, None],
        discussion: Union[dict, None],
        pull_request: Union[github.PullRequest.PullRequest, None],
        max_comments_to_evaluate,
    ) -> ____________
         Collect the number of responses per username for single item. Take only
         top n comments (max_comments_to_evaluate) into consideration.
    get_number_of_active_reviewers(
        mentors: List [mentors with metrics)
        ) -> int active_number
        Count the number of mentors active at least n times

"""

from collections import Counter
from datetime import datetime

from github.Issue import Issue
from github.PullRequest import PullRequest

from classes import IssueWithMetrics


def count_comments_per_user(
    issue: Issue | None,
    discussion: dict | None = None,
    pull_request: PullRequest | None = None,
    ready_for_review_at: datetime | None = None,
    ignore_users: list[str] | None = None,
    max_comments_to_eval=20,
    heavily_involved=3,
) -> dict:
    """Count the number of times a user was seen commenting on a single item.

    Args:
        issue (Union[Issue, None]): A GitHub issue.
        discussion (Union[dict, None]): A GitHub discussion as returned by
        discussions.get_discussions (a plain GraphQL dict, not a PyGithub
        object).
        pull_request (Union[PullRequest, None]): A GitHub pull
        request.
        ready_for_review_at (Union[datetime, None]): When the item became
        ready for review; comments before this are ignored.
        ignore_users (List[str]): A list of GitHub usernames to ignore.
        max_comments_to_eval: Maximum number of comments per item to look at.
        heavily_involved: Maximum number of comments to count for one
        user per issue.

    Returns:
        dict: A dictionary of usernames seen and number of comments they left.

    """
    if ignore_users is None:
        ignore_users = []
    mentor_count: dict[str, int] = {}

    # Get the first comments
    if issue:
        comments = issue.get_comments()
        comment_count = 0
        for comment in comments:
            if comment_count >= max_comments_to_eval:
                break
            comment_count += 1
            if ignore_comment(
                issue.user,
                comment.user,
                ignore_users,
                comment.created_at,
                ready_for_review_at,
            ):
                continue
            # increase the number of comments left by current user by 1
            if comment.user.login in mentor_count:
                if mentor_count[comment.user.login] < heavily_involved:
                    mentor_count[comment.user.login] += 1
            else:
                mentor_count[comment.user.login] = 1

        # Check if the issue is actually a pull request
        # so we may also get the first review comment time
        if pull_request:
            review_comments = pull_request.get_reviews()
            review_count = 0
            for review_comment in review_comments:
                if review_count >= max_comments_to_eval:
                    break
                review_count += 1
                if ignore_comment(
                    issue.user,
                    review_comment.user,
                    ignore_users,
                    review_comment.submitted_at,
                    ready_for_review_at,
                ):
                    continue

                # increase the number of comments left by current user by 1
                if review_comment.user.login in mentor_count:
                    mentor_count[review_comment.user.login] += 1
                else:
                    mentor_count[review_comment.user.login] = 1

    # The discussion branch: use dict access because GraphQL returns plain
    # dicts (not PyGithub objects). Filtering is inlined here (rather than
    # reusing ignore_comment, which expects PyGithub objects): the discussion
    # author's login is compared against each comment author to drop
    # self-comments.
    if discussion and len(discussion["comments"]["nodes"]) > 0:
        discussion_author_login = (discussion.get("author") or {}).get("login", "")
        comment_count = 0
        for comment in discussion["comments"]["nodes"]:
            if comment_count >= max_comments_to_eval:
                break
            comment_count += 1
            comment_author = comment.get("author") or {}
            comment_login = comment_author.get("login", "")
            comment_type = comment_author.get("__typename", "")
            comment_created_at = comment.get("createdAt")

            if (
                not comment_login
                # ignore bots
                or comment_type == "Bot"
                # ignore comments by the discussion author
                or comment_login == discussion_author_login
                # ignore users in the ignore list
                or comment_login in ignore_users
                # ignore comments without a timestamp
                or not comment_created_at
            ):
                continue

            if comment_login in mentor_count:
                if mentor_count[comment_login] < heavily_involved:
                    mentor_count[comment_login] += 1
            else:
                mentor_count[comment_login] = 1

    return mentor_count


def ignore_comment(
    issue_user,
    comment_user,
    ignore_users: list[str],
    comment_created_at: datetime,
    ready_for_review_at: datetime | None,
) -> bool:
    """Check if a comment should be ignored."""
    # PyGithub returns None for ghost (deleted) users
    if comment_user is None:
        return True
    return bool(
        # ignore comments by IGNORE_USERS
        comment_user.login in ignore_users
        # ignore comments by bots
        or comment_user.type == "Bot"
        # ignore comments by the issue creator
        or comment_user.login == issue_user.login
        # ignore pending reviews
        or not comment_created_at
        # ignore comments created before the issue was ready for review
        or (ready_for_review_at and comment_created_at < ready_for_review_at)
    )


def get_mentor_count(issues_with_metrics: list[IssueWithMetrics], cutoff: int) -> int:
    """Calculate the number of active mentors on the project.

    Args:
        issues_with_metrics (List[IssueWithMetrics]): A list of issues w/
        metrics
        cutoff (int: the minimum number of comments a user has to leave
        to count as active mentor.)

    Returns:
        int: Number of active mentors

    """

    mentor_count: Counter[str] = Counter({})
    for issue_with_metrics in issues_with_metrics:
        current_counter = Counter(issue_with_metrics.mentor_activity)
        mentor_count = mentor_count + current_counter

    active_mentor_count = 0
    for count in mentor_count.values():
        if count >= cutoff:
            active_mentor_count += 1

    return active_mentor_count
