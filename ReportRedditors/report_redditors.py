import praw
from Databases.archivesDB import *


class ReportSuicidalRedditor:
    """
    CLASS CONNECTS TO BOT AND REPORTS SUICIDAL REDDITOR TO REDDIT
    """

    def __init__(self, post_id, archives_db):
        self.post_id = post_id
        self.archives_db = archives_db
        self.reddit = praw.Reddit(
            client_id="PYhBZnomUNnE9w",
            client_secret="qC3PhLNu3Uarls1MnyanVxa3cWDlTA",
            user_agent="BPGhelperv1",
            username="BPGlimited",
            password="bpgpassword",
        )

    def report_redditor(self):
        submission = self.reddit.submission(id=self.post_id)
        submission.report('Suicidal Ideation')
        archives_conn = create_connection_archives(self.archives_db)
        with archives_conn:
            update_author_report_value(archives_conn, submission.author, 1)