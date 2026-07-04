"""
This module contains a function that measures the time a pull request has been in draft state.
"""

from datetime import datetime, timedelta
from typing import List, Union

import numpy
import pytz
from classes import IssueWithMetrics
from github.Issue import Issue
from github.PullRequest import PullRequest


def measure_time_in_draft(
    issue: Issue,
    pull_request: Union[PullRequest, None] = None,
) -> Union[timedelta, None]:
    """If a pull request has had time in the draft state, return the cumulative amount of time it was in draft.

    args:
        issue (Issue): A GitHub issue which has been pre-qualified as a pull request.
        pull_request (PullRequest, optional): The pull request object.

    returns:
        Union[timedelta, None]: Total time the pull request has spent in draft state.
    """
    events = list(issue.get_events())
    draft_start = None
    total_draft_time = timedelta(0)

    # Check if PR was initially created as draft
    pr_created_at = None

    try:
        if pull_request is None:
            pull_request = issue.as_pull_request()

        pr_created_at = issue.created_at

        # Look for ready_for_review events to determine if PR was initially draft
        ready_for_review_events = []
        convert_to_draft_events = []
        for event in events:
            if event.event == "ready_for_review":
                ready_for_review_events.append(event)
            elif event.event == "convert_to_draft":
                convert_to_draft_events.append(event)

        # If there are ready_for_review events, check if PR was initially draft
        if ready_for_review_events:
            first_ready_event = min(ready_for_review_events, key=lambda x: x.created_at)
            prior_draft_events = [
                e
                for e in convert_to_draft_events
                if e.created_at < first_ready_event.created_at
            ]

            if not prior_draft_events:
                # PR was initially created as draft, calculate time from creation to first ready_for_review
                total_draft_time += first_ready_event.created_at - pr_created_at

        # If there are no ready_for_review events but the PR is currently draft, it might be initially draft and still open
        elif not ready_for_review_events and not convert_to_draft_events:
            # Check if PR is currently draft and open
            if (
                hasattr(pull_request, "draft")
                and pull_request.draft
                and issue.state == "open"
            ):
                # PR was initially created as draft and is still draft
                draft_start = pr_created_at

    except (AttributeError, ValueError, TypeError):
        # If we can't get PR info, fall back to original logic
        pass

    for event in events:
        if event.event == "convert_to_draft":
            draft_start = event.created_at
        elif event.event == "ready_for_review" and draft_start:
            # Calculate draft time for this interval
            total_draft_time += event.created_at - draft_start
            draft_start = None

    # If the PR is currently in draft state, calculate the time in draft up to now
    if draft_start and issue.state == "open":
        total_draft_time += datetime.now(pytz.utc) - draft_start

    # Round to the nearest second
    return (
        timedelta(seconds=round(total_draft_time.total_seconds()))
        if total_draft_time > timedelta(0)
        else None
    )


def get_stats_time_in_draft(
    issues_with_metrics: List[IssueWithMetrics],
) -> Union[dict[str, timedelta], None]:
    """
    Calculate stats describing the time in draft for a list of issues.
    """
    # Filter out issues with no time in draft
    issues_with_time_to_draft = [
        issue for issue in issues_with_metrics if issue.time_in_draft is not None
    ]

    # Calculate the total time in draft for all issues
    draft_times = []
    if issues_with_time_to_draft:
        for issue in issues_with_time_to_draft:
            if issue.time_in_draft:
                draft_times.append(issue.time_in_draft.total_seconds())

    # Calculate stats describing time in draft
    num_issues_with_time_in_draft = len(issues_with_time_to_draft)
    if num_issues_with_time_in_draft > 0:
        average_time_in_draft = numpy.round(numpy.average(draft_times))
        med_time_in_draft = numpy.round(numpy.median(draft_times))
        ninety_percentile_time_in_draft = numpy.round(
            numpy.percentile(draft_times, 90, axis=0)
        )
    else:
        return None

    stats = {
        "avg": timedelta(seconds=average_time_in_draft),
        "med": timedelta(seconds=med_time_in_draft),
        "90p": timedelta(seconds=ninety_percentile_time_in_draft),
    }

    # Print the average time in draft converting seconds to a readable time format
    print(f"Average time in draft: {timedelta(seconds=average_time_in_draft)}")
    return stats
