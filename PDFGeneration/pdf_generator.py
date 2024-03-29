from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from Databases.archivesDB import *
import os
from Shared_Resources.resources import *


class CreateDailyPDF:
    """
    CLASS GENERATES THE DAILY PDFS FOR THE SCHOOL
    """

    def __init__(self, data, institution, filename, archives_db, num_users_flagged, new_ids_file):
        self.data = data
        self.institution = institution
        self.filename = filename
        self.directory = MAIN
        self.archives_db = archives_db
        self.num_users_flagged = num_users_flagged
        self.new_ids_file = new_ids_file
        self.school_directory = self.directory + self.institution

    def make_pdf(self):
        """
        Function builds our daily pdf
        """

        doc = SimpleDocTemplate(self.filename, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        Story = []
        logo = self.directory + 'Steti_Tech_Logos/' + 'logo_transparent.png'
        title_date = self.institution + ' ' + str(self.data['date'])
        users = self.data['users']

        im = Image(logo, 2 * inch, 2 * inch)
        Story.append(im)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='times-roman', alignment=TA_JUSTIFY))

        ptext = '<font size="15">%s</font>' % title_date
        Story.append(Spacer(1, 24))
        Story.append(Paragraph(ptext, styles['Title']))

        new_ids = []
        with open(self.new_ids_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                new_ids.append(line.replace('\n', ''))

        # loop through the users and write down the data. title, text, date, subreddit, negativity score
        count = 1
        for user in users:

            # if there are more users flagged in this new batch on same day we have to update the total amount of times
            # they were flagged
            if count > self.num_users_flagged:
                archives_conn = create_connection_archives(self.archives_db)
                with archives_conn:
                    prev_flagged = get_num_flagged(archives_conn, user['username'])[1]
                    # update_author_flagged_value(archives_conn, user['username'])
            elif count <= self.num_users_flagged:
                archives_conn = create_connection_archives(self.archives_db)
                with archives_conn:
                    prev_flagged = get_num_flagged(archives_conn, user['username'])[1]

            if count == 1:
                if prev_flagged > 1:
                    username = 'User : ' + user['username']
                    flagged = 'Amount of times previously flagged : ' + str(prev_flagged)
                    ptext = '<font size="13">%s</font>' % username
                    ftext = '<font size="13">%s</font>' % flagged
                    Story.append(Spacer(1, 12))
                    Story.append(Paragraph(ptext, styles['Heading1']))
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ftext, styles['Heading1']))
                else:
                    username = 'User : ' + user['username']
                    ptext = '<font size="13">%s</font>' % username
                    Story.append(Spacer(1, 12))
                    Story.append(Paragraph(ptext, styles['Heading1']))

            elif count != 1:
                if prev_flagged > 1:
                    username = 'User : ' + user['username']
                    flagged = 'Amount of times previously flagged : ' + str(prev_flagged)
                    ptext = '<font size="13">%s</font>' % username
                    ftext = '<font size="13">%s</font>' % flagged
                    Story.append(Spacer(1, 12))
                    Story.append(Paragraph(ptext, styles['Heading1']))
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ftext, styles['Heading1']))
                else:
                    username = 'User : ' + user['username']
                    ptext = '<font size="13">%s</font>' % username
                    Story.append(Spacer(1, 36))
                    Story.append(Paragraph(ptext, styles['Heading1']))

            texts = user['top_neg_posts_and_comments']
            for text in texts:

                if os.path.isfile(self.new_ids_file):
                    if new_ids:
                        check_id = text[3]
                        if check_id in new_ids:
                            ptext = '<font size="13" color="red">%s</font>' % 'NEW'
                            Story.append(Spacer(1, 6))
                            Story.append(Paragraph(ptext, styles['Heading1']))

                type = text[0]
                if type == 'Post':
                    type_ = 'Type : ' + type
                    ptext = '<font size="13">%s</font>' % type_
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    title = 'Title of Post : ' + text[1]
                    ptext = '<font size="13">%s</font>' % title
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    post = 'Post : ' + text[2]
                    ptext = '<font size="13">%s</font>' % post
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    id = 'Post id : ' + str(text[3])
                    ptext = '<font size="13">%s</font>' % id
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    readable_date = datetime.utcfromtimestamp(text[4]).strftime('%Y-%m-%d %H:%M')
                    date = 'Date posted : ' + readable_date
                    ptext = '<font size="13">%s</font>' % date
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    subreddit = 'Subreddit posted on : ' + text[5]
                    ptext = '<font size="13">%s</font>' % subreddit
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    link = 'Link to post : ' + text[6]
                    ptext = '<font size="13">%s</font>' % link
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    severity = 'Confidence level that user is showing signs of a mental health crisis : ' + str(text[7]) + '%'
                    ptext = '<font size="13">%s</font>' % severity
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))
                    Story.append(Spacer(1, 12))

                elif type == 'Comment':
                    type_ = 'Type : ' + type
                    ptext = '<font size="13">%s</font>' % type_
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    comment = 'Comment : ' + text[1]
                    ptext = '<font size="13">%s</font>' % comment
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    id = 'Comment id : ' + str(text[2])
                    ptext = '<font size="13">%s</font>' % id
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    readable_date = datetime.utcfromtimestamp(text[3]).strftime('%Y-%m-%d %H:%M')
                    date = 'Date commented : ' + readable_date
                    ptext = '<font size="13">%s</font>' % date
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    subreddit = 'Subreddit commented on : ' + text[4]
                    ptext = '<font size="13">%s</font>' % subreddit
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))

                    severity = 'Confidence level that user is showing signs of a mental health crisis: ' + str(text[5]) + '%'
                    ptext = '<font size="13">%s</font>' % severity
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ptext, styles['Normal']))
                    Story.append(Spacer(1, 12))

            count += 1

        doc.build(Story)

        # returns how many users were in this batch
        return count
