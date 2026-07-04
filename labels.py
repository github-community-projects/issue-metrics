"""Functions for calculating time spent in labels."""

from datetime import datetime, timedelta
from typing import List

import numpy
import pytz
from classes import IssueWithMetrics
from github.Issue import Issue


def get_label_events(issue: Issue, labels: List[str]) -> list:
    """
    Get the label events for a given issue if the label is of interest.

    Args:
        issue (Issue): A GitHub issue.
        labels (List[str]): A list of labels of interest.

    Returns:
        list: A list of label events for the given issue.
    """
    label_events = []
    for event in issue.get_events():
        if event.event in ("labeled", "unlabeled") and event.label.name in labels:
            label_events.append(event)

    return label_events


def get_label_metrics(issue: Issue, labels: List[str]) -> dict:
    """
    Calculate the time spent with the given labels on a given issue.

    Args:
        issue (Issue): A GitHub issue.
        labels (List[str]): A list of labels to measure time spent in.

    Returns:
        dict: A dictionary containing the time spent in each label or None.
    """
    label_metrics: dict = {}
    label_events = get_label_events(issue, labels)
    label_last_event_type: dict = {}

    for label in labels:
        label_metrics[label] = None

    # If the event is one of the labels we're looking for, add the time to the dictionary
    unlabeled = {}
    labeled = {}
    if not label_events:
        return label_metrics

    # Calculate the time to add or subtract to the time spent in label based on the label events
    for event in label_events:
        # Skip labeling events that have occurred past issue close time
        if issue.closed_at is not None and (event.created_at >= issue.closed_at):
            continue

        if event.event == "labeled":
            labeled[event.label.name] = True
            if event.label.name in labels:
                if label_metrics[event.label.name] is None:
                    label_metrics[event.label.name] = timedelta(0)
                label_metrics[event.label.name] -= event.created_at - issue.created_at
                label_last_event_type[event.label.name] = "labeled"
        elif event.event == "unlabeled":
            unlabeled[event.label.name] = True
            if event.label.name in labels:
                if label_metrics[event.label.name] is None:
                    label_metrics[event.label.name] = timedelta(0)
                label_metrics[event.label.name] += event.created_at - issue.created_at
                label_last_event_type[event.label.name] = "unlabeled"

    for label in labels:
        if label in labeled:
            # if the issue is closed, add the time from the issue creation to the closed_at time
            if issue.state == "closed":
                # Only add the final (closed_at - created_at) span if the label was still applied at closure.
                if label_last_event_type.get(label) != "labeled":
                    continue
                label_metrics[label] += issue.closed_at - issue.created_at
            else:
                # skip label if last labeling event is 'unlabeled' and issue is still open
                if label_last_event_type[label] == "unlabeled":
                    continue

                # if the issue is open, add the time from the issue creation to now
                label_metrics[label] += datetime.now(pytz.utc) - issue.created_at

    return label_metrics


def get_stats_time_in_labels(
    issues_with_metrics: List[IssueWithMetrics],
    labels: dict[str, timedelta],
) -> dict[str, dict[str, timedelta | None]]:
    """Calculate stats describing time spent in each label."""
    time_in_labels = {}
    for issue in issues_with_metrics:
        if issue.label_metrics:
            for label in issue.label_metrics:
                if issue.label_metrics[label] is None:
                    continue
                if label not in time_in_labels:
                    time_in_labels[label] = [issue.label_metrics[label].total_seconds()]
                else:
                    time_in_labels[label].append(
                        issue.label_metrics[label].total_seconds()
                    )

    average_time_in_labels: dict[str, timedelta | None] = {}
    med_time_in_labels: dict[str, timedelta | None] = {}
    ninety_percentile_in_labels: dict[str, timedelta | None] = {}
    for label, time_list in time_in_labels.items():
        average_time_in_labels[label] = timedelta(
            seconds=numpy.round(numpy.average(time_list))
        )
        med_time_in_labels[label] = timedelta(
            seconds=numpy.round(numpy.median(time_list))
        )
        ninety_percentile_in_labels[label] = timedelta(
            seconds=numpy.round(numpy.percentile(time_list, 90, axis=0))
        )

    for label in labels:
        if label not in average_time_in_labels:
            average_time_in_labels[label] = None
            med_time_in_labels[label] = None
            ninety_percentile_in_labels[label] = None

    stats = {
        "avg": average_time_in_labels,
        "med": med_time_in_labels,
        "90p": ninety_percentile_in_labels,
    }
    return stats
