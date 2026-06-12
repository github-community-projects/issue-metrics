"""Unit tests for the search module."""

import unittest
from unittest.mock import MagicMock, PropertyMock, patch

import github3
import requests
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

        # Set up the mock GitHub connection object
        mock_issues = [
            MagicMock(title="Issue 1"),
            MagicMock(title="Issue 2"),
        ]

        # simulating github3.structs.SearchIterator return value
        mock_search_result = MagicMock()
        mock_search_result.__iter__.return_value = iter(mock_issues)
        mock_search_result.ratelimit_remaining = 30

        mock_connection = MagicMock()
        mock_connection.search_issues.return_value = mock_search_result

        # Call search_issues and check that it returns the correct issues
        repo_with_owner = {"owner": "owner1", "repository": "repo1"}
        owners_and_repositories = [repo_with_owner]
        issues = search_issues("is:open", mock_connection, owners_and_repositories)
        self.assertEqual(issues, mock_issues)

    def test_search_issues_with_just_owner_or_org(self):
        """Test that search_issues with just an owner/org returns the correct issues."""

        # Set up the mock GitHub connection object
        mock_issues = [
            MagicMock(title="Issue 1"),
            MagicMock(title="Issue 2"),
            MagicMock(title="Issue 3"),
        ]

        # simulating github3.structs.SearchIterator return value
        mock_search_result = MagicMock()
        mock_search_result.__iter__.return_value = iter(mock_issues)
        mock_search_result.ratelimit_remaining = 30

        mock_connection = MagicMock()
        mock_connection.search_issues.return_value = mock_search_result

        # Call search_issues and check that it returns the correct issues
        org = {"owner": "org1"}
        owners = [org]
        issues = search_issues("is:open", mock_connection, owners)
        self.assertEqual(issues, mock_issues)

    def test_search_issues_with_just_owner_or_org_with_bypass(self):
        """Test that search_issues with just an owner/org returns the correct issues."""

        # Set up the mock GitHub connection object
        mock_issues = [
            MagicMock(title="Issue 1"),
            MagicMock(title="Issue 2"),
            MagicMock(title="Issue 3"),
        ]

        # simulating github3.structs.SearchIterator return value
        mock_search_result = MagicMock()
        mock_search_result.__iter__.return_value = iter(mock_issues)
        mock_search_result.ratelimit_remaining = 30

        mock_connection = MagicMock()
        mock_connection.search_issues.return_value = mock_search_result

        # Call search_issues and check that it returns the correct issues
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
    """Covers search.py rate-limit, exception, and parser branches."""

    @patch("search.sleep", return_value=None)
    def test_wait_for_api_refresh_retries_then_succeeds(self, mock_sleep):
        """Low rate limit sleeps and then continues once the limit refills."""
        iterator = MagicMock()
        # Sequence: low first, then refilled, then refilled (final exit).
        type(iterator).ratelimit_remaining = PropertyMock(side_effect=[1, 30, 30])
        iterator.__iter__.return_value = iter([MagicMock(title="I1")])

        connection = MagicMock()
        connection.search_issues.return_value = iterator

        issues = search_issues(
            "is:open", connection, [{"owner": "o", "repository": "r"}]
        )
        self.assertEqual(len(issues), 1)
        mock_sleep.assert_called()  # We did sleep at least once.

    @patch("search.sleep", return_value=None)
    def test_wait_for_api_refresh_exceeds_max_retries(self, _mock_sleep):
        """RuntimeError after the maximum number of rate-limit retries."""

        iterator = MagicMock()
        iterator.ratelimit_remaining = 0  # always too low
        iterator.__iter__.return_value = iter([])

        connection = MagicMock()
        connection.search_issues.return_value = iterator

        with self.assertRaises(RuntimeError):
            search_issues("is:open", connection, [])

    def test_periodic_refresh_after_full_page(self):
        """Refresh is invoked after each full page of results."""

        # 101 issues forces the modulo branch (idx % issues_per_page == 0).
        page_size_threshold = 100
        issues_list = [MagicMock(title=f"I{i}") for i in range(page_size_threshold + 1)]

        iterator = MagicMock()
        iterator.ratelimit_remaining = 30
        iterator.__iter__.return_value = iter(issues_list)

        connection = MagicMock()
        connection.search_issues.return_value = iterator

        # Rate-limit bypass keeps the refresh call a no-op so we can assert the
        # full iteration completed without exercising the sleep path.
        result = search_issues("is:open", connection, [], rate_limit_bypass=True)
        self.assertEqual(len(result), page_size_threshold + 1)

    def _assert_exception_exits(self, exception_instance):

        iterator = MagicMock()
        iterator.ratelimit_remaining = 30
        iterator.__iter__.side_effect = exception_instance

        connection = MagicMock()
        connection.search_issues.return_value = iterator

        with self.assertRaises(SystemExit):
            search_issues(
                "is:open",
                connection,
                [{"owner": "o", "repository": "r"}],
                rate_limit_bypass=True,
            )

    def test_forbidden_error_exits(self):
        """ForbiddenError from github3 triggers a clean SystemExit."""
        resp = MagicMock(status_code=403)
        resp.json.return_value = {"message": "forbidden"}
        self._assert_exception_exits(github3.exceptions.ForbiddenError(resp))

    def test_not_found_error_exits(self):
        """NotFoundError from github3 triggers a clean SystemExit."""
        resp = MagicMock(status_code=404)
        resp.json.return_value = {"message": "not found"}
        self._assert_exception_exits(github3.exceptions.NotFoundError(resp))

    def test_connection_error_exits(self):
        """ConnectionError wrapping a requests error triggers SystemExit."""
        self._assert_exception_exits(
            github3.exceptions.ConnectionError(requests.ConnectionError("boom"))
        )

    def test_authentication_failed_exits(self):
        """AuthenticationFailed from github3 triggers a clean SystemExit."""
        resp = MagicMock(status_code=401)
        resp.json.return_value = {"message": "auth failed"}
        self._assert_exception_exits(github3.exceptions.AuthenticationFailed(resp))

    def test_unprocessable_entity_exits(self):
        """UnprocessableEntity from github3 triggers a clean SystemExit."""
        resp = MagicMock(status_code=422)
        resp.json.return_value = {
            "message": "Validation Failed",
            "errors": [{"message": "bad query"}],
        }
        self._assert_exception_exits(github3.exceptions.UnprocessableEntity(resp))

    def test_print_error_messages_with_errors_attr(self):
        """print_error_messages iterates over .errors when present."""

        error = MagicMock()
        error.errors = [{"message": "bad query"}, {"message": "another"}]
        # Should not raise.
        print_error_messages(error)
