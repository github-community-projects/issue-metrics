"""A module containing classes for representing GitHub issues and their metrics.

Classes:
    IssueWithMetrics: A class to represent a GitHub issue with metrics.

"""


class IssueWithMetrics:
    """A class to represent a GitHub issue with metrics.

    Attributes:
        title (str): The title of the issue.
        html_url (str): The URL of the issue on GitHub.
        author (str): The author of the issue.
        assignee (str, optional): The primary assignee of the issue.
        assignees (list, optional): All assignees of the issue.
        time_to_first_response (timedelta, optional): The time it took to
            get the first response to the issue.
        time_to_close (timedelta, optional): The time it took to close the issue.
        time_to_answer (timedelta, optional): The time it took to answer the
            discussions in the issue.
        time_in_draft (timedelta, optional): The time the PR was in draft state.
        label_metrics (dict, optional): A dictionary containing the label metrics
        mentor_activity (dict, optional): A dictionary containing active mentors
        created_at (datetime, optional): The time the issue was created.
        status (str, optional): The status of the issue, e.g., "open", "closed as completed",
        pr_comment_count (int, optional): The number of comments on the PR (excluding bots).
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        title,
        html_url,
        author,
        time_to_first_response=None,
        time_to_close=None,
        time_to_answer=None,
        time_in_draft=None,
        labels_metrics=None,
        mentor_activity=None,
        created_at=None,
        assignee=None,
        assignees=None,
        status=None,
        pr_comment_count=None,
    ):
        self.title = title
        self.html_url = html_url
        self.author = author
        self.assignee = assignee
        self.assignees = assignees or []
        self.time_to_first_response = time_to_first_response
        self.time_to_first_review = None
        self.time_to_close = time_to_close
        self.time_to_answer = time_to_answer
        self.time_in_draft = time_in_draft
        self.label_metrics = labels_metrics
        self.mentor_activity = mentor_activity
        self.created_at = created_at
        self.status = status
        self.pr_comment_count = pr_comment_count
