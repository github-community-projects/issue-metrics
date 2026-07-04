"""Unit tests for labels.py"""

import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytz
from classes import IssueWithMetrics
from labels import get_label_events, get_label_metrics, get_stats_time_in_labels


def _label(name):
    """Create a label-like object with a .name attribute."""
    return SimpleNamespace(name=name)


class TestLabels(unittest.TestCase):
    """Unit tests for labels.py"""

    def setUp(self):
        self.issue = MagicMock()
        self.issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.UTC)
        self.issue.closed_at = datetime(2021, 1, 5, tzinfo=pytz.UTC)
        self.issue.state = "closed"
        self.issue.get_events.return_value = [
            MagicMock(
                event="labeled",
                label=_label("bug"),
                created_at=datetime(2021, 1, 1, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="labeled",
                label=_label("feature"),
                created_at=datetime(2021, 1, 2, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="unlabeled",
                label=_label("bug"),
                created_at=datetime(2021, 1, 3, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="labeled",
                label=_label("bug"),
                created_at=datetime(2021, 1, 4, tzinfo=pytz.UTC),
            ),
            # Label labeled after issue close date
            MagicMock(
                event="labeled",
                label=_label("foo"),
                created_at=datetime(2021, 1, 20, tzinfo=pytz.UTC),
            ),
        ]

    def test_get_label_events(self):
        """Test get_label_events"""
        labels = ["bug"]
        events = get_label_events(self.issue, labels)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].label.name, "bug")
        self.assertEqual(events[1].label.name, "bug")
        self.assertEqual(events[2].label.name, "bug")

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

        issue = MagicMock()
        issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.UTC)
        issue.closed_at = datetime(2021, 1, 16, tzinfo=pytz.UTC)
        issue.state = "closed"
        issue.get_events.return_value = [
            MagicMock(
                event="labeled",
                label=_label("test-label"),
                created_at=datetime(2021, 1, 6, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="unlabeled",
                label=_label("test-label"),
                created_at=datetime(2021, 1, 11, tzinfo=pytz.UTC),
            ),
        ]

        labels = ["test-label"]
        metrics = get_label_metrics(issue, labels)

        expected_duration = timedelta(days=5)
        self.assertEqual(metrics["test-label"], expected_duration)

    def test_get_label_metrics_closed_issue_label_remains_through_closure(self):
        """Test get_label_metrics for a closed issue where label remains applied through closure"""

        issue = MagicMock()
        issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.UTC)
        issue.closed_at = datetime(2021, 1, 11, tzinfo=pytz.UTC)
        issue.state = "closed"
        issue.get_events.return_value = [
            MagicMock(
                event="labeled",
                label=_label("stays-applied"),
                created_at=datetime(2021, 1, 3, tzinfo=pytz.UTC),
            ),
        ]

        labels = ["stays-applied"]
        metrics = get_label_metrics(issue, labels)

        expected_duration = timedelta(days=8)
        self.assertEqual(metrics["stays-applied"], expected_duration)

    def test_get_label_metrics_label_applied_at_creation_and_removed_before_closure(
        self,
    ):
        """Test get_label_metrics for a label applied at issue creation and removed before closure"""

        issue = MagicMock()
        issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.UTC)
        issue.closed_at = datetime(2021, 1, 21, tzinfo=pytz.UTC)
        issue.state = "closed"
        issue.get_events.return_value = [
            MagicMock(
                event="labeled",
                label=_label("creation-label"),
                created_at=datetime(2021, 1, 1, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="unlabeled",
                label=_label("creation-label"),
                created_at=datetime(2021, 1, 8, tzinfo=pytz.UTC),
            ),
        ]

        labels = ["creation-label"]
        metrics = get_label_metrics(issue, labels)

        expected_duration = timedelta(days=7)
        self.assertEqual(metrics["creation-label"], expected_duration)

    def test_get_label_metrics_label_applied_at_creation_remains_through_closure(self):
        """Test get_label_metrics for a label applied at creation and kept through closure"""

        issue = MagicMock()
        issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.UTC)
        issue.closed_at = datetime(2021, 1, 31, tzinfo=pytz.UTC)
        issue.state = "closed"
        issue.get_events.return_value = [
            MagicMock(
                event="labeled",
                label=_label("permanent-label"),
                created_at=datetime(2021, 1, 1, tzinfo=pytz.UTC),
            ),
        ]

        labels = ["permanent-label"]
        metrics = get_label_metrics(issue, labels)

        expected_duration = timedelta(days=30)
        self.assertEqual(metrics["permanent-label"], expected_duration)

    def test_get_label_metrics_multiple_labels_different_timeframes(self):
        """Test get_label_metrics with multiple labels having different application patterns and longer timeframes"""

        issue = MagicMock()
        issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.UTC)
        issue.closed_at = datetime(2021, 3, 2, tzinfo=pytz.UTC)
        issue.state = "closed"
        issue.get_events.return_value = [
            MagicMock(
                event="labeled",
                label=_label("label-a"),
                created_at=datetime(2021, 1, 1, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="labeled",
                label=_label("label-b"),
                created_at=datetime(2021, 1, 15, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="unlabeled",
                label=_label("label-a"),
                created_at=datetime(2021, 1, 22, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="unlabeled",
                label=_label("label-b"),
                created_at=datetime(2021, 2, 5, tzinfo=pytz.UTC),
            ),
        ]

        labels = ["label-a", "label-b"]
        metrics = get_label_metrics(issue, labels)

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
        issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.UTC)
        issue.closed_at = datetime(2021, 1, 5, tzinfo=pytz.UTC)
        issue.state = "closed"
        issue.get_events.return_value = []

        result = get_label_metrics(issue, ["bug"])
        self.assertEqual(result, {"bug": None})

    def test_get_label_metrics_unlabeled_first_initializes_zero(self):
        """'unlabeled' event with no prior 'labeled' init."""

        issue = MagicMock()
        issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.UTC)
        issue.closed_at = datetime(2021, 1, 5, tzinfo=pytz.UTC)
        issue.state = "closed"
        issue.get_events.return_value = [
            MagicMock(
                event="unlabeled",
                label=_label("bug"),
                created_at=datetime(2021, 1, 2, tzinfo=pytz.UTC),
            ),
        ]

        result = get_label_metrics(issue, ["bug"])
        self.assertIsInstance(result["bug"], timedelta)

    def test_get_label_metrics_open_issue_last_event_unlabeled_skips(self):
        """Open issue whose last event is 'unlabeled' is skipped."""

        issue = MagicMock()
        issue.created_at = datetime(2021, 1, 1, tzinfo=pytz.UTC)
        issue.closed_at = None
        issue.state = "open"
        issue.get_events.return_value = [
            MagicMock(
                event="labeled",
                label=_label("bug"),
                created_at=datetime(2021, 1, 1, tzinfo=pytz.UTC),
            ),
            MagicMock(
                event="unlabeled",
                label=_label("bug"),
                created_at=datetime(2021, 1, 3, tzinfo=pytz.UTC),
            ),
        ]

        result = get_label_metrics(issue, ["bug"])
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
        self.assertIsNone(stats["avg"]["bug"])
        self.assertEqual(stats["avg"]["feature"], timedelta(seconds=15))


if __name__ == "__main__":
    unittest.main()
