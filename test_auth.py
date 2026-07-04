"""A module containing unit tests for the auth module.

This module contains unit tests for the functions in the auth module
that authenticate to github.

Classes:
    TestAuthToGithub: A class to test the auth_to_github function.

"""

import unittest
from unittest.mock import MagicMock, patch

from auth import auth_to_github, get_github_app_installation_token
from github import Github


class TestAuthToGithub(unittest.TestCase):
    """Test the auth_to_github function."""

    @patch("auth.Auth")
    @patch("auth.Github")
    def test_auth_to_github_with_github_app(self, mock_github_cls, mock_auth):
        """
        Test the auth_to_github function when GitHub app
        parameters provided.
        """
        mock_app_auth = MagicMock()
        mock_auth.AppAuth.return_value = mock_app_auth
        mock_installation_auth = MagicMock()
        mock_app_auth.get_installation_auth.return_value = mock_installation_auth
        mock_github_instance = MagicMock()
        mock_github_cls.return_value = mock_github_instance

        result = auth_to_github("", 12345, 678910, b"hello", "", False)

        mock_auth.AppAuth.assert_called_once_with(12345, "hello")
        mock_app_auth.get_installation_auth.assert_called_once_with(678910)
        mock_github_cls.assert_called_once_with(auth=mock_installation_auth)
        self.assertEqual(result, mock_github_instance)

    def test_auth_to_github_with_token(self):
        """
        Test the auth_to_github function when the token is provided.
        """
        result = auth_to_github("token", None, None, b"", "", False)

        self.assertIsInstance(result, Github)

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

        self.assertIsInstance(result, Github)

    @patch("auth.Auth")
    @patch("auth.Github")
    def test_auth_to_github_with_ghe_and_ghe_app(self, mock_github_cls, mock_auth):
        """
        Test the auth_to_github function when the GitHub Enterprise URL \
            is provided and the app was created in GitHub Enterprise URL.
        """
        mock_app_auth = MagicMock()
        mock_auth.AppAuth.return_value = mock_app_auth
        mock_installation_auth = MagicMock()
        mock_app_auth.get_installation_auth.return_value = mock_installation_auth
        mock_github_instance = MagicMock()
        mock_github_cls.return_value = mock_github_instance

        result = auth_to_github(
            "", 123, 456, b"123", "https://github.example.com", True
        )
        mock_auth.AppAuth.assert_called_once_with(123, "123")
        mock_app_auth.get_installation_auth.assert_called_once_with(456)
        mock_github_cls.assert_called_once_with(
            base_url="https://github.example.com/api/v3",
            auth=mock_installation_auth,
        )
        self.assertEqual(result, mock_github_instance)

    @patch("auth.GithubIntegration")
    @patch("auth.Auth")
    def test_get_github_app_installation_token(self, mock_auth, mock_gi_cls):
        """
        Test the get_github_app_installation_token function.
        """
        dummy_token = "dummytoken"
        mock_app_auth = MagicMock()
        mock_auth.AppAuth.return_value = mock_app_auth
        mock_gi = MagicMock()
        mock_gi_cls.return_value = mock_gi
        mock_access_token = MagicMock()
        mock_access_token.token = dummy_token
        mock_gi.get_access_token.return_value = mock_access_token

        result = get_github_app_installation_token(
            "", 12345, b"gh_private_token", 678910
        )

        self.assertEqual(result, dummy_token)

    @patch("auth.GithubIntegration")
    @patch("auth.Auth")
    def test_get_github_app_installation_token_with_ghe(self, mock_auth, mock_gi_cls):
        """
        Test the get_github_app_installation_token function with a GHE URL.
        """
        dummy_token = "dummytoken"
        mock_app_auth = MagicMock()
        mock_auth.AppAuth.return_value = mock_app_auth
        mock_gi = MagicMock()
        mock_gi_cls.return_value = mock_gi
        mock_access_token = MagicMock()
        mock_access_token.token = dummy_token
        mock_gi.get_access_token.return_value = mock_access_token

        result = get_github_app_installation_token(
            "https://github.example.com", 12345, b"gh_private_token", 678910
        )

        mock_gi_cls.assert_called_once_with(
            auth=mock_app_auth, base_url="https://github.example.com/api/v3"
        )
        self.assertEqual(result, dummy_token)

    def test_get_github_app_installation_token_returns_none_for_missing_ids(self):
        """
        Test that get_github_app_installation_token returns None when app IDs are None.
        """
        result = get_github_app_installation_token("", None, b"private_key", 678910)
        self.assertIsNone(result)

        result = get_github_app_installation_token("", 12345, b"private_key", None)
        self.assertIsNone(result)

    @patch("auth.Auth")
    def test_get_github_app_installation_token_request_failure(self, mock_auth):
        """
        Test the get_github_app_installation_token function returns None when the request fails.
        """
        mock_auth.AppAuth.side_effect = ValueError("Auth failed")

        result = get_github_app_installation_token(
            ghe="https://api.github.com",
            gh_app_id=12345,
            gh_app_private_key_bytes=b"private_key",
            gh_app_installation_id=678910,
        )

        self.assertIsNone(result)

    @patch("auth.Github")
    @patch("auth.Auth")
    def test_auth_to_github_invalid_credentials(self, mock_auth, mock_github_cls):
        """
        Test the auth_to_github function raises correct ValueError
        when credentials are present but incorrect.
        """
        mock_token = MagicMock()
        mock_auth.Token.return_value = mock_token
        mock_github_cls.return_value = None
        with self.assertRaises(ValueError) as context_manager:
            auth_to_github("not_a_valid_token", "", "", b"", "", False)

        the_exception = context_manager.exception
        self.assertEqual(
            str(the_exception),
            "Unable to authenticate to GitHub",
        )
