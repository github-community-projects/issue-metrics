"""
This module provides functions for working with discussions in a GitHub repository.

Functions:
    get_discussions(github_connection: Github, search_query: str) -> list:
        Get a list of discussions in a GitHub repository that match the search query.

"""

from github import Github

COMMENTS_PAGE_SIZE = 100

# Fetches further pages of a single discussion's comments once the first page
# returned by the search query is exhausted.
COMMENTS_QUERY = """
query($id: ID!, $cursor: String, $pageSize: Int!) {
    node(id: $id) {
        ... on Discussion {
            comments(first: $pageSize, after: $cursor) {
                nodes {
                    createdAt
                    author {
                        login
                        __typename
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }
}
"""


def _fetch_remaining_comments(
    github_connection: Github, discussion: dict, max_comments: int
):
    """Page a single discussion's comments until max_comments is satisfied.

    The search query returns only the first page of each discussion's comments,
    so without this the mentor counting branch silently stops at that page.

    Args:
        github_connection (Github): An authenticated PyGithub connection.
        discussion (dict): A discussion node, updated in place.
        max_comments (int): Maximum number of comments to collect.
    """
    comments = discussion.get("comments")
    if not comments:
        return

    nodes = comments.get("nodes", [])
    page_info = comments.get("pageInfo") or {}

    while len(nodes) < max_comments and page_info.get("hasNextPage"):
        variables = {
            "id": discussion["id"],
            "cursor": page_info.get("endCursor"),
            "pageSize": min(COMMENTS_PAGE_SIZE, max_comments - len(nodes)),
        }
        _, response_json = github_connection.requester.graphql_query(
            COMMENTS_QUERY, variables
        )
        page = response_json["data"]["node"]["comments"]
        nodes.extend(page.get("nodes", []))
        page_info = page.get("pageInfo") or {}

    comments["pageInfo"] = page_info


def get_discussions(
    github_connection: Github, search_query: str, max_comments: int = 20
):
    """Get a list of discussions in a GitHub repository that match the search query.

    Args:
        github_connection (Github): An authenticated PyGithub connection.
            GitHub Enterprise routing is handled by the connection's base URL.
        search_query (str): The search query to filter discussions by.
        max_comments (int): Maximum number of comments to collect per discussion.
            Values above the GraphQL page size trigger extra requests, so that
            discussions match the issue and pull request branches, which keep
            paginating until the limit is satisfied.

    Returns:
        list: A list of discussions in the repository that match the search query.
    """
    # Construct the GraphQL query with pagination
    query = """
    query($query: String!, $cursor: String) {
        search(query: $query, type: DISCUSSION, first: 100, after: $cursor) {
            edges {
                node {
                    ... on Discussion {
                        id
                        title
                        url
                        createdAt
                        author {
                            login
                            __typename
                        }
                        comments(first: 100) {
                            nodes {
                                createdAt
                                author {
                                    login
                                    __typename
                                }
                            }
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                        }
                        answerChosenAt
                        closedAt
                    }
                }
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """

    # Remove the type:discussions filter from the search query
    search_query = search_query.replace("type:discussions ", "")

    # PyGithub's graphql_query reuses the connection's auth, base URL, and
    # GitHub Enterprise /api/graphql handling, and raises GithubException on
    # HTTP or GraphQL errors.
    discussions = []
    cursor = None

    while True:
        # Set the variables for the GraphQL query
        variables = {"query": search_query, "cursor": cursor}

        # Send the GraphQL request
        _, response_json = github_connection.requester.graphql_query(query, variables)

        data = response_json["data"]

        # Extract the discussions from the current page
        for edge in data["search"]["edges"]:
            discussion = edge["node"]
            _fetch_remaining_comments(github_connection, discussion, max_comments)
            discussions.append(discussion)

        # Check if there are more pages
        page_info = data["search"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]

    return discussions
