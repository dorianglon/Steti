import praw


class ReportSuicidalRedditor:
    """
    CLASS CONNECTS TO BOT AND REPORTS SUICIDAL REDDITOR TO REDDIT
    """

    def __init__(self, post_id):
        self.post_id = post_id
        self.reddit = praw.Reddit(
            client_id="PYhBZnomUNnE9w",
            client_secret="qC3PhLNu3Uarls1MnyanVxa3cWDlTA",
            user_agent="BPGhelperv1",
            username="bpglimitedd",
            password="bpgpassword",
        )

    def report_redditor(self):
        submission = self.reddit.submission(id=self.post_id)
        submission.report('Suicidal Ideation')


class ReportRedditorThreatToOthers:
    """
    CLASS CONNECTS TO BOT AND REPORTS REDDITOR POSING A THREAT TO OTHERS TO REDDIT
    """

    def __init__(self, post_id):
        self.post_id = post_id
        self.reddit = praw.Reddit(
            client_id="PYhBZnomUNnE9w",
            client_secret="qC3PhLNu3Uarls1MnyanVxa3cWDlTA",
            user_agent="BPGhelperv1",
            username="bpglimitedd",
            password="bpgpassword",
        )

    def report_redditor(self):
        submission = self.reddit.submission(id=self.post_id)
        submission.report('Threatening Violence')


def report_redditor(post_id, suicide=True, threat=True):
    """
    Function reports suicidal redditor or threat to others given post id
    """

    if suicide:
        report_suicide = ReportSuicidalRedditor(post_id)
        report_suicide.report_redditor()
    elif threat:
        report_threat = ReportRedditorThreatToOthers(post_id)
        report_threat.report_redditor()