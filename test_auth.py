"""A module containing unit tests for the auth module.

This module contains unit tests for the functions in the auth module
that authenticate to github.

Classes:
    TestAuthToGithub: A class to test the auth_to_github function.

"""

import unittest
from unittest.mock import MagicMock, patch

import github3
import requests
from auth import auth_to_github, get_github_app_installation_token


class TestAuthToGithub(unittest.TestCase):
    """Test the auth_to_github function."""

    @patch("github3.github.GitHub.login_as_app_installation")
    def test_auth_to_github_with_github_app(self, mock_login):
        """
        Test the auth_to_github function when GitHub app
        parameters provided.
        """
        mock_login.return_value = MagicMock()
        result = auth_to_github("", 12345, 678910, b"hello", "", False)

        mock_login.assert_called_once_with(b"hello", "12345", 678910)
        self.assertIsInstance(result, github3.github.GitHub, False)

    def test_auth_to_github_with_token(self):
        """
        Test the auth_to_github function when the token is provided.
        """
        result = auth_to_github("token", None, None, b"", "", False)

        self.assertIsInstance(result, github3.github.GitHub, False)

    def test_auth_to_github_without_authentication_information(self):
        """
        Test the auth_to_github function when authentication information is not provided.
        Expect a ValueError to be raised.
        """
        with self.assertRaises(ValueError):
            auth_to_github("", None, None, b"", "", False)

    def test_auth_to_github_with_ghe(self):
        """
        Test the auth_to_github function when the GitHub Enterprise URL is provided.
        """
        result = auth_to_github(
            "token", None, None, b"", "https://github.example.com", False
        )

        self.assertIsInstance(result, github3.github.GitHubEnterprise, False)

    @patch("github3.github.GitHubEnterprise")
    def test_auth_to_github_with_ghe_and_ghe_app(self, mock_ghe):
        """
        Test the auth_to_github function when the GitHub Enterprise URL \
            is provided and the app was created in GitHub Enterprise URL.
        """
        mock = mock_ghe.return_value
        mock.login_as_app_installation = MagicMock(return_value=True)
        result = auth_to_github(
            "", 123, 456, b"123", "https://github.example.com", True
        )
        mock.login_as_app_installation.assert_called_once_with(b"123", "123", 456)
        self.assertEqual(result, mock)

    @patch("github3.apps.create_jwt_headers", MagicMock(return_value="gh_token"))
    @patch("requests.post")
    def test_get_github_app_installation_token(self, mock_post):
        """
        Test the get_github_app_installation_token function.
        """
        dummy_token = "dummytoken"
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"token": dummy_token}
        mock_post.return_value = mock_response
        mock_ghe = ""

        result = get_github_app_installation_token(
            mock_ghe, "gh_app_id", b"gh_private_token", "gh_installation_id"
        )

        self.assertEqual(result, dummy_token)

    @patch("github3.apps.create_jwt_headers", MagicMock(return_value="gh_token"))
    @patch("auth.requests.post")
    def test_get_github_app_installation_token_request_failure(self, mock_post):
        """
        Test the get_github_app_installation_token function returns None when the request fails.
        """
        # Mock the post request to raise a RequestException
        mock_post.side_effect = requests.exceptions.RequestException("Request failed")

        # Call the function with test data
        result = get_github_app_installation_token(
            ghe="https://api.github.com",
            gh_app_id=12345,
            gh_app_private_key_bytes=b"private_key",
            gh_app_installation_id=678910,
        )

        # Assert that the result is None
        self.assertIsNone(result)

    @patch("github3.login")
    def test_auth_to_github_invalid_credentials(self, mock_login):
        """
        Test the auth_to_github function raises correct ValueError
        when credentials are present but incorrect.
        """
        mock_login.return_value = None
        with self.assertRaises(ValueError) as context_manager:
            auth_to_github("not_a_valid_token", "", "", b"", "", False)

        the_exception = context_manager.exception
        self.assertEqual(
            str(the_exception),
            "Unable to authenticate to GitHub",
        )
