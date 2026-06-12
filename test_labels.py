"""Unit tests for labels.py"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import github3
import pytz
from classes import IssueWithMetrics
from labels import get_label_events, get_label_metrics, get_stats_time_in_labels


class TestLabels(unittest.TestCase):
    """Unit tests for labels.py"""

    def setUp(self):
        self.issue = MagicMock()  # type: ignore
        self.issue.issue = MagicMock(spec=github3.issues.Issue)  # type: ignore
        self.issue.created_at = "2021-01-01T00:00:00Z"
        self.issue.closed_at = "2021-01-05T00:00:00Z"
        self.issue.state = "closed"
        self.issue.issue.events.return_value = [
            MagicMock(
                event="labeled",
                label={"name": "bug"},
                created_at=datetime(2021, 1, 1, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="labeled",
                label={"name": "feature"},
                created_at=datetime(2021, 1, 2, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="unlabeled",
                label={"name": "bug"},
                created_at=datetime(2021, 1, 3, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="labeled",
                label={"name": "bug"},
                created_at=datetime(2021, 1, 4, tzinfo=pytz.UTC),
            ),
            # Label labeled after issue close date
            MagicMock(
                event="labeled",
                label={"name": "foo"},
                created_at=datetime(2021, 1, 20, tzinfo=pytz.UTC),
            ),
        ]

    def test_get_label_events(self):
        """Test get_label_events"""
        labels = ["bug"]
        events = get_label_events(self.issue, labels)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].label["name"], "bug")
        self.assertEqual(events[1].label["name"], "bug")
        self.assertEqual(events[2].label["name"], "bug")

    def test_get_label_metrics_closed_issue(self):
        """Test get_label_metrics using a closed issue"""
        labels = ["bug", "feature"]
        metrics = get_label_metrics(self.issue, labels)
        self.assertEqual(metrics["bug"], timedelta(days=3))
        self.assertEqual(metrics["feature"], timedelta(days=3))

    def test_get_label_metrics_open_issue(self):
        """Test get_label_metrics using an open issue"""
        self.issue.state = "open"
        labels = ["bug", "feature"]
        metrics = get_label_metrics(self.issue, labels)
        self.assertLessEqual(
            metrics["bug"],
            datetime.now(pytz.utc) - datetime(2021, 1, 2, tzinfo=pytz.UTC),
        )
        self.assertGreater(
            metrics["bug"],
            datetime.now(pytz.utc) - datetime(2021, 1, 3, tzinfo=pytz.UTC),
        )
        self.assertLessEqual(
            metrics["feature"],
            datetime.now(pytz.utc) - datetime(2021, 1, 2, tzinfo=pytz.UTC),
        )
        self.assertGreater(
            metrics["feature"],
            datetime.now(pytz.utc) - datetime(2021, 1, 4, tzinfo=pytz.UTC),
        )

    def test_get_label_metrics_closed_issue_labeled_past_closed_at(self):
        """Test get_label_metrics using a closed issue that was labeled past issue closed_at"""
        self.issue.state = "closed"
        labels = ["foo"]
        metrics = get_label_metrics(self.issue, labels)
        self.assertEqual(metrics["foo"], None)

    def test_get_label_metrics_closed_issue_label_removed_before_closure(self):
        """Test get_label_metrics for a closed issue where label was removed before closure"""
        # Create a mock issue that reproduces the problem scenario:
        # Issue created: day 0 (2021-01-01)
        # Label added: day 5 (2021-01-06)
        # Label removed: day 10 (2021-01-11)
        # Issue closed: day 15 (2021-01-16)
        # Expected duration: 5 days (from day 5 to day 10)

        issue = MagicMock()
        issue.issue = MagicMock(spec=github3.issues.Issue)
        issue.created_at = "2021-01-01T00:00:00Z"
        issue.closed_at = "2021-01-16T00:00:00Z"  # 15 days after creation
        issue.state = "closed"
        issue.issue.events.return_value = [
            MagicMock(
                event="labeled",
                label={"name": "test-label"},
                created_at=datetime(2021, 1, 6, tzinfo=pytz.UTC),  # day 5
            ),
            MagicMock(
                event="unlabeled",
                label={"name": "test-label"},
                created_at=datetime(2021, 1, 11, tzinfo=pytz.UTC),  # day 10
            ),
        ]

        labels = ["test-label"]
        metrics = get_label_metrics(issue, labels)

        # Should be 5 days (from day 5 to day 10), not 15 days (full issue duration)
        expected_duration = timedelta(days=5)
        self.assertEqual(metrics["test-label"], expected_duration)

    def test_get_label_metrics_closed_issue_label_remains_through_closure(self):
        """Test get_label_metrics for a closed issue where label remains applied through closure"""
        # Test scenario where label is applied and never removed:
        # Issue created: day 0 (2021-01-01)
        # Label added: day 2 (2021-01-03)
        # Issue closed: day 10 (2021-01-11)
        # Expected duration: 10 days (from issue creation to closure)

        issue = MagicMock()
        issue.issue = MagicMock(spec=github3.issues.Issue)
        issue.created_at = "2021-01-01T00:00:00Z"
        issue.closed_at = "2021-01-11T00:00:00Z"  # 10 days after creation
        issue.state = "closed"
        issue.issue.events.return_value = [
            MagicMock(
                event="labeled",
                label={"name": "stays-applied"},
                created_at=datetime(2021, 1, 3, tzinfo=pytz.UTC),  # day 2
            ),
            # No unlabel event - label remains applied
        ]

        labels = ["stays-applied"]
        metrics = get_label_metrics(issue, labels)

        # Should be 8 days (from day 2 when label was applied to day 10 when issue closed)
        expected_duration = timedelta(days=8)
        self.assertEqual(metrics["stays-applied"], expected_duration)

    def test_get_label_metrics_label_applied_at_creation_and_removed_before_closure(
        self,
    ):
        """Test get_label_metrics for a label applied at issue creation and removed before closure"""
        # Test scenario where label is applied at creation and later removed:
        # Issue created: day 0 (2021-01-01) with label applied
        # Label removed: day 7 (2021-01-08)
        # Issue closed: day 20 (2021-01-21)
        # Expected duration: 7 days (from creation to removal)

        issue = MagicMock()
        issue.issue = MagicMock(spec=github3.issues.Issue)
        issue.created_at = "2021-01-01T00:00:00Z"
        issue.closed_at = "2021-01-21T00:00:00Z"  # 20 days after creation
        issue.state = "closed"
        issue.issue.events.return_value = [
            MagicMock(
                event="labeled",
                label={"name": "creation-label"},
                created_at=datetime(2021, 1, 1, tzinfo=pytz.UTC),  # day 0 - at creation
            ),
            MagicMock(
                event="unlabeled",
                label={"name": "creation-label"},
                created_at=datetime(2021, 1, 8, tzinfo=pytz.UTC),  # day 7
            ),
        ]

        labels = ["creation-label"]
        metrics = get_label_metrics(issue, labels)

        # Should be 7 days (from creation to removal), not 20 days (full issue duration)
        expected_duration = timedelta(days=7)
        self.assertEqual(metrics["creation-label"], expected_duration)

    def test_get_label_metrics_label_applied_at_creation_remains_through_closure(self):
        """Test get_label_metrics for a label applied at creation and kept through closure"""
        # Test scenario where label is applied at creation and never removed:
        # Issue created: day 0 (2021-01-01) with label applied
        # Issue closed: day 30 (2021-01-31)
        # Expected duration: 30 days (full issue duration)

        issue = MagicMock()
        issue.issue = MagicMock(spec=github3.issues.Issue)
        issue.created_at = "2021-01-01T00:00:00Z"
        issue.closed_at = "2021-01-31T00:00:00Z"  # 30 days after creation
        issue.state = "closed"
        issue.issue.events.return_value = [
            MagicMock(
                event="labeled",
                label={"name": "permanent-label"},
                created_at=datetime(2021, 1, 1, tzinfo=pytz.UTC),  # day 0 - at creation
            ),
            # No unlabel event - label remains applied
        ]

        labels = ["permanent-label"]
        metrics = get_label_metrics(issue, labels)

        # Should be 30 days (full issue duration since label was applied at creation)
        expected_duration = timedelta(days=30)
        self.assertEqual(metrics["permanent-label"], expected_duration)

    def test_get_label_metrics_multiple_labels_different_timeframes(self):
        """Test get_label_metrics with multiple labels having different application patterns and longer timeframes"""
        # Test scenario with multiple labels and longer timeframes:
        # Issue created: day 0 (2021-01-01)
        # Label A applied: day 0 (at creation)
        # Label B applied: day 14 (2021-01-15)
        # Label A removed: day 21 (2021-01-22)
        # Label B removed: day 35 (2021-02-05)
        # Issue closed: day 60 (2021-03-02)
        # Expected: Label A = 21 days, Label B = 21 days

        issue = MagicMock()
        issue.issue = MagicMock(spec=github3.issues.Issue)
        issue.created_at = "2021-01-01T00:00:00Z"
        issue.closed_at = "2021-03-02T00:00:00Z"  # 60 days after creation
        issue.state = "closed"
        issue.issue.events.return_value = [
            MagicMock(
                event="labeled",
                label={"name": "label-a"},
                created_at=datetime(2021, 1, 1, tzinfo=pytz.UTC),  # day 0 - at creation
            ),
            MagicMock(
                event="labeled",
                label={"name": "label-b"},
                created_at=datetime(2021, 1, 15, tzinfo=pytz.UTC),  # day 14
            ),
            MagicMock(
                event="unlabeled",
                label={"name": "label-a"},
                created_at=datetime(2021, 1, 22, tzinfo=pytz.UTC),  # day 21
            ),
            MagicMock(
                event="unlabeled",
                label={"name": "label-b"},
                created_at=datetime(2021, 2, 5, tzinfo=pytz.UTC),  # day 35
            ),
        ]

        labels = ["label-a", "label-b"]
        metrics = get_label_metrics(issue, labels)

        # Label A: 21 days (from day 0 to day 21)
        # Label B: 21 days (from day 14 to day 35)
        expected_duration_a = timedelta(days=21)
        expected_duration_b = timedelta(days=21)
        self.assertEqual(metrics["label-a"], expected_duration_a)
        self.assertEqual(metrics["label-b"], expected_duration_b)


class TestGetAverageTimeInLabels(unittest.TestCase):
    """Unit tests for get_stats_time_in_labels"""

    def setUp(self):
        self.issues_with_metrics = MagicMock()
        self.issues_with_metrics = [
            IssueWithMetrics(
                title="issue1",
                html_url="url1",
                author="alice",
                time_to_first_response=None,
                time_to_close=None,
                time_to_answer=None,
                labels_metrics={"bug": timedelta(days=2)},
            ),
        ]

    def test_get_stats_time_in_labels(self):
        """Test get_stats_time_in_labels"""
        labels = ["bug", "feature"]
        metrics = get_stats_time_in_labels(self.issues_with_metrics, labels)
        print(metrics)
        self.assertEqual(len(metrics["avg"]), 2)
        self.assertEqual(metrics["avg"]["bug"], timedelta(days=2))
        self.assertIsNone(metrics["avg"].get("feature"))


class TestLabelsCoverageGaps(unittest.TestCase):
    """Covers labels.py edge-case branches."""

    def test_get_label_metrics_returns_early_when_no_events(self):
        """Early return when there are no label events."""

        issue = MagicMock()
        issue.issue = MagicMock(spec=github3.issues.Issue)
        issue.created_at = "2021-01-01T00:00:00Z"
        issue.closed_at = "2021-01-05T00:00:00Z"
        issue.state = "closed"
        issue.issue.events.return_value = []

        result = get_label_metrics(issue, ["bug"])
        self.assertEqual(result, {"bug": None})

    def test_get_label_metrics_unlabeled_first_initializes_zero(self):
        """'unlabeled' event with no prior 'labeled' init."""

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
        """Open issue whose last event is 'unlabeled' is skipped."""

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
        # labeled at +0d (subtracts 0), unlabeled at +2d (adds 2d) -> 2 days.
        self.assertEqual(result["bug"], timedelta(days=2))

    def test_get_stats_time_in_labels_skips_none_and_appends(self):
        """None label_metrics is skipped; second hit appends."""

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


if __name__ == "__main__":
    unittest.main()
