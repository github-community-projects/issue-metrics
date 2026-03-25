# Issue Metrics Action

> [!IMPORTANT]
> This repository has been transferred from `github/issue-metrics` to `github-community-projects/issue-metrics`. Please update any references to the old repository location.

[![CodeQL](https://github.com/github-community-projects/issue-metrics/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/github-community-projects/issue-metrics/actions/workflows/github-code-scanning/codeql)
[![Docker Image CI](https://github.com/github-community-projects/issue-metrics/actions/workflows/docker-image.yml/badge.svg)](https://github.com/github-community-projects/issue-metrics/actions/workflows/docker-image.yml)
[![Python package](https://github.com/github-community-projects/issue-metrics/actions/workflows/python-package.yml/badge.svg)](https://github.com/github-community-projects/issue-metrics/actions/workflows/python-package.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/github-community-projects/issue-metrics/badge)](https://scorecard.dev/viewer/?uri=github.com/github-community-projects/issue-metrics)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/9501/badge)](https://www.bestpractices.dev/projects/9501)

This is a GitHub Action that searches for issues/pull requests/discussions in a repository, measures several metrics, and generates a report in form of a GitHub issue.
The issues/pull requests/discussions to search for can be filtered by using a search query.

This action, developed by GitHub OSPO for our internal use, is open-sourced for your potential benefit.
Feel free to inquire about its usage by creating an issue in this repository.

## Available Metrics

| Metric                            | Description                                                                                |
| --------------------------------- | ------------------------------------------------------------------------------------------ |
| Time to First Response            | The duration from creation to the initial comment or review.\*                             |
| Time to First Review (PRs Only)   | The duration from creation to the first submitted review.\*                                |
| Time to Close                     | The period from creation to closure.\*                                                     |
| Time to Answer (Discussions Only) | The time from creation to an answer.                                                       |
| Time in Label                     | The duration from label application to removal, requires `LABELS_TO_MEASURE` env variable. |
| Time in Draft (PRs Only)          | The duration from creation to the PR being marked as ready for review.                     |

\*For pull requests, these metrics exclude the time the PR was in draft mode.

\*For issues and pull requests, comments by issue/pull request author's and comments by bots are excluded.

To find syntax for search queries, check out the documentation on [searching issues and pull requests](https://docs.github.com/en/issues/tracking-your-work-with-issues/filtering-and-searching-issues-and-pull-requests)
or [searching discussions](https://docs.github.com/en/search-github/searching-on-github/searching-discussions).

## Sample Report

The output of this action is a report in form of a GitHub issue.
Below you see a sample of such a GitHub issue.

![Sample GitHub issue created by the issue/metrics GitHub Action](docs/img/issue-metrics-sample-output.png)

## Getting Started

Create a workflow file (ie. `.github/workflows/issue-metrics.yml`) in your repository with the following contents:

**Note**: `repo:owner/repo` is the repository you want to measure metrics on

```yaml
name: Monthly issue metrics
on:
  workflow_dispatch:
  schedule:
    - cron: "3 2 1 * *"

permissions:
  contents: read

jobs:
  build:
    name: issue metrics
    runs-on: ubuntu-latest
    permissions:
      issues: write
      pull-requests: read
    steps:
      - name: Get dates for last month
        shell: bash
        run: |
          # Calculate the first day of the previous month
          first_day=$(date -d "last month" +%Y-%m-01)

          # Calculate the last day of the previous month
          last_day=$(date -d "$first_day +1 month -1 day" +%Y-%m-%d)

          #Set an environment variable with the date range
          echo "$first_day..$last_day"
          echo "last_month=$first_day..$last_day" >> "$GITHUB_ENV"

      - name: Run issue-metrics tool
        uses: github-community-projects/issue-metrics@v4
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SEARCH_QUERY: 'repo:owner/repo is:issue created:${{ env.last_month }} -reason:"not planned"'

      - name: Create issue
        uses: peter-evans/create-issue-from-file@v5
        with:
          title: Monthly issue metrics report
          token: ${{ secrets.GITHUB_TOKEN }}
          content-filepath: ./issue_metrics.md
```

## Example use cases

- As a maintainer, I want to see metrics for issues and pull requests on the repository I maintain in order to ensure I am giving them the proper amount of attention.
- As a first responder on a repository, I want to ensure that users are getting contact from me in a reasonable amount of time.
- As an OSPO, I want to see how many open source repository requests are open/closed, and metrics for how long it takes to get through the open source process.
- As a product development team, I want to see metrics around how long pull request reviews are taking, so that we can reflect on that data during retrospectives.

## Support

If you need support using this project or have questions about it, please [open up an issue in this repository](https://github.com/github-community-projects/issue-metrics/issues). Requests made directly to GitHub staff or support team will be redirected here to open an issue. GitHub SLA's and support/services contracts do not apply to this repository.

### OSPO GitHub Actions as a Whole

All feedback regarding our GitHub Actions, as a whole, should be communicated through [issues on our github-ospo repository](https://github.com/github/github-ospo/issues/new).

## Use as a GitHub Action

1. Create a repository to host this GitHub Action or select an existing repository. This is easiest if it is the same repository as the one you want to measure metrics on.
1. Select a best fit workflow file from the [examples directory](./docs/example-workflows.md) for your use case.
1. Copy that example into your repository (from step 1) and into the proper directory for GitHub Actions: `.github/workflows/` directory with the file extension `.yml` (ie. `.github/workflows/issue-metrics.yml`)
1. Edit the values (`SEARCH_QUERY`, `assignees`) from the sample workflow with your information. See the [SEARCH_QUERY](./docs/search-query.md) section for more information on how to configure the search query.
1. If you are running metrics on a repository other than the one where the workflow file is going to be, then update the value of `GH_TOKEN`.
   - Do this by creating a [GitHub API token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic) with permissions to read the repository and write issues.
   - Then take the value of the API token you just created, and [create a repository secret](https://docs.github.com/en/actions/security-guides/encrypted-secrets) where the name of the secret is `GH_TOKEN` and the value of the secret the API token.
   - Then finally update the workflow file to use that repository secret by changing `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` to `GH_TOKEN: ${{ secrets.GH_TOKEN }}`. The name of the secret can really be anything. It just needs to match between when you create the secret name and when you refer to it in the workflow file.
   - Help on verifying your token's access to your repository [in the docs directory](docs/verify-token-access-to-repository.md)
1. If you want the resulting issue with the metrics in it to appear in a different repository other than the one the workflow file runs in, update the line `token: ${{ secrets.GITHUB_TOKEN }}` with your own GitHub API token stored as a repository secret.
   - This process is the same as described in the step above. More info on creating secrets can be found [in the GitHub docs security guide on encrypted secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets).
1. Commit the workflow file to the default branch (often `master` or `main`)
1. Wait for the action to trigger based on the `schedule` entry or manually trigger the workflow as shown in the [documentation](https://docs.github.com/en/actions/using-workflows/manually-running-a-workflow).

### Configuration

Below are the allowed configuration options:

#### Authentication

This action can be configured to authenticate with GitHub App Installation or Personal Access Token (PAT). If all configuration options are provided, the GitHub App Installation configuration has precedence. You can choose one of the following methods to authenticate:

##### GitHub App Installation

| field                        | required | default | description                                                                                                                                                                                             |
| ---------------------------- | -------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GH_APP_ID`                  | True     | `""`    | GitHub Application ID. See [documentation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/about-authentication-with-a-github-app) for more details.              |
| `GH_APP_INSTALLATION_ID`     | True     | `""`    | GitHub Application Installation ID. See [documentation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/about-authentication-with-a-github-app) for more details. |
| `GH_APP_PRIVATE_KEY`         | True     | `""`    | GitHub Application Private Key. See [documentation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/about-authentication-with-a-github-app) for more details.     |
| `GITHUB_APP_ENTERPRISE_ONLY` | False    | false   | Set this input to `true` if your app is created in GHE and communicates with GHE.                                                                                                                       |

##### Personal Access Token (PAT)

| field      | required | default | description                                                                                                           |
| ---------- | -------- | ------- | --------------------------------------------------------------------------------------------------------------------- |
| `GH_TOKEN` | True     | `""`    | The GitHub Token used to scan the repository. Must have read access to all repository you are interested in scanning. |

#### Other Configuration Options

| field                         | required | default                                    | description                                                                                                                                                                                                                                                                                                |
| ----------------------------- | -------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GH_ENTERPRISE_URL`           | False    | `""`                                       | URL of GitHub Enterprise instance to use for auth instead of github.com                                                                                                                                                                                                                                    |
| `RATE_LIMIT_BYPASS`           | False    | `false`                                    | If set to `true`, the rate limit will be bypassed. This is useful if being run on an local GitHub server with rate limiting disabled.                                                                                                                                                                      |
| `HIDE_ASSIGNEE`               | False    | False                                      | If set to `true`, the assignee will not be displayed in the generated Markdown file.                                                                                                                                                                                                                       |
| `HIDE_AUTHOR`                 | False    | False                                      | If set to `true`, the author will not be displayed in the generated Markdown file.                                                                                                                                                                                                                         |
| `HIDE_ITEMS_CLOSED_COUNT`     | False    | False                                      | If set to `true`, the number of items closed metric will not be displayed in the generated Markdown file.                                                                                                                                                                                                  |
| `HIDE_LABEL_METRICS`          | False    | False                                      | If set to `true`, the time in label metrics will not be displayed in the generated Markdown file.                                                                                                                                                                                                          |
| `HIDE_TIME_TO_ANSWER`         | False    | False                                      | If set to `true`, the time to answer a discussion will not be displayed in the generated Markdown file.                                                                                                                                                                                                    |
| `HIDE_TIME_TO_CLOSE`          | False    | False                                      | If set to `true`, the time to close will not be displayed in the generated Markdown file.                                                                                                                                                                                                                  |
| `HIDE_TIME_TO_FIRST_RESPONSE` | False    | False                                      | If set to `true`, the time to first response will not be displayed in the generated Markdown file.                                                                                                                                                                                                         |
<<<<<<< HEAD
| `HIDE_TIME_TO_FIRST_REVIEW`   | False    | False                                      | If set to `true`, the time to first review will not be displayed in the generated Markdown file.                                                                                                                                                                                                         |
=======
| `HIDE_TIME_TO_FIRST_REVIEW`   | False    | False                                      | If set to `true`, the time to first review will not be displayed in the generated Markdown file.                                                                                                                                                                                                           |
>>>>>>> 14965b3 (doc: README.md edited for time_to_first_review metric)
| `HIDE_STATUS`                 | False    | True                                       | If set to `true`, the status column will not be shown                                                                                                                                                                                                                                                      |
| `HIDE_CREATED_AT`             | False    | True                                       | If set to `true`, the creation timestamp will not be displayed in the generated Markdown file.                                                                                                                                                                                                             |
| `HIDE_PR_STATISTICS`          | False    | True                                       | If set to `true`, PR comment statistics (mean, median, 90th percentile, and individual PR comment counts) will not be displayed in the generated Markdown file.                                                                                                                                            |
| `HIDE_ITEMS_LIST`             | False    | False                                      | If set to `true`, the individual items list table of individual pull requests, issues, and discussions will not be displayed in the generated Markdown file. Only the summary metrics will be shown.                                                                                                       |
| `DRAFT_PR_TRACKING`           | False    | False                                      | If set to `true`, draft PRs will be included in the metrics as a new column and in the summary stats.                                                                                                                                                                                                      |
| `IGNORE_USERS`                | False    | False                                      | A comma separated list of users to ignore when calculating metrics. (ie. `IGNORE_USERS: 'user1,user2'`). To ignore bots, append `[bot]` to the user (ie. `IGNORE_USERS: 'github-actions[bot]'`) Users in this list will also have their authored issues and pull requests removed from the Markdown table. |
| `ENABLE_MENTOR_COUNT`         | False    | False                                      | If set to 'TRUE' count number of comments users left on discussions, issues and PRs and display number of active mentors                                                                                                                                                                                   |
| `MIN_MENTOR_COMMENTS`         | False    | 10                                         | Minimum number of comments to count as a mentor                                                                                                                                                                                                                                                            |
| `MAX_COMMENTS_EVAL`           | False    | 20                                         | Maximum number of comments per thread to evaluate for mentor stats                                                                                                                                                                                                                                         |
| `HEAVILY_INVOLVED_CUTOFF`     | False    | 3                                          | Cutoff after which a mentor's comments in one issue are no longer counted against their total score                                                                                                                                                                                                        |
| `LABELS_TO_MEASURE`           | False    | `""`                                       | A comma separated list of labels to measure how much time the label is applied. If not provided, no labels durations will be measured. Not compatible with discussions at this time.                                                                                                                       |
| `NON_MENTIONING_LINKS`        | False    | False                                      | If set to `true`, will use non-mentioning GitHub links to avoid linking to the generated issue from the source repository. Links of the form `https://www.github.com` will be used.                                                                                                                        |
| `OUTPUT_FILE`                 | False    | `issue_metrics.md` or `issue_metrics.json` | Output filename.                                                                                                                                                                                                                                                                                           |
| `REPORT_TITLE`                | False    | `"Issue Metrics"`                          | Title to have on the report issue.                                                                                                                                                                                                                                                                         |
| `SEARCH_QUERY`                | True     | `""`                                       | The query by which you can filter issues/PRs which must contain a `repo:`, `org:`, `owner:`, or a `user:` entry. For discussions, include `type:discussions` in the query.                                                                                                                                 |
| `GROUP_BY`                    | False    | `""`                                       | Group items in the report by the specified field. Supported values: `author`, `assignee`. When set, items will be grouped into separate sections by the chosen field.                                                                                                                                      |
<<<<<<< HEAD
| `SORT_BY`                     | False    | `""`                                       | Sort items in the report by the specified field. Supported values: `time_to_close`, `time_to_first_response`, `time_to_first_review`, `time_to_answer`, `time_in_draft`, `created_at`. When set, items will be sorted by the chosen metric. |
=======
| `SORT_BY`                     | False    | `""`                                       | Sort items in the report by the specified field. Supported values: `time_to_close`, `time_to_first_response`, `time_to_first_review`, `time_to_answer`, `time_in_draft`, `created_at`. When set, items will be sorted by the chosen metric.                                                                |
>>>>>>> 14965b3 (doc: README.md edited for time_to_first_review metric)
| `SORT_ORDER`                  | False    | `asc`                                      | Sort order for the items. Supported values: `asc` (ascending), `desc` (descending). Only applies when `SORT_BY` is set.                                                                                                                                                                                    |

## Further Documentation

- [Example workflows](./docs/example-workflows.md)
- [Measuring time spent in labels](./docs/measure-time.md)
- [Assigning teams instead of individuals](./docs/assign-team-instead-of-individual.md)
- [Example using the JSON output instead of the Markdown output](./docs/example-using-json-instead-markdown-output.md)
- [Configuring the `SEARCH_QUERY`](./docs/search-query.md)
- [Local usage without Docker](./docs/local-usage-without-docker.md)
- [Authenticating with GitHub App Installation](./docs/authenticating-with-github-app-installation.md)
- [Dealing with large issue_metrics.md files](./docs/dealing-with-large-issue-metrics.md)

## Contributions

We would ❤️ contributions to improve this action. Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for how to get involved.

### Development Setup

- Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Clone this repository and cd into `issue-metrics`
- Install dependencies
  `uv sync`
- Run tests
  `make test`
- Run linter
  `make lint`

## License

[MIT](LICENSE)

## More OSPO Tools

Looking for more resources for your open source program office (OSPO)? Check out the [`github-ospo`](https://github.com/github/github-ospo) repository for a variety of tools designed to support your needs.