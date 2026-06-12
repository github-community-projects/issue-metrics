"""Additional unit tests to raise coverage to 100%.

This module bundles together targeted unit tests that exercise branches
not covered by the per-module test files. Each test is named to indicate
the file and line it covers so future maintainers can trace coverage.

All GitHub API calls are mocked via unittest.mock; no network access
is performed.
"""

import os
import runpy
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, PropertyMock, patch

import github3
import pytz
import requests
from classes import IssueWithMetrics
from config import get_env_vars
from issue_metrics import get_per_issue_metrics
from json_writer import write_to_json
from labels import get_label_metrics, get_stats_time_in_labels
from markdown_writer import get_non_hidden_columns, write_to_markdown
from most_active_mentors import count_comments_per_user
from pr_comments import count_pr_comments
from search import (
    get_owners_and_repositories,
    print_error_messages,
    search_issues,
)
from time_to_close import measure_time_to_close
from time_to_first_response import measure_time_to_first_response
from time_to_first_review import measure_time_to_first_review
from time_to_ready_for_review import get_time_to_ready_for_review


# ---------------------------------------------------------------------------
# config.py
# ---------------------------------------------------------------------------
class TestConfigSortOrderFallback(unittest.TestCase):
    """Covers config.py:266 — SORT_ORDER fallback when value is invalid."""

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:issue repo:user/repo",
            "SORT_ORDER": "sideways",
        },
    )
    def test_invalid_sort_order_defaults_to_asc(self):
        """An unrecognized SORT_ORDER value is normalized to 'asc'."""

        env_vars = get_env_vars(test=True)
        self.assertEqual(env_vars.sort_order, "asc")


# ---------------------------------------------------------------------------
# labels.py
# ---------------------------------------------------------------------------
class TestLabelsCoverageGaps(unittest.TestCase):
    """Covers labels.py:55, 78, 97, 117, 121."""

    def test_get_label_metrics_returns_early_when_no_events(self):
        """labels.py:55 — early return when there are no label events."""

        issue = MagicMock()
        issue.issue = MagicMock(spec=github3.issues.Issue)
        issue.created_at = "2021-01-01T00:00:00Z"
        issue.closed_at = "2021-01-05T00:00:00Z"
        issue.state = "closed"
        issue.issue.events.return_value = []

        result = get_label_metrics(issue, ["bug"])
        self.assertEqual(result, {"bug": None})

    def test_get_label_metrics_unlabeled_first_initializes_zero(self):
        """labels.py:78 — 'unlabeled' event with no prior 'labeled' init."""

        issue = MagicMock()
        issue.issue = MagicMock(spec=github3.issues.Issue)
        issue.created_at = "2021-01-01T00:00:00Z"
        issue.closed_at = "2021-01-05T00:00:00Z"
        issue.state = "closed"
        issue.issue.events.return_value = [
            MagicMock(
                event="unlabeled",
                label={"name": "bug"},
                created_at=datetime(2021, 1, 2, tzinfo=pytz.UTC),
            ),
        ]

        result = get_label_metrics(issue, ["bug"])
        # The unlabeled-only path produces a positive delta (since label was
        # never explicitly applied, the bookkeeping treats the gap as time
        # spent unlabeled). The key assertion is that no KeyError was raised
        # and the value was initialized from None to a timedelta.
        self.assertIsInstance(result["bug"], timedelta)

    def test_get_label_metrics_open_issue_last_event_unlabeled_skips(self):
        """labels.py:97 — open issue whose last event is 'unlabeled' is skipped."""

        issue = MagicMock()
        issue.issue = MagicMock(spec=github3.issues.Issue)
        issue.created_at = "2021-01-01T00:00:00Z"
        issue.closed_at = None
        issue.state = "open"
        issue.issue.events.return_value = [
            MagicMock(
                event="labeled",
                label={"name": "bug"},
                created_at=datetime(2021, 1, 1, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="unlabeled",
                label={"name": "bug"},
                created_at=datetime(2021, 1, 3, tzinfo=pytz.UTC),
            ),
        ]

        result = get_label_metrics(issue, ["bug"])
        # The last event was 'unlabeled' on an open issue, so the final
        # open-issue 'now - created' span must not be added.
        # That leaves only the labeled/unlabeled delta:
        # labeled at +0d (subtracts 0), unlabeled at +2d (adds 2d) → 2 days.
        self.assertEqual(result["bug"], timedelta(days=2))

    def test_get_stats_time_in_labels_skips_none_and_appends(self):
        """labels.py:117, 121 — None label_metrics is skipped; second hit appends."""

        issue1 = IssueWithMetrics(
            "I1",
            "https://example/1",
            "alice",
            labels_metrics={"bug": None, "feature": timedelta(seconds=10)},
        )
        issue2 = IssueWithMetrics(
            "I2",
            "https://example/2",
            "bob",
            labels_metrics={"feature": timedelta(seconds=20)},
        )

        labels: dict[str, timedelta] = {
            "bug": timedelta(0),
            "feature": timedelta(0),
        }
        stats = get_stats_time_in_labels([issue1, issue2], labels)
        # 'bug' had only a None entry, so it gets filled in as None at the end.
        self.assertIsNone(stats["avg"]["bug"])
        # 'feature' appears in two issues and is averaged.
        self.assertEqual(stats["avg"]["feature"], timedelta(seconds=15))


# ---------------------------------------------------------------------------
# pr_comments.py
# ---------------------------------------------------------------------------
class TestPRCommentsIgnoreUsersDefault(unittest.TestCase):
    """Covers pr_comments.py:46 — ignore_users defaults to []."""

    def test_count_pr_comments_with_default_ignore_users(self):
        """Default ignore_users falls back to an empty list."""

        mock_comment = MagicMock()
        mock_comment.user.type = "User"
        mock_comment.user.login = "alice"

        mock_issue = MagicMock()
        mock_issue.issue.comments.return_value = [mock_comment]

        mock_pr = MagicMock()
        mock_pr.review_comments.return_value = []

        result = count_pr_comments(mock_issue, mock_pr)
        self.assertEqual(result, 1)


# ---------------------------------------------------------------------------
# time_to_close.py
# ---------------------------------------------------------------------------
class TestTimeToCloseEdgeCases(unittest.TestCase):
    """Covers time_to_close.py:49, 55."""

    def test_discussion_with_no_closed_at_returns_none(self):
        """time_to_close.py:49."""

        discussion = {"closedAt": None, "createdAt": "2021-01-01T00:00:00Z"}
        self.assertIsNone(measure_time_to_close(None, discussion))

    def test_neither_issue_nor_discussion_returns_none(self):
        """time_to_close.py:55."""

        self.assertIsNone(measure_time_to_close(None, None))


# ---------------------------------------------------------------------------
# time_to_first_response.py
# ---------------------------------------------------------------------------
class TestTimeToFirstResponseEdgeCases(unittest.TestCase):
    """Covers time_to_first_response.py:88-89, 121."""

    def test_pull_request_reviews_raises_type_error(self):
        """time_to_first_response.py:88-89 — TypeError in reviews is caught."""

        mock_issue = MagicMock()
        mock_issue.created_at = "2023-01-01T00:00:00Z"
        mock_issue.issue.user.login = "owner"
        mock_issue.issue.comments.return_value = []

        # The source wraps the `for` loop (not the .reviews() call) in
        # try/except TypeError, so we make iteration itself fail.
        class _RaisingIterator:
            def __iter__(self):
                raise TypeError("ghost user")

        mock_pr = MagicMock()
        mock_pr.reviews.return_value = _RaisingIterator()

        # No issue comments and no review comments → earliest_response is None
        # → function returns None before computing a delta.
        result = measure_time_to_first_response(mock_issue, None, mock_pr)
        self.assertIsNone(result)

    def test_returns_none_when_no_issue_and_no_discussion(self):
        """time_to_first_response.py:121 — final return None fallback."""

        self.assertIsNone(measure_time_to_first_response(None, None))


# ---------------------------------------------------------------------------
# time_to_first_review.py
# ---------------------------------------------------------------------------
class TestTimeToFirstReviewEdgeCases(unittest.TestCase):
    """Covers time_to_first_review.py:21, 24."""

    def test_returns_none_when_issue_or_pr_missing(self):
        """time_to_first_review.py:21."""

        self.assertIsNone(measure_time_to_first_review(None, MagicMock()))
        self.assertIsNone(measure_time_to_first_review(MagicMock(), None))

    def test_ignore_users_defaults_to_empty_list(self):
        """time_to_first_review.py:24 — ignore_users default."""

        mock_issue = MagicMock()
        mock_issue.created_at = "2023-01-01T00:00:00Z"

        mock_review = MagicMock()
        mock_review.submitted_at = datetime.fromisoformat("2023-01-02T00:00:00Z")

        mock_pr = MagicMock()
        mock_pr.reviews.return_value = [mock_review]

        # Omit ignore_users to exercise the default-None branch.
        result = measure_time_to_first_review(mock_issue, mock_pr)
        self.assertEqual(result, timedelta(days=1))


# ---------------------------------------------------------------------------
# time_to_ready_for_review.py
# ---------------------------------------------------------------------------
class TestTimeToReadyForReviewTypeError(unittest.TestCase):
    """Covers time_to_ready_for_review.py:45-49 — ghost user TypeError path."""

    def test_events_raises_type_error_returns_none(self):
        """A TypeError from pull_request.events() short-circuits to None."""

        pull_request = MagicMock()
        pull_request.draft = False

        bad_event = MagicMock()
        # Accessing .event on this MagicMock raises TypeError to simulate
        # a ghost user reference deep in the github3 response.
        type(bad_event).event = property(
            lambda _self: (_ for _ in ()).throw(TypeError("ghost user"))
        )

        issue = MagicMock()
        issue.issue.events.return_value = [bad_event]

        result = get_time_to_ready_for_review(issue, pull_request)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# search.py
# ---------------------------------------------------------------------------
class TestSearchCoverageGaps(unittest.TestCase):
    """Covers search.py rate-limit, exception, and parser branches."""

    def _build_iterator(self, issues, ratelimit_remaining):
        iterator = MagicMock()
        iterator.__iter__.return_value = iter(issues)
        iterator.ratelimit_remaining = ratelimit_remaining
        return iterator

    @patch("search.sleep", return_value=None)
    def test_wait_for_api_refresh_retries_then_succeeds(self, mock_sleep):
        """search.py:45-56 (loop body) — low rate limit sleeps then continues."""
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
        """search.py:46-47 — RuntimeError after max retries."""

        iterator = MagicMock()
        iterator.ratelimit_remaining = 0  # always too low
        iterator.__iter__.return_value = iter([])

        connection = MagicMock()
        connection.search_issues.return_value = iterator

        with self.assertRaises(RuntimeError):
            search_issues("is:open", connection, [])

    def test_periodic_refresh_after_full_page(self):
        """search.py:81 — refresh is invoked after each full page of results."""

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
        """search.py:83-87."""
        resp = MagicMock(status_code=403)
        resp.json.return_value = {"message": "forbidden"}
        self._assert_exception_exits(github3.exceptions.ForbiddenError(resp))

    def test_not_found_error_exits(self):
        """search.py:88-92."""
        resp = MagicMock(status_code=404)
        resp.json.return_value = {"message": "not found"}
        self._assert_exception_exits(github3.exceptions.NotFoundError(resp))

    def test_connection_error_exits(self):
        """search.py:93-98."""
        # github3.exceptions.ConnectionError wraps a requests ConnectionError.

        self._assert_exception_exits(
            github3.exceptions.ConnectionError(requests.ConnectionError("boom"))
        )

    def test_authentication_failed_exits(self):
        """search.py:99-102."""
        resp = MagicMock(status_code=401)
        resp.json.return_value = {"message": "auth failed"}
        self._assert_exception_exits(github3.exceptions.AuthenticationFailed(resp))

    def test_unprocessable_entity_exits(self):
        """search.py:103-106."""
        resp = MagicMock(status_code=422)
        resp.json.return_value = {
            "message": "Validation Failed",
            "errors": [{"message": "bad query"}],
        }
        self._assert_exception_exits(github3.exceptions.UnprocessableEntity(resp))

    def test_print_error_messages_with_errors_attr(self):
        """search.py:118-120 — iterate over .errors when present."""

        error = MagicMock()
        error.errors = [{"message": "bad query"}, {"message": "another"}]
        # Should not raise.
        print_error_messages(error)

    def test_get_owners_and_repositories_handles_user_prefix(self):
        """search.py:144-145 — user: prefix sets the owner."""

        result = get_owners_and_repositories("user:octocat")
        self.assertEqual(result[0]["owner"], "octocat")

    def test_get_owners_and_repositories_handles_owner_prefix(self):
        """search.py:146-147 — owner: prefix sets the owner."""

        result = get_owners_and_repositories("owner:octocat")
        self.assertEqual(result[0]["owner"], "octocat")


# ---------------------------------------------------------------------------
# most_active_mentors.py
# ---------------------------------------------------------------------------
class TestMostActiveMentorsExtraBranches(unittest.TestCase):
    """Covers most_active_mentors.py review-comments and discussion branches."""

    def _make_issue(self, owner_login="issue_owner"):
        mock_issue = MagicMock()
        mock_issue.issue.user.login = owner_login
        mock_issue.issue.comments.return_value = []
        return mock_issue

    def test_count_comments_per_user_with_pr_reviews(self):
        """most_active_mentors.py:97-113 — review_comments path."""

        mock_issue = self._make_issue()

        # Two reviews from the same human reviewer.
        review_a = MagicMock()
        review_a.user.login = "reviewer"
        review_a.user.type = "User"
        review_a.submitted_at = datetime.fromisoformat("2023-01-02T00:00:00Z")

        review_b = MagicMock()
        review_b.user.login = "reviewer"
        review_b.user.type = "User"
        review_b.submitted_at = datetime.fromisoformat("2023-01-03T00:00:00Z")

        # One review from a bot (must be ignored by ignore_comment).
        bot_review = MagicMock()
        bot_review.user.login = "dependabot"
        bot_review.user.type = "Bot"
        bot_review.submitted_at = datetime.fromisoformat("2023-01-04T00:00:00Z")

        mock_pr = MagicMock()
        mock_pr.reviews.return_value = [review_a, review_b, bot_review]

        result = count_comments_per_user(mock_issue, pull_request=mock_pr)
        self.assertEqual(result, {"reviewer": 2})


# ---------------------------------------------------------------------------
# json_writer.py
# ---------------------------------------------------------------------------
class TestJsonWriterExtraBranches(unittest.TestCase):
    """Covers json_writer.py:98, 114-116, 162-164, 230-231."""

    def test_returns_empty_string_when_no_issues(self):
        """json_writer.py:98."""

        result = write_to_json(
            issues_with_metrics=None,
            stats_time_to_first_response=None,
            stats_time_to_first_review=None,
            stats_time_to_close=None,
            stats_time_to_answer=None,
            stats_time_in_draft=None,
            stats_time_in_labels=None,
            stats_pr_comments=None,
            num_issues_opened=0,
            num_issues_closed=0,
            num_mentor_count=0,
            search_query="is:issue repo:user/repo",
            output_file="",
        )
        self.assertEqual(result, "")

    def test_includes_time_to_first_review_and_pr_comments(self):
        """json_writer.py:114-116 (review stats) and 162-164 (pr comments)."""

        issue = IssueWithMetrics(
            title="PR 1",
            html_url="https://github.com/owner/repo/pull/1",
            author="alice",
            assignee=None,
            assignees=[],
            pr_comment_count=3,
        )
        # time_to_first_review is not a constructor arg; set it directly.
        issue.time_to_first_review = timedelta(hours=4)
        issues = [issue]

        stats_review = {
            "avg": timedelta(hours=4),
            "med": timedelta(hours=4),
            "90p": timedelta(hours=4),
        }
        stats_pr_comments = {"avg": 3.0, "med": 3.0, "90p": 3.0}

        out = write_to_json(
            issues_with_metrics=issues,
            stats_time_to_first_response=None,
            stats_time_to_first_review=stats_review,
            stats_time_to_close=None,
            stats_time_to_answer=None,
            stats_time_in_draft=None,
            stats_time_in_labels=None,
            stats_pr_comments=stats_pr_comments,
            num_issues_opened=1,
            num_issues_closed=0,
            num_mentor_count=0,
            search_query="is:pr repo:owner/repo",
            output_file="coverage_test.json",
        )

        self.assertIn("4:00:00", out)
        self.assertIn('"average_pr_comments": 3.0', out)

        # Clean up the file the writer created so the test leaves no artifacts.
        try:
            os.remove("coverage_test.json")
        except OSError:
            pass

    def test_writes_github_output_when_env_var_present(self):
        """json_writer.py:230-231 — GITHUB_OUTPUT branch."""

        github_output_path = "coverage_github_output.txt"
        try:
            with patch.dict(os.environ, {"GITHUB_OUTPUT": github_output_path}):
                write_to_json(
                    issues_with_metrics=[
                        IssueWithMetrics(
                            title="I1",
                            html_url="https://x/1",
                            author="a",
                            assignee=None,
                            assignees=[],
                        )
                    ],
                    stats_time_to_first_response=None,
                    stats_time_to_first_review=None,
                    stats_time_to_close=None,
                    stats_time_to_answer=None,
                    stats_time_in_draft=None,
                    stats_time_in_labels=None,
                    stats_pr_comments=None,
                    num_issues_opened=1,
                    num_issues_closed=0,
                    num_mentor_count=0,
                    search_query="is:issue repo:user/repo",
                    output_file="coverage_test_gh.json",
                )

            with open(github_output_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("metrics=", content)
        finally:
            for path in (github_output_path, "coverage_test_gh.json"):
                try:
                    os.remove(path)
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# markdown_writer.py
# ---------------------------------------------------------------------------
class TestMarkdownWriterExtraBranches(unittest.TestCase):
    """Covers markdown_writer.py:111, 270, 372, 433, 470, 486."""

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:pr repo:owner/repo",
            "HIDE_PR_STATISTICS": "false",
            "HIDE_STATUS": "true",
            "HIDE_CREATED_AT": "true",
        },
    )
    def test_pr_comments_column_present_when_not_hidden(self):
        """markdown_writer.py:111 — 'PR Comments' column included."""

        columns = get_non_hidden_columns(labels=None)
        self.assertIn("PR Comments", columns)

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:issue repo:user/repo",
        },
    )
    def test_no_issues_writes_search_query_line(self):
        """markdown_writer.py:270 — search_query is written when no issues."""

        output = "coverage_md_no_issues.md"
        try:
            write_to_markdown(
                issues_with_metrics=None,
                average_time_to_first_response=None,
                average_time_to_first_review=None,
                average_time_to_close=None,
                average_time_to_answer=None,
                average_time_in_draft=None,
                average_time_in_labels=None,
                stats_pr_comments=None,
                num_issues_opened=None,
                num_issues_closed=None,
                num_mentor_count=None,
                search_query="is:issue repo:user/repo",
                output_file=output,
            )
            with open(output, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Search query used to find these items", content)
        finally:
            try:
                os.remove(output)
            except OSError:
                pass

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:pr repo:owner/repo",
            "HIDE_ITEMS_LIST": "false",
            "HIDE_PR_STATISTICS": "false",
            "HIDE_STATUS": "true",
            "HIDE_CREATED_AT": "true",
            "HIDE_TIME_TO_FIRST_RESPONSE": "true",
            "HIDE_TIME_TO_FIRST_REVIEW": "false",
            "HIDE_TIME_TO_CLOSE": "true",
            "HIDE_TIME_TO_ANSWER": "true",
            "HIDE_AUTHOR": "false",
            "HIDE_ASSIGNEE": "true",
            "HIDE_LABEL_METRICS": "true",
            "DRAFT_PR_TRACKING": "true",
        },
    )
    def test_individual_row_includes_pr_comments_and_review_columns(self):
        """markdown_writer.py:372 ('PR Comments' row cell), 433 (Time to first review row)."""

        issue = IssueWithMetrics(
            title="PR 1",
            html_url="https://github.com/owner/repo/pull/1",
            author="alice",
            assignee=None,
            assignees=[],
            pr_comment_count=5,
            time_in_draft=timedelta(hours=2),
        )
        issue.time_to_first_review = timedelta(hours=4)
        issues = [issue]

        stats_review = {
            "avg": timedelta(hours=4),
            "med": timedelta(hours=4),
            "90p": timedelta(hours=4),
        }
        stats_pr_comments = {"avg": 5.0, "med": 5.0, "90p": 5.0}

        output = "coverage_md_row.md"
        try:
            write_to_markdown(
                issues_with_metrics=issues,
                average_time_to_first_response=None,
                average_time_to_first_review=stats_review,
                average_time_to_close=None,
                average_time_to_answer=None,
                average_time_in_draft=None,  # ← drives line 470 (None branch).
                average_time_in_labels=None,
                stats_pr_comments=stats_pr_comments,
                num_issues_opened=1,
                num_issues_closed=0,
                num_mentor_count=0,
                search_query="is:pr repo:owner/repo",
                output_file=output,
            )
            with open(output, "r", encoding="utf-8") as f:
                content = f.read()
            # PR Comments cell rendered (line 372).
            self.assertIn("| 5 |", content)
            # Time to first review row written (line 433).
            self.assertIn("Time to first review", content)
            # Time in draft None branch (line 470).
            self.assertIn("Time in draft | None | None | None", content)
            # PR comments overall row (line 486).
            self.assertIn("Number of comments per PR", content)
        finally:
            try:
                os.remove(output)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# issue_metrics.py
# ---------------------------------------------------------------------------
def _make_pr_search_result(
    *,
    title="PR 1",
    url="https://github.com/owner/repo/pull/1",
    login="alice",
    state="open",
    created_at="2023-01-01T00:00:00Z",
    closed_at=None,
    state_reason="completed",
    is_pull_request=True,
    pull_request=None,
):
    """Build a MagicMock that matches github3.search.IssueSearchResult shape.

    Setting __class__ on the mock makes isinstance(mock,
    github3.search.IssueSearchResult) return True, which is required for the
    created_at extraction branch in issue_metrics.py to take the
    IssueSearchResult path. We avoid spec= because IssueSearchResult does not
    expose .issue as a class-level attribute.
    """
    mock = MagicMock()
    mock.__class__ = github3.search.IssueSearchResult  # type: ignore
    mock.title = title
    mock.html_url = url
    mock.user = {"login": login}
    mock.state = state
    mock.created_at = created_at
    mock.closed_at = closed_at

    mock.issue.as_dict.return_value = {
        "assignee": {"login": login},
        "assignees": [{"login": login}],
    }
    mock.issue.state = state
    mock.issue.state_reason = state_reason
    mock.issue.created_at = datetime.fromisoformat(created_at)
    mock.issue.pull_request_urls = (
        ["https://api.github.com/repos/owner/repo/pulls/1"] if is_pull_request else None
    )
    mock.issue.pull_request.return_value = pull_request
    return mock


class TestIssueMetricsExtraBranches(unittest.TestCase):
    """Covers issue_metrics.py:101, 119, 149-153, 163, 167, 180, 190, 195, 203, 207, 210."""

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:issue repo:user/repo",
            "ENABLE_MENTOR_COUNT": "true",
        },
    )
    def test_discussion_open_and_enable_mentor_count(self):
        """issue_metrics.py:101 (mentor in discussion) and 119 (open discussion)."""

        # Open discussion (closedAt None) plus enabled mentor counting.
        discussion = {
            "title": "D1",
            "url": "https://example.com/d/1",
            "createdAt": "2023-01-01T00:00:00Z",
            "comments": {"nodes": [{"createdAt": "2023-01-02T00:00:00Z"}]},
            "answerChosenAt": None,
            "closedAt": None,
        }

        with patch("issue_metrics.count_comments_per_user", return_value={"u": 1}):
            metrics, num_open, num_closed = get_per_issue_metrics(
                [discussion],
                discussions=True,
                env_vars=get_env_vars(test=True),
            )
        self.assertEqual(num_open, 1)
        self.assertEqual(num_closed, 0)
        self.assertEqual(metrics[0].mentor_activity, {"u": 1})

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:pr repo:owner/repo",
            "DRAFT_PR_TRACKING": "true",
            "HIDE_PR_STATISTICS": "false",
            "ENABLE_MENTOR_COUNT": "true",
            "HIDE_LABEL_METRICS": "false",
            "HIDE_TIME_TO_FIRST_REVIEW": "false",
            "HIDE_STATUS": "false",
            "HIDE_CREATED_AT": "false",
            "LABELS_TO_MEASURE": "bug",
        },
    )
    def test_pull_request_branches_with_status_and_created_at(self):
        """Cover the PR branches for time_in_draft, count_pr_comments,
        time_to_first_review, count_comments_per_user, get_label_metrics,
        measure_time_to_merge, status (open and closed), and created_at.
        """

        mock_pr_obj = MagicMock()

        # Closed PR — exercises 195 (measure_time_to_merge), 203 (closed status).
        closed_pr = _make_pr_search_result(
            title="Closed PR",
            url="https://github.com/owner/repo/pull/2",
            state="closed",
            closed_at="2023-01-05T00:00:00Z",
            state_reason="completed",
            pull_request=mock_pr_obj,
        )
        # Open PR — exercises 207 (open status).
        open_pr = _make_pr_search_result(
            title="Open PR",
            url="https://github.com/owner/repo/pull/3",
            state="open",
            pull_request=mock_pr_obj,
        )

        with (
            patch("issue_metrics.get_time_to_ready_for_review", return_value=None),
            patch(
                "issue_metrics.measure_time_in_draft",
                return_value=timedelta(hours=2),
            ),
            patch("issue_metrics.count_pr_comments", return_value=4),
            patch(
                "issue_metrics.measure_time_to_first_review",
                return_value=timedelta(hours=1),
            ),
            patch(
                "issue_metrics.measure_time_to_first_response",
                return_value=timedelta(hours=3),
            ),
            patch(
                "issue_metrics.count_comments_per_user",
                return_value={"reviewer": 2},
            ),
            patch(
                "issue_metrics.get_label_metrics",
                return_value={"bug": timedelta(days=1)},
            ),
            patch(
                "issue_metrics.measure_time_to_merge",
                return_value=timedelta(days=4),
            ),
        ):
            env_vars = get_env_vars(test=True)
            metrics, num_open, num_closed = get_per_issue_metrics(
                [closed_pr, open_pr],
                env_vars=env_vars,
                labels=env_vars.labels_to_measure,
                ignore_users=[],
            )

        self.assertEqual(num_open, 1)
        self.assertEqual(num_closed, 1)
        # Closed PR uses measure_time_to_merge (line 195).
        self.assertEqual(metrics[0].time_to_close, timedelta(days=4))
        # Closed status uses the "as state_reason" form (line 203).
        self.assertIn("as", metrics[0].status)
        # Open status uses just the state value (line 207).
        self.assertEqual(metrics[1].status, "open")
        # created_at is populated from issue.issue.created_at (line 210).
        self.assertIsNotNone(metrics[0].created_at)

    @patch.dict(
        os.environ,
        {
            "GH_TOKEN": "test_token",
            "SEARCH_QUERY": "is:pr repo:owner/repo",
            "DRAFT_PR_TRACKING": "true",
        },
    )
    def test_pull_request_with_ready_for_review_path(self):
        """Cover issue_metrics.py:149-153 — ready_for_review and time_in_draft."""

        mock_pr_obj = MagicMock()
        pr = _make_pr_search_result(pull_request=mock_pr_obj)

        with (
            patch(
                "issue_metrics.get_time_to_ready_for_review",
                return_value=datetime.fromisoformat("2023-01-02T00:00:00Z"),
            ),
            patch(
                "issue_metrics.measure_time_in_draft",
                return_value=timedelta(days=1),
            ),
            patch("issue_metrics.measure_time_to_first_review", return_value=None),
            patch("issue_metrics.measure_time_to_first_response", return_value=None),
        ):
            metrics, _open, _closed = get_per_issue_metrics(
                [pr],
                env_vars=get_env_vars(test=True),
            )
        self.assertEqual(metrics[0].time_in_draft, timedelta(days=1))


# ---------------------------------------------------------------------------
# issue_metrics.py:441 — __main__ guard. Re-executing the module under
# runpy with run_name='__main__' covers the `if __name__ == "__main__": main()`
# block. We patch get_env_vars to short-circuit before any real work happens.
# ---------------------------------------------------------------------------
class TestIssueMetricsMainGuard(unittest.TestCase):
    """Covers issue_metrics.py:441 — the `main()` call under __main__."""

    def test_main_guard_invokes_main(self):
        """Executes issue_metrics as __main__ to cover the if-name guard."""

        original_module = sys.modules.get("issue_metrics")
        try:
            sys.modules.pop("issue_metrics", None)
            # Patch get_env_vars at import-time so main() raises immediately
            # without doing any real GitHub work. We only need the
            # `if __name__ == "__main__": main()` line itself to execute
            # for coverage to register line 441.
            with patch(
                "config.get_env_vars",
                side_effect=SystemExit(0),
            ):
                with self.assertRaises(SystemExit):
                    runpy.run_module("issue_metrics", run_name="__main__")
        finally:
            # Restore the originally imported module so other tests see the
            # same identity for any patches they have applied.
            if original_module is not None:
                sys.modules["issue_metrics"] = original_module
            else:
                sys.modules.pop("issue_metrics", None)


if __name__ == "__main__":
    unittest.main()
