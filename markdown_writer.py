"""A module for writing GitHub issue metrics to a markdown file.

This module provides a function for writing a list of GitHub issues with metrics
to a markdown file. The metrics include the average time to first response, the
average time to close, and the average time to answer the discussions. The module
also provides functions for sorting the issues by time to first response.

Functions:
    write_to_markdown(
        issues_with_metrics: Union[List[IssueWithMetrics], None],
        average_time_to_first_response: Union[dict[str, timedelta], None],
        average_time_to_close: Union[dict[str, timedelta], None],
        average_time_to_answer: Union[dict[str, timedelta], None],
        average_time_in_labels: Union[dict, None],
        num_issues_opened: Union[int, None],
        num_issues_closed: Union[int, None],
        num_mentor_count: Union[int, None],
        labels: List[str],
        search_query: str,
        hide_label_metrics: bool,
        hide_items_closed_count: bool,
        non_mentioning_links: bool,
        report_title: str,
        output_file: str,
    ) -> None:
        Write the issues with metrics to a markdown file.
    get_non_hidden_columns(
        average_time_to_first_response: timedelta,
        average_time_to_close: timedelta,
        average_time_to_answer: timedelta
    ) -> List[str]:
        Get the columns that are not hidden.
    sort_issues(
        issues: List[IssueWithMetrics],
        sort_by: str | None,
        sort_order: str
    ) -> List[IssueWithMetrics]:
        Sort issues by the specified field.
    group_issues(
        issues: List[IssueWithMetrics],
        group_by: str | None
    ) -> dict[str, List[IssueWithMetrics]]:
        Group issues by the specified field.
"""

from datetime import timedelta
from typing import Dict, List, Union

from classes import IssueWithMetrics
from config import get_env_vars


def get_non_hidden_columns(labels) -> List[str]:
    """
    Get a list of the columns that are not hidden.

    Args:
        labels (List[str]): A list of the labels that are used in the issues.

    Returns:
        List[str]: A list of the columns that are not hidden.

    """
    columns = ["Title", "URL"]

    env_vars = get_env_vars()

    # Find the number of columns and which are to be hidden
    hide_assignee = env_vars.hide_assignee
    if not hide_assignee:
        columns.append("Assignee")

    hide_author = env_vars.hide_author
    if not hide_author:
        columns.append("Author")

    hide_time_to_first_response = env_vars.hide_time_to_first_response
    if not hide_time_to_first_response:
        columns.append("Time to first response")

    hide_time_to_first_review = env_vars.hide_time_to_first_review
    if not hide_time_to_first_review:
        columns.append("Time to first review")

    hide_time_to_close = env_vars.hide_time_to_close
    if not hide_time_to_close:
        columns.append("Time to close")

    hide_time_to_answer = env_vars.hide_time_to_answer
    if not hide_time_to_answer:
        columns.append("Time to answer")

    enable_time_in_draft = env_vars.draft_pr_tracking
    if enable_time_in_draft:
        columns.append("Time in draft")

    hide_label_metrics = env_vars.hide_label_metrics
    if not hide_label_metrics and labels:
        for label in labels:
            columns.append(f"Time spent in {label}")
    hide_created_at = env_vars.hide_created_at
    if not hide_created_at:
        columns.append("Created At")

    hide_status = env_vars.hide_status
    if not hide_status:
        columns.append("Status")

    hide_pr_statistics = env_vars.hide_pr_statistics
    if not hide_pr_statistics:
        columns.append("PR Comments")

    return columns


def sort_issues(
    issues: List[IssueWithMetrics], sort_by: str | None, sort_order: str
) -> List[IssueWithMetrics]:
    """Sort issues by the specified field.

    Args:
        issues (List[IssueWithMetrics]): List of issues to sort.
        sort_by (str | None): Field to sort by (e.g., 'time_to_close', 'time_to_first_response').
        sort_order (str): Sort order, either 'asc' for ascending or 'desc' for descending.

    Returns:
        List[IssueWithMetrics]: Sorted list of issues.
    """
    if not sort_by or not issues:
        return issues

    # Map of valid sort fields
    valid_fields = {
        "time_to_close",
        "time_to_first_response",
        "time_to_first_review",
        "time_to_answer",
        "time_in_draft",
        "created_at",
    }

    if sort_by not in valid_fields:
        return issues

    reverse = sort_order == "desc"

    # Sort with None values at the end, regardless of sort order
    non_none_issues: List[IssueWithMetrics] = []
    none_issues: List[IssueWithMetrics] = []

    for issue in issues:
        value = getattr(issue, sort_by, None)
        if value is None:
            none_issues.append(issue)
        else:
            non_none_issues.append(issue)

    sorted_non_none = sorted(
        non_none_issues,
        key=lambda issue: getattr(issue, sort_by),
        reverse=reverse,
    )

    return sorted_non_none + none_issues


def group_issues(
    issues: List[IssueWithMetrics], group_by: str | None
) -> Dict[str, List[IssueWithMetrics]]:
    """Group issues by the specified field.

    Args:
        issues (List[IssueWithMetrics]): List of issues to group.
        group_by (str | None): Field to group by (e.g., 'author', 'assignee').

    Returns:
        Dict[str, List[IssueWithMetrics]]: Dictionary of grouped issues.
    """
    if not group_by or not issues:
        return {"": issues}

    # Map of valid group fields
    valid_fields = {"author", "assignee"}

    if group_by not in valid_fields:
        return {"": issues}

    grouped: Dict[str, List[IssueWithMetrics]] = {}
    for issue in issues:
        if group_by == "author":
            key = issue.author or "Unknown"
        elif group_by == "assignee":
            # Use the first assignee or "Unassigned"
            key = issue.assignees[0] if issue.assignees else "Unassigned"
        else:
            key = "Unknown"

        if key not in grouped:
            grouped[key] = []
        grouped[key].append(issue)

    return grouped


def write_to_markdown(
    issues_with_metrics: Union[List[IssueWithMetrics], None],
    average_time_to_first_response: Union[dict[str, timedelta], None],
    average_time_to_first_review: Union[dict[str, timedelta], None],
    average_time_to_close: Union[dict[str, timedelta], None],
    average_time_to_answer: Union[dict[str, timedelta], None],
    average_time_in_draft: Union[dict[str, timedelta], None],
    average_time_in_labels: Union[dict, None],
    stats_pr_comments: Union[dict[str, float], None],
    num_issues_opened: Union[int, None],
    num_issues_closed: Union[int, None],
    num_mentor_count: Union[int, None],
    labels=None,
    search_query=None,
    hide_label_metrics=False,
    hide_items_closed_count=False,
    enable_mentor_count=False,
    non_mentioning_links=False,
    report_title="",
    output_file="",
    ghe="",
) -> None:
    """Write the issues with metrics to a markdown file.

    Args:
        issues_with_metrics (IssueWithMetrics): A list of GitHub issues with metrics
        average_time_to_first_response (datetime.timedelta): The average time to first
            response for the issues.
        average_time_to_close (datetime.timedelta): The average time to close for the issues.
        average_time_to_answer (datetime.timedelta): The average time to answer the discussions.
        average_time_in_draft (datetime.timedelta): The average time spent in draft for the issues.
        average_time_in_labels (dict): A dictionary containing the average time spent in each label.
        file (file object, optional): The file object to write to. If not provided,
            a file named "issue_metrics.md" will be created.
        num_issues_opened (int): The Number of items that remain opened.
        num_issues_closed (int): The number of issues that were closed.
        num_mentor_count (int): The number of very active commentors.
        labels (List[str]): A list of the labels that are used in the issues.
        search_query (str): The search query used to find the issues.
        hide_label_metrics (bool): Represents whether the user has chosen to hide label
            metrics in the output
        hide_items_closed_count (bool): Represents whether the user has chosen to hide
            the number of items closed
        non_mentioning_links (bool): Represents whether links do not cause a notification
            in the destination repository
        report_title (str): The title of the report
        output_file (str): The name of the file to write the report to
        ghe (str): the GitHub Enterprise endpoint

    Returns:
        None.

    """
    columns = get_non_hidden_columns(labels)
    env_vars = get_env_vars()
    output_file_name = output_file if output_file else "issue_metrics.md"
    with open(output_file_name, "w", encoding="utf-8") as file:
        file.write(f"# {report_title}\n\n")

        # If all the metrics are None, then there are no issues
        if not issues_with_metrics or len(issues_with_metrics) == 0:
            file.write("no issues found for the given search criteria\n\n")
            file.write("\n_This report was generated with the \
[Issue Metrics Action](https://github.com/github-community-projects/issue-metrics)_\n")
            if search_query:
                file.write(f"Search query used to find these items: `{search_query}`\n")
            return

        # Write first table with overall metrics
        write_overall_metrics_tables(
            issues_with_metrics,
            average_time_to_first_response,
            average_time_to_first_review,
            average_time_to_close,
            average_time_to_answer,
            average_time_in_draft,
            average_time_in_labels,
            stats_pr_comments,
            num_issues_opened,
            num_issues_closed,
            num_mentor_count,
            labels,
            columns,
            file,
            hide_label_metrics,
            hide_items_closed_count,
            enable_mentor_count,
            env_vars.hide_pr_statistics,
        )

        # Write second table with individual issue/pr/discussion metrics
        # Skip this table if hide_items_list is True
        if not env_vars.hide_items_list:  # pylint: disable=too-many-nested-blocks
            # Apply sorting and grouping
            sorted_issues = sort_issues(
                issues_with_metrics, env_vars.sort_by, env_vars.sort_order
            )
            grouped_issues_dict = group_issues(sorted_issues, env_vars.group_by)

            # If grouping, write separate sections for each group
            for group_name, group_issues_list in grouped_issues_dict.items():
                # Write group header if grouping is enabled
                if env_vars.group_by and group_name:
                    file.write(f"\n### {group_name}\n\n")

                # First write the header
                file.write("|")
                for column in columns:
                    file.write(f" {column} |")
                file.write("\n")

                # Then write the column dividers
                file.write("|")
                for _ in columns:
                    file.write(" --- |")
                file.write("\n")

                # Then write the issues/pr/discussions row by row
                for issue in group_issues_list:
                    # Replace the vertical bar with the HTML entity
                    issue.title = issue.title.replace("|", "&#124;")
                    # Replace any whitespace
                    issue.title = issue.title.strip()

                    endpoint = ghe.removeprefix("https://") if ghe else "github.com"
                    if non_mentioning_links:
                        file.write(
                            f"| {issue.title} | "
                            f"{issue.html_url}".replace(
                                f"https://{endpoint}", f"https://www.{endpoint}"
                            )
                            + " |"
                        )
                    else:
                        file.write(f"| {issue.title} | {issue.html_url} |")
                    if "Assignee" in columns:
                        if issue.assignees:
                            assignee_links = [
                                f"[{assignee}](https://{endpoint}/{assignee})"
                                for assignee in issue.assignees
                            ]
                            file.write(f" {', '.join(assignee_links)} |")
                        else:
                            file.write(" None |")
                    if "Author" in columns:
                        file.write(
                            f" [{issue.author}](https://{endpoint}/{issue.author}) |"
                        )
                    if "Time to first response" in columns:
                        file.write(f" {issue.time_to_first_response} |")
                    if "Time to first review" in columns:
                        file.write(f" {issue.time_to_first_review} |")
                    if "Time to close" in columns:
                        file.write(f" {issue.time_to_close} |")
                    if "Time to answer" in columns:
                        file.write(f" {issue.time_to_answer} |")
                    if "Time in draft" in columns:
                        file.write(f" {issue.time_in_draft} |")
                    if labels and issue.label_metrics:
                        for label in labels:
                            if f"Time spent in {label}" in columns:
                                file.write(f" {issue.label_metrics[label]} |")
                    if "Created At" in columns:
                        file.write(f" {issue.created_at} |")
                    if "Status" in columns:
                        file.write(f" {issue.status} |")
                    if "PR Comments" in columns:
                        file.write(f" {issue.pr_comment_count or 'N/A'} |")
                    file.write("\n")
                file.write("\n")
        file.write("_This report was generated with the \
[Issue Metrics Action](https://github.com/github-community-projects/issue-metrics)_\n")
        if search_query:
            file.write(f"Search query used to find these items: `{search_query}`\n")

    print(f"Wrote issue metrics to {output_file_name}")


def write_overall_metrics_tables(
    issues_with_metrics,
    stats_time_to_first_response,
    stats_time_to_first_review,
    stats_time_to_close,
    stats_time_to_answer,
    average_time_in_draft,
    stats_time_in_labels,
    stats_pr_comments,
    num_issues_opened,
    num_issues_closed,
    num_mentor_count,
    labels,
    columns,
    file,
    hide_label_metrics,
    hide_items_closed_count=False,
    enable_mentor_count=False,
    hide_pr_statistics=True,
):
    """Write the overall metrics tables to the markdown file."""

    if (
        any(
            column in columns
            for column in [
                "Time to first response",
                "Time to first review",
                "Time to close",
                "Time to answer",
                "Time in draft",
            ]
        )
        or (hide_label_metrics is False and len(labels) > 0)
        or (not hide_pr_statistics and stats_pr_comments is not None)
    ):
        file.write("| Metric | Average | Median | 90th percentile |\n")
        file.write("| --- | --- | --- | ---: |\n")
        if "Time to first response" in columns:
            if stats_time_to_first_response is not None:
                file.write(
                    f"| Time to first response "
                    f"| {stats_time_to_first_response['avg']} "
                    f"| {stats_time_to_first_response['med']} "
                    f"| {stats_time_to_first_response['90p']} |\n"
                )
            else:
                file.write("| Time to first response | None | None | None |\n")
        if "Time to first review" in columns:
            if stats_time_to_first_review is not None:
                file.write(
                    f"| Time to first review "
                    f"| {stats_time_to_first_review['avg']} "
                    f"| {stats_time_to_first_review['med']} "
                    f"| {stats_time_to_first_review['90p']} |\n"
                )
            else:
                file.write("| Time to first review | None | None | None |\n")
        if "Time to close" in columns:
            if stats_time_to_close is not None:
                file.write(
                    f"| Time to close "
                    f"| {stats_time_to_close['avg']} "
                    f"| {stats_time_to_close['med']} "
                    f"| {stats_time_to_close['90p']} |\n"
                )
            else:
                file.write("| Time to close | None | None | None |\n")
        if "Time to answer" in columns:
            if stats_time_to_answer is not None:
                file.write(
                    f"| Time to answer "
                    f"| {stats_time_to_answer['avg']} "
                    f"| {stats_time_to_answer['med']} "
                    f"| {stats_time_to_answer['90p']} |\n"
                )
            else:
                file.write("| Time to answer | None | None | None |\n")
        if "Time in draft" in columns:
            if average_time_in_draft is not None:
                file.write(
                    f"| Time in draft "
                    f"| {average_time_in_draft['avg']} "
                    f"| {average_time_in_draft['med']} "
                    f"| {average_time_in_draft['90p']} |\n"
                )
            else:
                file.write("| Time in draft | None | None | None |\n")
        if labels and stats_time_in_labels:
            for label in labels:
                if (
                    f"Time spent in {label}" in columns
                    and label in stats_time_in_labels["avg"]
                ):
                    file.write(
                        f"| Time spent in {label} "
                        f"| {stats_time_in_labels['avg'][label]} "
                        f"| {stats_time_in_labels['med'][label]} "
                        f"| {stats_time_in_labels['90p'][label]} |\n"
                    )

        # Add PR comment statistics if not hidden
        if not hide_pr_statistics and stats_pr_comments is not None:
            file.write(
                f"| Number of comments per PR "
                f"| {stats_pr_comments['avg']} "
                f"| {stats_pr_comments['med']} "
                f"| {stats_pr_comments['90p']} |\n"
            )

        if "Status" in columns:  # Add logic for the 'status' column
            file.write("| Status | | | |\n")

        file.write("\n")
    # Write count stats to a separate table
    file.write("| Metric | Count |\n")
    file.write("| --- | ---: |\n")
    file.write(f"| Number of items that remain open | {num_issues_opened} |\n")
    if not hide_items_closed_count:
        file.write(f"| Number of items closed | {num_issues_closed} |\n")
    if enable_mentor_count:
        file.write(f"| Number of most active mentors | {num_mentor_count} |\n")
    file.write(f"| Total number of items created | {len(issues_with_metrics)} |\n\n")
