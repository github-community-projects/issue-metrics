"""Unit tests for the search module."""

import unittest
from unittest.mock import MagicMock

from github import GithubException
from search import get_owners_and_repositories, print_error_messages, search_issues


class TestSearchIssues(unittest.TestCase):
    """Unit tests for the search_issues function.

    This class contains unit tests for the search_issues function in the
    issue_metrics module. The tests use the unittest module and the unittest.mock
    module to mock the GitHub API and test the function in isolation.

    Methods:
        test_search_issues_with_owner_and_repository:
            Test that search_issues with owner/repo returns the correct issues.
        test_search_issues_with_just_owner_or_org:
            Test that search_issues with just an owner/org returns the correct issues.
        test_search_issues_with_just_owner_or_org_with_bypass:
            Test that search_issues with just an owner/org returns the correct issues
            with rate limit bypass enabled.

    """

    def test_search_issues_with_owner_and_repository(self):
        """Test that search_issues with owner/repo returns the correct issues."""

        mock_issues = [
            MagicMock(title="Issue 1"),
            MagicMock(title="Issue 2"),
        ]

        mock_connection = MagicMock()
        mock_connection.search_issues.return_value = mock_issues

        repo_with_owner = {"owner": "owner1", "repository": "repo1"}
        owners_and_repositories = [repo_with_owner]
        issues = search_issues("is:open", mock_connection, owners_and_repositories)
        self.assertEqual(issues, mock_issues)

    def test_search_issues_with_just_owner_or_org(self):
        """Test that search_issues with just an owner/org returns the correct issues."""

        mock_issues = [
            MagicMock(title="Issue 1"),
            MagicMock(title="Issue 2"),
            MagicMock(title="Issue 3"),
        ]

        mock_connection = MagicMock()
        mock_connection.search_issues.return_value = mock_issues

        org = {"owner": "org1"}
        owners = [org]
        issues = search_issues("is:open", mock_connection, owners)
        self.assertEqual(issues, mock_issues)

    def test_search_issues_with_just_owner_or_org_with_bypass(self):
        """Test that search_issues with just an owner/org returns the correct issues."""

        mock_issues = [
            MagicMock(title="Issue 1"),
            MagicMock(title="Issue 2"),
            MagicMock(title="Issue 3"),
        ]

        mock_connection = MagicMock()
        mock_connection.search_issues.return_value = mock_issues

        org = {"owner": "org1"}
        owners = [org]
        issues = search_issues(
            "is:open", mock_connection, owners, rate_limit_bypass=True
        )
        self.assertEqual(issues, mock_issues)


class TestGetOwnerAndRepository(unittest.TestCase):
    """Unit tests for the get_owners_and_repositories function.

    This class contains unit tests for the get_owners_and_repositories function in the
    issue_metrics module. The tests use the unittest module and the unittest.mock
    module to mock the GitHub API and test the function in isolation.

    Methods:
        test_get_owners_with_owner_and_repo_in_query: Test get both owner and repo.
        test_get_owner_and_repositories_without_repo_in_query: Test get just owner.
        test_get_owners_and_repositories_without_either_in_query: Test get neither.
        test_get_owners_and_repositories_with_multiple_entries: Test get multiple entries.
        test_get_owners_and_repositories_with_org: Test get org as owner.
        test_get_owners_and_repositories_with_user: Test get user as owner.
    """

    def test_get_owners_with_owner_and_repo_in_query(self):
        """Test get both owner and repo."""
        result = get_owners_and_repositories("repo:owner1/repo1")
        self.assertEqual(result[0].get("owner"), "owner1")
        self.assertEqual(result[0].get("repository"), "repo1")

    def test_get_owner_and_repositories_without_repo_in_query(self):
        """Test get just owner."""
        result = get_owners_and_repositories("org:owner1")
        self.assertEqual(result[0].get("owner"), "owner1")
        self.assertIsNone(result[0].get("repository"))

    def test_get_owners_and_repositories_without_either_in_query(self):
        """Test get neither."""
        result = get_owners_and_repositories("is:blah")
        self.assertEqual(result, [])

    def test_get_owners_and_repositories_with_multiple_entries(self):
        """Test get multiple entries."""
        result = get_owners_and_repositories("repo:owner1/repo1 org:owner2")
        self.assertEqual(result[0].get("owner"), "owner1")
        self.assertEqual(result[0].get("repository"), "repo1")
        self.assertEqual(result[1].get("owner"), "owner2")
        self.assertIsNone(result[1].get("repository"))

    def test_get_owners_and_repositories_with_org(self):
        """Test get org as owner."""
        result = get_owners_and_repositories("org:owner1")
        self.assertEqual(result[0].get("owner"), "owner1")
        self.assertIsNone(result[0].get("repository"))

    def test_get_owners_and_repositories_with_user(self):
        """Test get user as owner."""
        result = get_owners_and_repositories("user:owner1")
        self.assertEqual(result[0].get("owner"), "owner1")
        self.assertIsNone(result[0].get("repository"))

    def test_get_owners_and_repositories_handles_owner_prefix(self):
        """Test get owner: prefix sets the owner."""
        result = get_owners_and_repositories("owner:octocat")
        self.assertEqual(result[0]["owner"], "octocat")


class TestSearchCoverageGaps(unittest.TestCase):
    """Covers search.py exception and parser branches."""

    def _assert_exception_exits(self, exception_instance):

        mock_connection = MagicMock()
        mock_connection.search_issues.side_effect = exception_instance

        with self.assertRaises(SystemExit):
            search_issues(
                "is:open",
                mock_connection,
                [{"owner": "o", "repository": "r"}],
                rate_limit_bypass=True,
            )

    def test_forbidden_error_exits(self):
        """403 GithubException triggers a clean SystemExit."""
        self._assert_exception_exits(
            GithubException(403, {"message": "forbidden"}, None)
        )

    def test_not_found_error_exits(self):
        """404 GithubException triggers a clean SystemExit."""
        self._assert_exception_exits(
            GithubException(404, {"message": "not found"}, None)
        )

    def test_connection_error_exits(self):
        """ConnectionError triggers SystemExit."""
        self._assert_exception_exits(ConnectionError("boom"))

    def test_os_error_exits(self):
        """OSError (parent of requests.ConnectionError) triggers SystemExit."""
        self._assert_exception_exits(OSError("network unreachable"))

    def test_authentication_failed_exits(self):
        """401 GithubException triggers a clean SystemExit."""
        self._assert_exception_exits(
            GithubException(401, {"message": "auth failed"}, None)
        )

    def test_unprocessable_entity_exits(self):
        """422 GithubException triggers a clean SystemExit."""
        self._assert_exception_exits(
            GithubException(
                422,
                {
                    "message": "Validation Failed",
                    "errors": [{"message": "bad query"}],
                },
                None,
            )
        )

    def test_generic_github_exception_exits(self):
        """Generic GithubException triggers a clean SystemExit."""
        self._assert_exception_exits(
            GithubException(500, {"message": "server error"}, None)
        )

    def test_print_error_messages_with_errors_attr(self):
        """print_error_messages iterates over .data['errors'] when present."""
        error = GithubException(
            422,
            {"errors": [{"message": "bad query"}, {"message": "another"}]},
            None,
        )
        print_error_messages(error)

    def test_print_error_messages_without_errors(self):
        """print_error_messages handles exceptions without error details."""
        error = GithubException(500, {"message": "server error"}, None)
        print_error_messages(error)
