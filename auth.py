"""This is the module that contains functions related to authenticating to GitHub with a personal access token."""

from github import Auth, Github, GithubException, GithubIntegration


def auth_to_github(
    token: str,
    gh_app_id: int | None,
    gh_app_installation_id: int | None,
    gh_app_private_key_bytes: bytes,
    ghe: str,
    gh_app_enterprise_only: bool,
) -> Github:
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
        Github: the GitHub connection object
    """
    if gh_app_id and gh_app_private_key_bytes and gh_app_installation_id:
        private_key_str = gh_app_private_key_bytes.decode("utf-8")
        app_auth = Auth.AppAuth(int(gh_app_id), private_key_str)
        installation_auth = app_auth.get_installation_auth(int(gh_app_installation_id))
        if ghe and gh_app_enterprise_only:
            github_connection = Github(base_url=f"{ghe}/api/v3", auth=installation_auth)
        else:
            github_connection = Github(auth=installation_auth)
    elif ghe and token:
        github_connection = Github(base_url=f"{ghe}/api/v3", auth=Auth.Token(token))
    elif token:
        github_connection = Github(auth=Auth.Token(token))
    else:
        raise ValueError("GH_TOKEN or the set of [GH_APP_ID, GH_APP_INSTALLATION_ID, \
                GH_APP_PRIVATE_KEY] environment variables are not set")

    return github_connection


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
        str | None: the GitHub App token, or None if IDs are missing or token fetch fails.
    """
    if gh_app_id is None or gh_app_installation_id is None:
        return None

    try:
        private_key_str = gh_app_private_key_bytes.decode("utf-8")
        app_auth = Auth.AppAuth(gh_app_id, private_key_str)
        if ghe:
            gi = GithubIntegration(auth=app_auth, base_url=f"{ghe}/api/v3")
        else:
            gi = GithubIntegration(auth=app_auth)
        installation_token = gi.get_access_token(gh_app_installation_id)
        return installation_token.token
    except (GithubException, ValueError, AttributeError) as e:
        print(f"Failed to get installation token: {e}")
        return None
