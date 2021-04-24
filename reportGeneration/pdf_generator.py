from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from Databases.archivesDB import *


class CreateDailyPDF:
    """
    CLASS GENERATES THE DAILY PDFS FOR THE SCHOOL
    """

    def __init__(self, data, institution, filename, directory, archives_db):
        self.data = data
        self.institution = institution
        self.filename = filename
        self.directory = directory
        self.archives_db = archives_db
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
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

        ptext = '<font size="14">%s</font>' % title_date
        Story.append(Spacer(1, 24))
        Story.append(Paragraph(ptext, styles['Title']))

        # loop through the users and write down the data. title, text, date, subreddit, negativity score
        count = 1
        for user in users:

            archives_conn = create_connection_archives(self.archives_db)
            with archives_conn:
                prev_flagged = get_num_flagged(archives_conn, user['username'])[1]
                # update_author_flagged_value(archives_conn, user['username'])

            if count == 1:
                if prev_flagged > 1:
                    username = 'User : ' + user['username']
                    flagged = 'Amount of times previously flagged : ' + str(prev_flagged)
                    ptext = '<font size="12">%s</font>' % username
                    ftext = '<font size="12">%s</font>' % flagged
                    Story.append(Spacer(1, 12))
                    Story.append(Paragraph(ptext, styles['Heading1']))
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ftext, styles['Heading1']))
                else:
                    username = 'User : ' + user['username']
                    ptext = '<font size="12">%s</font>' % username
                    Story.append(Spacer(1, 12))
                    Story.append(Paragraph(ptext, styles['Heading1']))

            else:
                if prev_flagged > 1:
                    username = 'User : ' + user['username']
                    flagged = 'Amount of times previously flagged : ' + str(prev_flagged)
                    ptext = '<font size="12">%s</font>' % username
                    ftext = '<font size="12">%s</font>' % flagged
                    Story.append(Spacer(1, 12))
                    Story.append(Paragraph(ptext, styles['Heading1']))
                    Story.append(Spacer(1, 6))
                    Story.append(Paragraph(ftext, styles['Heading1']))
                else:
                    username = 'User : ' + user['username']
                    ptext = '<font size="12">%s</font>' % username
                    Story.append(Spacer(1, 36))
                    Story.append(Paragraph(ptext, styles['Heading1']))

            posts = user['top_neg_posts']
            for post in posts:
                title = 'Title of Post : ' + post[0]
                ptext = '<font size="12">%s</font>' % title
                Story.append(Spacer(1, 6))
                Story.append(Paragraph(ptext, styles['Normal']))

                text = 'Post : ' + post[1]
                ptext = '<font size="12">%s</font>' % text
                Story.append(Spacer(1, 6))
                Story.append(Paragraph(ptext, styles['Normal']))

                text = 'Post id : ' + str(post[2])
                ptext = '<font size="12">%s</font>' % text
                Story.append(Spacer(1, 6))
                Story.append(Paragraph(ptext, styles['Normal']))

                readable_date = datetime.utcfromtimestamp(post[3]).strftime('%Y-%m-%d %H:%M')
                date = 'Date posted : ' + readable_date
                ptext = '<font size="12">%s</font>' % date
                Story.append(Spacer(1, 6))
                Story.append(Paragraph(ptext, styles['Normal']))

                subreddit = 'Subreddit posted on : ' + post[4]
                ptext = '<font size="12">%s</font>' % subreddit
                Story.append(Spacer(1, 6))
                Story.append(Paragraph(ptext, styles['Normal']))

                severity = 'Confidence level that user is showing mental health issues : ' + str(post[5]) + '%'
                ptext = '<font size="12">%s</font>' % severity
                Story.append(Spacer(1, 6))
                Story.append(Paragraph(ptext, styles['Normal']))
                Story.append(Spacer(1, 12))

            count += 1

        doc.build(Story)
