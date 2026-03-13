"""A module for managing environment variables used in GitHub metrics calculation.

This module defines a class for encapsulating environment variables
and a function to retrieve these variables.

Classes:
    EnvVars: Represents the collection of environment variables used in the script.

Functions:
    get_env_vars: Retrieves and returns an instance of EnvVars populated with environment variables.
"""

import os
from os.path import dirname, join
from typing import List

from dotenv import load_dotenv


class EnvVars:
    # pylint: disable=too-many-instance-attributes
    """
    Environment variables

    Attributes:
        gh_app_id (int | None): The GitHub App ID to use for authentication
        gh_app_installation_id (int | None): The GitHub App Installation ID to use for
            authentication
        gh_app_private_key_bytes (bytes): The GitHub App Private Key as bytes to use for
            authentication
        gh_token (str | None): GitHub personal access token (PAT) for API authentication
        ghe (str): The GitHub Enterprise URL to use for authentication
        hide_assignee (bool): If true, the assignee's information is hidden in the output
        hide_author (bool): If true, the author's information is hidden in the output
        hide_items_closed_count (bool): If true, the number of items closed metric is hidden
            in the output
        hide_label_metrics (bool): If true, the label metrics are hidden in the output
        hide_time_to_answer (bool): If true, the time to answer discussions is hidden in the output
        hide_time_to_close (bool): If true, the time to close metric is hidden in the output
        hide_time_to_first_response (bool): If true, the time to first response metric is hidden
            in the output
        hide_time_to_first_review (bool): If true, the time to first review metric is hidden in the output
        hide_created_at (bool): If true, the created at timestamp is hidden in the output
        hide_status (bool): If true, the status column is hidden in the output
        ignore_users (List[str]): List of usernames to ignore when calculating metrics
        labels_to_measure (List[str]): List of labels to measure how much time the label is applied
        enable_mentor_count (bool): If set to TRUE, compute number of mentors
        min_mentor_comments (str): If set, defines the minimum number of comments for mentors
        max_comments_eval (str): If set, defines the maximum number of comments to look
            at for mentor evaluation
        heavily_involved_cutoff (str): If set, defines the cutoff after which heavily
            involved commentors in
        search_query (str): Search query used to filter issues/prs/discussions on GitHub
        non_mentioning_links (bool): If set to TRUE, links do not cause a notification
            in the destination repository
        report_title (str): The title of the report
        output_file (str): The name of the file to write the report to
        rate_limit_bypass (bool): If set to TRUE, bypass the rate limit for the GitHub API
        draft_pr_tracking (bool): If set to TRUE, track PR time in draft state
            in addition to other metrics
        hide_pr_statistics (bool): If set to TRUE, hide PR comment statistics in the output
        hide_items_list (bool): If set to TRUE, hide the list of individual items in the report
        group_by (str | None): If set, group items by the specified field (e.g., 'author')
        sort_by (str | None): If set, sort items by the specified field (e.g., 'time_to_close')
        sort_order (str): Sort order, either 'asc' for ascending or 'desc' for descending
    """

    def __init__(
        self,
        gh_app_id: int | None,
        gh_app_installation_id: int | None,
        gh_app_private_key_bytes: bytes,
        gh_app_enterprise_only: bool,
        gh_token: str | None,
        ghe: str | None,
        hide_assignee: bool,
        hide_author: bool,
        hide_items_closed_count: bool,
        hide_label_metrics: bool,
        hide_time_to_answer: bool,
        hide_time_to_close: bool,
        hide_time_to_first_response: bool,
        hide_time_to_first_review: bool,
        hide_created_at: bool,
        hide_status: bool,
        ignore_user: List[str],
        labels_to_measure: List[str],
        enable_mentor_count: bool,
        min_mentor_comments: str,
        max_comments_eval: str,
        heavily_involved_cutoff: str,
        search_query: str,
        non_mentioning_links: bool,
        report_title: str,
        output_file: str,
        rate_limit_bypass: bool = False,
        draft_pr_tracking: bool = False,
        hide_pr_statistics: bool = True,
        hide_items_list: bool = False,
        group_by: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
    ):
        self.gh_app_id = gh_app_id
        self.gh_app_installation_id = gh_app_installation_id
        self.gh_app_private_key_bytes = gh_app_private_key_bytes
        self.gh_app_enterprise_only = gh_app_enterprise_only
        self.gh_token = gh_token
        self.ghe = ghe
        self.ignore_users = ignore_user
        self.labels_to_measure = labels_to_measure
        self.hide_assignee = hide_assignee
        self.hide_author = hide_author
        self.hide_items_closed_count = hide_items_closed_count
        self.hide_label_metrics = hide_label_metrics
        self.hide_time_to_answer = hide_time_to_answer
        self.hide_time_to_close = hide_time_to_close
        self.hide_time_to_first_response = hide_time_to_first_response
        self.hide_time_to_first_review = hide_time_to_first_review
        self.hide_created_at = hide_created_at
        self.hide_status = hide_status
        self.enable_mentor_count = enable_mentor_count
        self.min_mentor_comments = min_mentor_comments
        self.max_comments_eval = max_comments_eval
        self.heavily_involved_cutoff = heavily_involved_cutoff
        self.search_query = search_query
        self.non_mentioning_links = non_mentioning_links
        self.report_title = report_title
        self.output_file = output_file
        self.rate_limit_bypass = rate_limit_bypass
        self.draft_pr_tracking = draft_pr_tracking
        self.hide_pr_statistics = hide_pr_statistics
        self.hide_items_list = hide_items_list
        self.group_by = group_by
        self.sort_by = sort_by
        self.sort_order = sort_order

    def __repr__(self):
        return (
            "EnvVars("
            f"{self.gh_app_id}, "
            f"{self.gh_app_installation_id}, "
            f"{self.gh_app_private_key_bytes}, "
            f"{self.gh_app_enterprise_only}, "
            f"{self.gh_token}, "
            f"{self.ghe}, "
            f"{self.hide_assignee}, "
            f"{self.hide_author}, "
            f"{self.hide_items_closed_count}, "
            f"{self.hide_label_metrics}, "
            f"{self.hide_time_to_answer}, "
            f"{self.hide_time_to_close}, "
            f"{self.hide_time_to_first_response}, "
            f"{self.hide_time_to_first_review}, "
            f"{self.hide_created_at}, "
            f"{self.hide_status}, "
            f"{self.ignore_users}, "
            f"{self.labels_to_measure}, "
            f"{self.enable_mentor_count}, "
            f"{self.min_mentor_comments}, "
            f"{self.max_comments_eval}, "
            f"{self.heavily_involved_cutoff}, "
            f"{self.search_query}, "
            f"{self.non_mentioning_links}, "
            f"{self.report_title}, "
            f"{self.output_file}, "
            f"{self.rate_limit_bypass}, "
            f"{self.draft_pr_tracking}, "
            f"{self.hide_pr_statistics}, "
            f"{self.hide_items_list}, "
            f"{self.group_by}, "
            f"{self.sort_by}, "
            f"{self.sort_order})"
        )


def get_bool_env_var(env_var_name: str, default: bool = False) -> bool:
    """Get a boolean environment variable.

    Args:
        env_var_name: The name of the environment variable to retrieve.
        default: The default value to return if the environment variable is not set.

    Returns:
        The value of the environment variable as a boolean.
    """
    ev = os.environ.get(env_var_name, "")
    if ev == "" and default:
        return default
    return ev.strip().lower() == "true"


def get_int_env_var(env_var_name: str) -> int | None:
    """Get an integer environment variable.

    Args:
        env_var_name: The name of the environment variable to retrieve.

    Returns:
        The value of the environment variable as an integer or None.
    """
    env_var = os.environ.get(env_var_name)
    if env_var is None or not env_var.strip():
        return None
    try:
        return int(env_var)
    except ValueError:
        return None


def get_env_vars(test: bool = False) -> EnvVars:
    """
    Get the environment variables for use in the script.

    Returns EnvVars object with all environment variables
    """
    if not test:
        dotenv_path = join(dirname(__file__), ".env")
        load_dotenv(dotenv_path)

    search_query = os.getenv("SEARCH_QUERY")
    if not search_query:
        raise ValueError("SEARCH_QUERY environment variable not set")

    gh_app_id = get_int_env_var("GH_APP_ID")
    gh_app_private_key_bytes = os.environ.get("GH_APP_PRIVATE_KEY", "").encode("utf8")
    gh_app_installation_id = get_int_env_var("GH_APP_INSTALLATION_ID")
    gh_app_enterprise_only = get_bool_env_var("GITHUB_APP_ENTERPRISE_ONLY")

    if gh_app_id and (not gh_app_private_key_bytes or not gh_app_installation_id):
        raise ValueError(
            "GH_APP_ID set and GH_APP_INSTALLATION_ID or GH_APP_PRIVATE_KEY variable not set"
        )

    gh_token = os.getenv("GH_TOKEN")
    if (
        not gh_app_id
        and not gh_app_private_key_bytes
        and not gh_app_installation_id
        and not gh_token
    ):
        raise ValueError("GH_TOKEN environment variable not set")

    ghe = os.getenv("GH_ENTERPRISE_URL", default="").strip()

    labels_to_measure_list: List[str] = []
    labels_to_measure: str | None = os.getenv("LABELS_TO_MEASURE")
    if labels_to_measure:
        labels_to_measure_list = labels_to_measure.split(",")

    ignore_users_list: List[str] = []
    ignore_users: str | None = os.getenv("IGNORE_USERS")
    if ignore_users:
        ignore_users_list = ignore_users.split(",")

    report_title = os.getenv("REPORT_TITLE", "Issue Metrics")
    output_file = os.getenv("OUTPUT_FILE", "")
    rate_limit_bypass = get_bool_env_var("RATE_LIMIT_BYPASS", False)
    draft_pr_tracking = get_bool_env_var("DRAFT_PR_TRACKING", False)

    # Grouping and sorting options
    group_by = os.getenv("GROUP_BY", "").strip().lower() or None
    sort_by = os.getenv("SORT_BY", "").strip().lower() or None
    sort_order = os.getenv("SORT_ORDER", "asc").strip().lower()
    if sort_order not in ["asc", "desc"]:
        sort_order = "asc"

    # Hidden columns
    hide_assignee = get_bool_env_var("HIDE_ASSIGNEE", False)
    hide_author = get_bool_env_var("HIDE_AUTHOR", False)
    hide_items_closed_count = get_bool_env_var("HIDE_ITEMS_CLOSED_COUNT", False)
    hide_label_metrics = get_bool_env_var("HIDE_LABEL_METRICS", False)
    hide_time_to_answer = get_bool_env_var("HIDE_TIME_TO_ANSWER", False)
    hide_time_to_close = get_bool_env_var("HIDE_TIME_TO_CLOSE", False)
    hide_time_to_first_response = get_bool_env_var("HIDE_TIME_TO_FIRST_RESPONSE", False)
    hide_time_to_first_review = get_bool_env_var("HIDE_TIME_TO_FIRST_REVIEW", False)
    hide_created_at = get_bool_env_var("HIDE_CREATED_AT", True)
    hide_status = get_bool_env_var("HIDE_STATUS", True)
    hide_pr_statistics = get_bool_env_var("HIDE_PR_STATISTICS", True)
    hide_items_list = get_bool_env_var("HIDE_ITEMS_LIST", False)
    enable_mentor_count = get_bool_env_var("ENABLE_MENTOR_COUNT", False)
    min_mentor_comments = os.getenv("MIN_MENTOR_COMMENTS", "10")
    max_comments_eval = os.getenv("MAX_COMMENTS_EVAL", "20")
    heavily_involved_cutoff = os.getenv("HEAVILY_INVOLVED_CUTOFF", "3")
    non_mentioning_links = get_bool_env_var("NON_MENTIONING_LINKS", False)

    return EnvVars(
        gh_app_id,
        gh_app_installation_id,
        gh_app_private_key_bytes,
        gh_app_enterprise_only,
        gh_token,
        ghe,
        hide_assignee,
        hide_author,
        hide_items_closed_count,
        hide_label_metrics,
        hide_time_to_answer,
        hide_time_to_close,
        hide_time_to_first_response,
        hide_time_to_first_review,
        hide_created_at,
        hide_status,
        ignore_users_list,
        labels_to_measure_list,
        enable_mentor_count,
        min_mentor_comments,
        max_comments_eval,
        heavily_involved_cutoff,
        search_query,
        non_mentioning_links,
        report_title,
        output_file,
        rate_limit_bypass,
        draft_pr_tracking,
        hide_pr_statistics,
        hide_items_list,
        group_by,
        sort_by,
        sort_order,
    )
