"""This is the module that contains functions related to authenticating to GitHub with a personal access token."""

import github3
import requests


def auth_to_github(
    token: str,
    gh_app_id: int | None,
    gh_app_installation_id: int | None,
    gh_app_private_key_bytes: bytes,
    ghe: str,
    gh_app_enterprise_only: bool,
) -> github3.GitHub:
    """
    Connect to GitHub.com or GitHub Enterprise, depending on env variables.

    Args:
        token (str): the GitHub personal access token
        gh_app_id (int | None): the GitHub App ID
        gh_app_installation_id (int | None): the GitHub App Installation ID
        gh_app_private_key_bytes (bytes): the GitHub App Private Key
        ghe (str): the GitHub Enterprise URL
        gh_app_enterprise_only (bool): Set this to true if the GH APP is created
                                       on GHE and needs to communicate with GHE api only

    Returns:
        github3.GitHub: the GitHub connection object
    """
    if gh_app_id and gh_app_private_key_bytes and gh_app_installation_id:
        if ghe and gh_app_enterprise_only:
            gh = github3.github.GitHubEnterprise(url=ghe)
        else:
            gh = github3.github.GitHub()
        gh.login_as_app_installation(
            gh_app_private_key_bytes, str(gh_app_id), gh_app_installation_id
        )
        github_connection = gh
    elif ghe and token:
        github_connection = github3.github.GitHubEnterprise(url=ghe, token=token)
    elif token:
        github_connection = github3.login(token=token)
    else:
        raise ValueError("GH_TOKEN or the set of [GH_APP_ID, GH_APP_INSTALLATION_ID, \
                GH_APP_PRIVATE_KEY] environment variables are not set")

    if not github_connection:
        raise ValueError("Unable to authenticate to GitHub")
    return github_connection  # type: ignore


def get_github_app_installation_token(
    ghe: str,
    gh_app_id: int | None,
    gh_app_private_key_bytes: bytes,
    gh_app_installation_id: int | None,
) -> str | None:
    """
    Get a GitHub App Installation token.
    API: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation # noqa: E501

    Args:
        ghe (str): the GitHub Enterprise endpoint
        gh_app_id (int | None): the GitHub App ID
        gh_app_private_key_bytes (bytes): the GitHub App Private Key
        gh_app_installation_id (int | None): the GitHub App Installation ID

    Returns:
        str: the GitHub App token
    """
    jwt_headers = github3.apps.create_jwt_headers(
        gh_app_private_key_bytes, str(gh_app_id)
    )
    api_endpoint = f"{ghe}/api/v3" if ghe else "https://api.github.com"
    url = f"{api_endpoint}/app/installations/{gh_app_installation_id}/access_tokens"

    try:
        response = requests.post(url, headers=jwt_headers, json=None, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    return response.json().get("token")
