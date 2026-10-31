# Local usage without Docker

1. Make sure you have at least Python3.11 installed
1. Copy `.env-example` to `.env`
1. Fill out the `.env` file with a _token_ from a user that has access to the organization to scan (listed below). Tokens should have admin:org or read:org access.
1. Fill out the `.env` file with the _search_query_ to filter issues by
1. Install uv and dependencies using the [development setup instructions](../README.md#development-setup).
1. Run `uv run python ./issue_metrics.py`, which will output issue metrics data.
