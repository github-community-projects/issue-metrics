"""A module to search for issues in a GitHub repository."""

import sys
from typing import List

from github import Github, GithubException, RateLimitExceededException


def search_issues(
    search_query: str,
    github_connection: Github,
    owners_and_repositories: List[dict],
) -> list:
    """
    Searches for issues/prs/discussions in a GitHub repository that match
    the given search query and handles errors related to GitHub API responses.

    Args:
        search_query (str): The search query to use for finding issues/prs/discussions.
        github_connection (Github): A connection to the GitHub API.
        owners_and_repositories (List[dict]): A list of dictionaries containing
            the owner and repository names.

    Returns:
        list: A list of issues that match the search query.
    """
    repos_and_owners_string = ""
    for item in owners_and_repositories:
        repos_and_owners_string += (
            f"{item.get('owner', '')}/{item.get('repository', '')} "
        )

    print("Searching for issues...")
    try:
        issues = []
        search_results = github_connection.search_issues(search_query, per_page=100)
        for issue in search_results:
            print(issue.title)
            issues.append(issue)

    except RateLimitExceededException as e:
        print(
            "GitHub API rate limit exceeded; wait for the rate limit to reset and try again."
        )
        print_error_messages(e)
        sys.exit(1)
    except GithubException as e:
        status = e.status if hasattr(e, "status") else None
        if status == 403:
            print(f"You do not have permission to view a repository \
from: '{repos_and_owners_string}'; Check your API Token.")
            print_error_messages(e)
            sys.exit(1)
        elif status == 404:
            print(f"The repository could not be found; \
Check the repository owner and names: '{repos_and_owners_string}")
            print_error_messages(e)
            sys.exit(1)
        elif status == 401:
            print("Authentication failed; Check your API Token.")
            print_error_messages(e)
            sys.exit(1)
        elif status == 422:
            print("The search query is invalid; Check the search query.")
            print_error_messages(e)
            sys.exit(1)
        else:
            print(f"An error occurred: {e}")
            print_error_messages(e)
            sys.exit(1)
    except (ConnectionError, OSError) as e:
        print(
            "There was a connection error; Check your internet connection or API Token."
        )
        print(f"Error: {e}")
        sys.exit(1)

    return issues


def print_error_messages(error: GithubException):
    """Prints the error messages from the GitHub API response.

    Args:
        Error (GithubException): The error object from the GitHub API response.

    """
    if hasattr(error, "data") and isinstance(error.data, dict):
        errors = error.data.get("errors", [])
        for e in errors:
            if isinstance(e, dict):
                print(f"Error: {e.get('message')}")


def get_owners_and_repositories(
    search_query: str,
) -> List[dict]:
    """Get the owners and repositories from the search query.

    Args:
        search_query (str): The search query used to search for issues.

    Returns:
        List[dict]: A list of dictionaries of owners and repositories.

    """
    search_query_split = search_query.split(" ")
    results_list = []
    for item in search_query_split:
        result = {}
        if "repo:" in item and "/" in item:
            result["owner"] = item.split(":")[1].split("/")[0]
            result["repository"] = item.split(":")[1].split("/")[1]
        if "org:" in item or "owner:" in item or "user:" in item:
            result["owner"] = item.split(":")[1]
        if "user:" in item:
            result["owner"] = item.split(":")[1]
        if "owner:" in item:
            result["owner"] = item.split(":")[1]
        if result:
            results_list.append(result)

    return results_list
