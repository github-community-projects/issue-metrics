"""A module containing unit tests for the get_discussions function in the discussions module.

Classes:
    TestGetDiscussions: A class to test the get_discussions function with mock GraphQL responses.

"""

import unittest
from unittest.mock import MagicMock

from discussions import get_discussions
from github import GithubException


class TestGetDiscussions(unittest.TestCase):
    """A class to test the get_discussions function in the discussions module."""

    def _create_mock_response(
        self, discussions, has_next_page=False, end_cursor="cursor123"
    ):
        """Helper method to create a mock GraphQL response body."""
        return {
            "data": {
                "search": {
                    "edges": [{"node": discussion} for discussion in discussions],
                    "pageInfo": {"hasNextPage": has_next_page, "endCursor": end_cursor},
                }
            }
        }

    def test_get_discussions_single_page(self):
        """Test the get_discussions function with a single page of results."""
        # Mock data for two discussions
        mock_discussions = [
            {
                "title": "Discussion 1",
                "url": "https://github.com/user/repo/discussions/1",
                "createdAt": "2021-01-01T00:00:00Z",
                "comments": {"nodes": [{"createdAt": "2021-01-01T00:01:00Z"}]},
                "answerChosenAt": None,
                "closedAt": None,
            },
            {
                "title": "Discussion 2",
                "url": "https://github.com/user/repo/discussions/2",
                "createdAt": "2021-01-02T00:00:00Z",
                "comments": {"nodes": [{"createdAt": "2021-01-02T00:01:00Z"}]},
                "answerChosenAt": "2021-01-03T00:00:00Z",
                "closedAt": "2021-01-04T00:00:00Z",
            },
        ]

        github_connection = MagicMock()
        # graphql_query returns (headers, response_json)
        github_connection.requester.graphql_query.return_value = (
            {},
            self._create_mock_response(mock_discussions, has_next_page=False),
        )

        discussions = get_discussions(
            github_connection, "repo:user/repo type:discussions query"
        )

        # Check that the function returns the expected discussions
        self.assertEqual(len(discussions), 2)
        self.assertEqual(discussions[0]["title"], "Discussion 1")
        self.assertEqual(discussions[1]["title"], "Discussion 2")

        # Verify only one API call was made
        self.assertEqual(github_connection.requester.graphql_query.call_count, 1)

    def test_get_discussions_multiple_pages(self):
        """Test the get_discussions function with multiple pages of results."""
        # Mock data for pagination
        page1_discussions = [
            {
                "title": "Discussion 1",
                "url": "https://github.com/user/repo/discussions/1",
                "createdAt": "2021-01-01T00:00:00Z",
                "comments": {"nodes": [{"createdAt": "2021-01-01T00:01:00Z"}]},
                "answerChosenAt": None,
                "closedAt": None,
            }
        ]

        page2_discussions = [
            {
                "title": "Discussion 2",
                "url": "https://github.com/user/repo/discussions/2",
                "createdAt": "2021-01-02T00:00:00Z",
                "comments": {"nodes": [{"createdAt": "2021-01-02T00:01:00Z"}]},
                "answerChosenAt": None,
                "closedAt": None,
            }
        ]

        github_connection = MagicMock()
        # Return a different page for each call
        github_connection.requester.graphql_query.side_effect = [
            (
                {},
                self._create_mock_response(
                    page1_discussions, has_next_page=True, end_cursor="cursor123"
                ),
            ),
            ({}, self._create_mock_response(page2_discussions, has_next_page=False)),
        ]

        discussions = get_discussions(
            github_connection, "repo:user/repo type:discussions query"
        )

        # Check that all discussions were returned
        self.assertEqual(len(discussions), 2)
        self.assertEqual(discussions[0]["title"], "Discussion 1")
        self.assertEqual(discussions[1]["title"], "Discussion 2")

        # Verify that two API calls were made
        self.assertEqual(github_connection.requester.graphql_query.call_count, 2)

        # Verify the second call paginated using the first page's end cursor
        second_call_variables = (
            github_connection.requester.graphql_query.call_args_list[1].args[1]
        )
        self.assertEqual(second_call_variables["cursor"], "cursor123")

    def test_get_discussions_propagates_github_exception(self):
        """A GithubException raised by graphql_query propagates to the caller."""
        github_connection = MagicMock()
        github_connection.requester.graphql_query.side_effect = GithubException(
            500, {"message": "server error"}, None
        )

        with self.assertRaises(GithubException):
            get_discussions(github_connection, "repo:user/repo type:discussions query")

    def test_get_discussions_paginates_comments(self):
        """Comments beyond the first page are fetched when max_comments allows."""

        def comment(index):
            return {
                "createdAt": "2021-01-01T00:00:00Z",
                "author": {"login": f"user{index}", "__typename": "User"},
            }

        first_page = [comment(index) for index in range(100)]
        second_page = [comment(index) for index in range(100, 150)]

        discussion = {
            "id": "D_kwDO",
            "title": "Discussion 1",
            "url": "https://github.com/user/repo/discussions/1",
            "createdAt": "2021-01-01T00:00:00Z",
            "author": {"login": "author", "__typename": "User"},
            "comments": {
                "nodes": first_page,
                "pageInfo": {"hasNextPage": True, "endCursor": "comment100"},
            },
            "answerChosenAt": None,
            "closedAt": None,
        }

        github_connection = MagicMock()
        github_connection.requester.graphql_query.side_effect = [
            ({}, self._create_mock_response([discussion], has_next_page=False)),
            (
                {},
                {
                    "data": {
                        "node": {
                            "comments": {
                                "nodes": second_page,
                                "pageInfo": {
                                    "hasNextPage": False,
                                    "endCursor": "comment150",
                                },
                            }
                        }
                    }
                },
            ),
        ]

        discussions = get_discussions(
            github_connection, "repo:user/repo type:discussions query", max_comments=150
        )

        # All 150 comments are collected, not just the first page of 100
        self.assertEqual(len(discussions[0]["comments"]["nodes"]), 150)

        # A follow-up query was made for the remaining comments
        self.assertEqual(github_connection.requester.graphql_query.call_count, 2)
        comment_call_variables = (
            github_connection.requester.graphql_query.call_args_list[1].args[1]
        )
        self.assertEqual(comment_call_variables["id"], "D_kwDO")
        self.assertEqual(comment_call_variables["cursor"], "comment100")
        self.assertEqual(comment_call_variables["pageSize"], 50)

    def test_get_discussions_stops_paginating_comments_at_max_comments(self):
        """No extra request is made once max_comments comments are collected."""
        discussion = {
            "id": "D_kwDO",
            "title": "Discussion 1",
            "url": "https://github.com/user/repo/discussions/1",
            "createdAt": "2021-01-01T00:00:00Z",
            "author": {"login": "author", "__typename": "User"},
            "comments": {
                "nodes": [
                    {
                        "createdAt": "2021-01-01T00:00:00Z",
                        "author": {"login": "user1", "__typename": "User"},
                    }
                ],
                "pageInfo": {"hasNextPage": True, "endCursor": "comment1"},
            },
            "answerChosenAt": None,
            "closedAt": None,
        }

        github_connection = MagicMock()
        github_connection.requester.graphql_query.return_value = (
            {},
            self._create_mock_response([discussion], has_next_page=False),
        )

        discussions = get_discussions(
            github_connection, "repo:user/repo type:discussions query", max_comments=1
        )

        self.assertEqual(len(discussions[0]["comments"]["nodes"]), 1)
        self.assertEqual(github_connection.requester.graphql_query.call_count, 1)

    def test_get_discussions_with_no_comments(self):
        """A discussion without a comments connection triggers no extra request."""
        discussion = {
            "id": "D_kwDO",
            "title": "Discussion 1",
            "url": "https://github.com/user/repo/discussions/1",
            "createdAt": "2021-01-01T00:00:00Z",
            "author": {"login": "author", "__typename": "User"},
            "comments": None,
            "answerChosenAt": None,
            "closedAt": None,
        }

        github_connection = MagicMock()
        github_connection.requester.graphql_query.return_value = (
            {},
            self._create_mock_response([discussion], has_next_page=False),
        )

        discussions = get_discussions(
            github_connection, "repo:user/repo type:discussions query", max_comments=150
        )

        self.assertIsNone(discussions[0]["comments"])
        self.assertEqual(github_connection.requester.graphql_query.call_count, 1)
