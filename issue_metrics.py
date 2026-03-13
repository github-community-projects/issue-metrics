"""A script for measuring time to first response and time to close for GitHub issues.

This script uses the GitHub API to search for issues/prs/discussions in a repository
and measure the time to first response and time to close for each issue. It then calculates
the average time to first response and time to close and writes the issues with
their metrics to a markdown file.

Functions:
    get_per_issue_metrics(issues: Union[List[dict], List[github3.issues.Issue]],
        discussions: bool = False), labels: Union[List[str], None] = None,
        ignore_users: List[str] = [] -> tuple[List, int, int]:
        Calculate the metrics for each issue in a list of GitHub issues.
    get_owner(search_query: str) -> Union[str, None]]:
        Get the owner from the search query.
    main(): Run the issue-metrics script.
"""

import shutil
from pathlib import Path
from typing import List, Union

import github3
import github3.structs
from auth import auth_to_github, get_github_app_installation_token
from classes import IssueWithMetrics
from config import EnvVars, get_env_vars
from discussions import get_discussions
from json_writer import write_to_json
from labels import get_label_metrics, get_stats_time_in_labels
from markdown_helpers import markdown_too_large_for_issue_body, split_markdown_file
from markdown_writer import write_to_markdown
from most_active_mentors import count_comments_per_user, get_mentor_count
from pr_comments import count_pr_comments, get_stats_pr_comments
from search import get_owners_and_repositories, search_issues
from time_in_draft import get_stats_time_in_draft, measure_time_in_draft
from time_to_answer import get_stats_time_to_answer, measure_time_to_answer
from time_to_close import get_stats_time_to_close, measure_time_to_close
from time_to_first_response import (
    get_stats_time_to_first_response,
    measure_time_to_first_response,
)
from time_to_first_review import (
    get_stats_time_to_first_review,
    measure_time_to_first_review,
)
from time_to_merge import measure_time_to_merge
from time_to_ready_for_review import get_time_to_ready_for_review


def get_per_issue_metrics(
    issues: Union[List[dict], List[github3.search.IssueSearchResult]],  # type: ignore
    env_vars: EnvVars,
    discussions: bool = False,
    labels: Union[List[str], None] = None,
    ignore_users: Union[List[str], None] = None,
    max_comments_to_eval: int = 20,
    heavily_involved: int = 3,
) -> tuple[List, int, int]:
    """
    Calculate the metrics for each issue/pr/discussion in a list provided.

    Args:
        issues (Union[List[dict], List[github3.search.IssueSearchResult]]): A list of
            GitHub issues or discussions.
        discussions (bool, optional): Whether the issues are discussions or not.
            Defaults to False.
        labels (List[str]): A list of labels to measure time spent in. Defaults to empty list.
        ignore_users (List[str]): A list of users to ignore when calculating metrics.
        env_vars (EnvVars): The environment variables for the script.

    Returns:
        tuple[List[IssueWithMetrics], int, int]: A tuple containing a
            list of IssueWithMetrics objects, the number of open issues,
            and the number of closed issues or discussions.

    """
    issues_with_metrics = []
    num_issues_open = 0
    num_issues_closed = 0

    for issue in issues:
        if discussions:
            issue_with_metrics = IssueWithMetrics(
                issue["title"],
                issue["url"],
                None,
                None,
                None,
                None,
                None,
                None,
            )
            # Discussions typically don't have assignees in the same way as issues/PRs
            issue_with_metrics.assignee = None
            issue_with_metrics.assignees = []
            if env_vars.hide_time_to_first_response is False:
                issue_with_metrics.time_to_first_response = (
                    measure_time_to_first_response(None, issue, ignore_users)
                )
            if env_vars.enable_mentor_count:
                issue_with_metrics.mentor_activity = count_comments_per_user(
                    None,
                    issue,
                    None,
                    None,
                    ignore_users,
                    max_comments_to_eval,
                    heavily_involved,
                )
            if env_vars.hide_time_to_answer is False:
                issue_with_metrics.time_to_answer = measure_time_to_answer(issue)
            if issue["closedAt"]:
                num_issues_closed += 1
                if not env_vars.hide_time_to_close:
                    issue_with_metrics.time_to_close = measure_time_to_close(
                        None, issue
                    )
            else:
                num_issues_open += 1
        else:
            if ignore_users and issue.user["login"] in ignore_users:  # type: ignore
                continue

            issue_with_metrics = IssueWithMetrics(
                title=issue.title,  # type: ignore
                html_url=issue.html_url,  # type: ignore
                author=issue.user["login"],  # type: ignore
            )

            # Extract assignee information from the issue
            issue_dict = issue.issue.as_dict()  # type: ignore
            assignee = None
            assignees = []

            if issue_dict.get("assignee"):
                assignee = issue_dict["assignee"]["login"]

            if issue_dict.get("assignees"):
                assignees = [a["login"] for a in issue_dict["assignees"]]

            issue_with_metrics.assignee = assignee
            issue_with_metrics.assignees = assignees

            # Check if issue is actually a pull request
            pull_request, ready_for_review_at = None, None
            if issue.issue.pull_request_urls:  # type: ignore
                try:
                    pull_request = issue.issue.pull_request()  # type: ignore
                    ready_for_review_at = get_time_to_ready_for_review(
                        issue, pull_request
                    )
                    if env_vars.draft_pr_tracking:
                        issue_with_metrics.time_in_draft = measure_time_in_draft(
                            issue=issue, pull_request=pull_request
                        )
                except TypeError as e:
                    print(
                        f"An error occurred processing review comments. Perhaps the review contains a ghost user. {e}"
                    )

            # Count PR comments if this is a pull request and statistics are not hidden
            if pull_request and not env_vars.hide_pr_statistics:
                issue_with_metrics.pr_comment_count = count_pr_comments(
                    issue, pull_request, ignore_users
                )
            if not env_vars.hide_time_to_first_review and pull_request:
                issue_with_metrics.time_to_first_review = measure_time_to_first_review(
                    issue,
                    pull_request,
                    ready_for_review_at,
                    ignore_users,
                )
            if env_vars.hide_time_to_first_response is False:
                issue_with_metrics.time_to_first_response = (
                    measure_time_to_first_response(
                        issue, None, pull_request, ready_for_review_at, ignore_users
                    )
                )
            if env_vars.enable_mentor_count:
                issue_with_metrics.mentor_activity = count_comments_per_user(
                    issue,
                    None,
                    pull_request,
                    ready_for_review_at,
                    ignore_users,
                    max_comments_to_eval,
                    heavily_involved,
                )
            if labels and env_vars.hide_label_metrics is False:
                issue_with_metrics.label_metrics = get_label_metrics(issue, labels)
            if issue.state == "closed":  # type: ignore
                num_issues_closed += 1
                if not env_vars.hide_time_to_close:
                    if pull_request:
                        issue_with_metrics.time_to_close = measure_time_to_merge(
                            pull_request, ready_for_review_at
                        )
                    else:
                        issue_with_metrics.time_to_close = measure_time_to_close(
                            issue, None
                        )
                if not env_vars.hide_status:
                    issue_with_metrics.status = f"{issue.issue.state} as {issue.issue.state_reason}"  # type: ignore
            elif issue.state == "open":  # type: ignore
                num_issues_open += 1
                if not env_vars.hide_status:
                    issue_with_metrics.status = f"{issue.issue.state}"  # type: ignore
        if not env_vars.hide_created_at:
            if isinstance(issue, github3.search.IssueSearchResult):  # type: ignore
                issue_with_metrics.created_at = issue.issue.created_at  # type: ignore
            elif isinstance(issue, dict):  # type: ignore
                issue_with_metrics.created_at = issue["createdAt"]  # type: ignore
        issues_with_metrics.append(issue_with_metrics)

    return issues_with_metrics, num_issues_open, num_issues_closed


def evaluate_markdown_file_size(output_file: str) -> None:
    """
    Evaluate the size of the markdown file and split it, if it is too large.
    """
    output_file_name = output_file if output_file else "issue_metrics.md"
    file_name_without_extension = Path(output_file_name).stem
    max_char_count = 65535
    if markdown_too_large_for_issue_body(output_file_name, max_char_count):
        split_markdown_file(output_file_name, max_char_count)
        shutil.move(output_file_name, f"{file_name_without_extension}_full.md")
        shutil.move(f"{file_name_without_extension}_0.md", output_file_name)
        print(
            f"Issue metrics markdown file is too large for GitHub issue body and has been \
split into multiple files. ie. {output_file_name}, {file_name_without_extension}_1.md, etc. \
The full file is saved as {file_name_without_extension}_full.md\n\
See https://github.com/github-community-projects/issue-metrics/blob/main/docs/dealing-with-large-issue-metrics.md"
        )


def main():  # pragma: no cover
    """Run the issue-metrics script.

    This function authenticates to GitHub, searches for issues/prs/discussions
    using the SEARCH_QUERY environment variable, measures the time to first response
    and close for each issue, calculates the average time to first response,
    and writes the results to a markdown file.

    Raises:
        ValueError: If the SEARCH_QUERY environment variable is not set.
        ValueError: If the search query does not include a repository owner and name.
    """

    print("Starting issue-metrics search...")

    # Get the environment variables for use in the script
    env_vars = get_env_vars()
    search_query = env_vars.search_query
    token = env_vars.gh_token
    ignore_users = env_vars.ignore_users
    hide_items_closed_count = env_vars.hide_items_closed_count
    hide_label_metrics = env_vars.hide_label_metrics
    non_mentioning_links = env_vars.non_mentioning_links
    report_title = env_vars.report_title
    output_file = env_vars.output_file
    rate_limit_bypass = env_vars.rate_limit_bypass

    ghe = env_vars.ghe
    gh_app_id = env_vars.gh_app_id
    gh_app_installation_id = env_vars.gh_app_installation_id
    gh_app_private_key_bytes = env_vars.gh_app_private_key_bytes
    gh_app_enterprise_only = env_vars.gh_app_enterprise_only

    # Auth to GitHub.com
    github_connection = auth_to_github(
        token,
        gh_app_id,
        gh_app_installation_id,
        gh_app_private_key_bytes,
        ghe,
        gh_app_enterprise_only,
    )

    if not token and gh_app_id and gh_app_installation_id and gh_app_private_key_bytes:
        token = get_github_app_installation_token(
            ghe, gh_app_id, gh_app_private_key_bytes, gh_app_installation_id
        )

    enable_mentor_count = env_vars.enable_mentor_count
    min_mentor_count = int(env_vars.min_mentor_comments)
    max_comments_eval = int(env_vars.max_comments_eval)
    heavily_involved_cutoff = int(env_vars.heavily_involved_cutoff)

    # Get the owners and repositories from the search query
    owners_and_repositories = get_owners_and_repositories(search_query)

    # Every search query must include a repository owner for each repository, organization, or user
    for item in owners_and_repositories:
        if item["owner"] is None:
            raise ValueError(
                "The search query must include a repository owner and name \
                (ie. repo:owner/repo), an organization (ie. org:organization), \
                a user (ie. user:login) or an owner (ie. owner:user-or-organization)"
            )

    # Determine if there are label to measure
    labels = env_vars.labels_to_measure

    # Search for issues
    # If type:discussions is in the search_query, search for discussions using get_discussions()
    if "type:discussions" in search_query:
        if labels:
            raise ValueError(
                "The search query for discussions cannot include labels to measure"
            )
        issues = get_discussions(token, search_query, ghe)
        if len(issues) <= 0:
            print("No discussions found")
            write_to_markdown(
                issues_with_metrics=None,
                average_time_to_first_response=None,
                average_time_to_first_review=None,
                average_time_to_close=None,
                average_time_to_answer=None,
                average_time_in_draft=None,
                average_time_in_labels=None,
                stats_pr_comments=None,
                num_issues_opened=None,
                num_issues_closed=None,
                num_mentor_count=None,
                labels=None,
                search_query=search_query,
                hide_label_metrics=False,
                hide_items_closed_count=False,
                enable_mentor_count=enable_mentor_count,
                non_mentioning_links=False,
                report_title=report_title,
                output_file=output_file,
                ghe=ghe,
            )
            return
    else:
        issues = search_issues(
            search_query, github_connection, owners_and_repositories, rate_limit_bypass
        )
        if len(issues) <= 0:
            print("No issues found")
            write_to_markdown(
                issues_with_metrics=None,
                average_time_to_first_response=None,
                average_time_to_first_review=None,
                average_time_to_close=None,
                average_time_to_answer=None,
                average_time_in_draft=None,
                average_time_in_labels=None,
                stats_pr_comments=None,
                num_issues_opened=None,
                num_issues_closed=None,
                num_mentor_count=None,
                labels=None,
                search_query=search_query,
                hide_label_metrics=False,
                hide_items_closed_count=False,
                enable_mentor_count=enable_mentor_count,
                non_mentioning_links=False,
                report_title=report_title,
                output_file=output_file,
                ghe=ghe,
            )
            return

    # Get all the metrics
    issues_with_metrics, num_issues_open, num_issues_closed = get_per_issue_metrics(
        issues,
        discussions="type:discussions" in search_query,
        labels=labels,
        ignore_users=ignore_users,
        max_comments_to_eval=max_comments_eval,
        heavily_involved=heavily_involved_cutoff,
        env_vars=env_vars,
    )

    stats_time_to_first_response = get_stats_time_to_first_response(issues_with_metrics)
    stats_time_to_first_review = get_stats_time_to_first_review(issues_with_metrics)
    stats_time_to_close = None
    if num_issues_closed > 0:
        stats_time_to_close = get_stats_time_to_close(issues_with_metrics)

    stats_time_to_answer = get_stats_time_to_answer(issues_with_metrics)
    stats_time_in_draft = get_stats_time_in_draft(issues_with_metrics)
    stats_pr_comments = get_stats_pr_comments(issues_with_metrics)

    num_mentor_count = 0
    if enable_mentor_count:
        num_mentor_count = get_mentor_count(issues_with_metrics, min_mentor_count)

    # Get stats describing the time in label for each label and store it in a dictionary
    # where the key is the label and the value is the average time
    stats_time_in_labels = get_stats_time_in_labels(issues_with_metrics, labels)

    # Write the results to json and a markdown file
    write_to_json(
        issues_with_metrics=issues_with_metrics,
        stats_time_to_first_response=stats_time_to_first_response,
        stats_time_to_first_review=stats_time_to_first_review,
        stats_time_to_close=stats_time_to_close,
        stats_time_to_answer=stats_time_to_answer,
        stats_time_in_draft=stats_time_in_draft,
        stats_time_in_labels=stats_time_in_labels,
        stats_pr_comments=stats_pr_comments,
        num_issues_opened=num_issues_open,
        num_issues_closed=num_issues_closed,
        num_mentor_count=num_mentor_count,
        search_query=search_query,
        output_file=output_file,
    )

    write_to_markdown(
        issues_with_metrics=issues_with_metrics,
        average_time_to_first_response=stats_time_to_first_response,
        average_time_to_first_review=stats_time_to_first_review,
        average_time_to_close=stats_time_to_close,
        average_time_to_answer=stats_time_to_answer,
        average_time_in_draft=stats_time_in_draft,
        average_time_in_labels=stats_time_in_labels,
        stats_pr_comments=stats_pr_comments,
        num_issues_opened=num_issues_open,
        num_issues_closed=num_issues_closed,
        num_mentor_count=num_mentor_count,
        labels=labels,
        search_query=search_query,
        hide_label_metrics=hide_label_metrics,
        hide_items_closed_count=hide_items_closed_count,
        enable_mentor_count=enable_mentor_count,
        non_mentioning_links=non_mentioning_links,
        report_title=report_title,
        output_file=output_file,
        ghe=ghe,
    )

    evaluate_markdown_file_size(output_file)


if __name__ == "__main__":
    main()
