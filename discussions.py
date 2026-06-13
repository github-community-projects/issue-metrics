"""
This module provides functions for working with discussions in a GitHub repository.

Functions:
    get_discussions(repo_url: str, token: str, search_query: str) -> List[Dict]:
        Get a list of discussions in a GitHub repository that match the search query.

"""

import requests


def get_discussions(token: str, search_query: str, ghe: str):
    """Get a list of discussions in a GitHub repository that match the search query.

    Args:
        token (str): A personal access token for GitHub.
        search_query (str): The search query to filter discussions by.
        ghe (str): GitHub Enterprise URL if applicable, or None for github.com.

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

    # Send the GraphQL request
    api_endpoint = f"{ghe}/api" if ghe else "https://api.github.com"
    headers = {"Authorization": f"Bearer {token}"}

    discussions = []
    cursor = None

    while True:
        # Set the variables for the GraphQL query
        variables = {"query": search_query, "cursor": cursor}

        # Send the GraphQL request
        response = requests.post(
            f"{api_endpoint}/graphql",
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=60,
        )

        # Check for errors in the GraphQL response
        if response.status_code != 200:
            raise ValueError(
                f"GraphQL query failed with status code {response.status_code}"
            )

        response_json = response.json()
        if "errors" in response_json:
            raise ValueError(f"GraphQL query failed: {response_json['errors']}")

        data = response_json["data"]

        # Extract the discussions from the current page
        for edge in data["search"]["edges"]:
            discussions.append(edge["node"])

        # Check if there are more pages
        page_info = data["search"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]

    return discussions
