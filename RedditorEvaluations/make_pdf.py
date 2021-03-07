from fpdf import FPDF
import ftfy
import os
import datetime

WIDTH = 210
HEIGHT = 297


def create_title_NN(pdf, username):
    """
    Function creates a title for our pdf
    :param pdf: our pdf object
    :param username: redditor username that the pdf is for
    """

    title = 'Report for ' + username
    pdf.set_font('helvetica', 'B', 15)
    w = pdf.get_string_width(title) + 6
    pdf.set_x((210 - w) / 2)
    # Colors of frame, background and text
    pdf.set_draw_color(209.0, 15.0, 15.0)
    pdf.set_fill_color(202.0, 76.0, 76.0)
    pdf.set_text_color(0.0, 0.0, 0.0)
    # Thickness of frame (1 mm)
    pdf.set_line_width(1)
    # Title
    pdf.cell(w, 9, title, 1, 1, 'C', True)
    # Line break
    pdf.ln(10)


def add_rectangle_NN(pdf):
    """
    Function adds a pretty rectangle around pdf
    :param pdf: our pdf object
    """

    pdf.set_fill_color(209.0, 15.0, 15.0)
    pdf.rect(5.0, 5.0, 200.0, 287.0, 'DF')
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(8.0, 8.0, 194.0, 282.0, 'FD')


def write_logo_NN(pdf, logo_path):
    """
    Function puts school logo on pdf
    :param pdf: our pdf object
    :param logo_path: path to school logo image
    """

    pdf.set_xy(8.5, 8.5)
    pdf.image(logo_path, link='', type='', w=1586 / 80, h=1920 / 80)


def create_analytics_report_NN(username, depressed, word_cloud_file, subs_file, dest_dir):
    """
    Function creates pdf report for a redditor with depressed/suicidal posts, and saves it.
    :param username: redditor username
    :param depressed: list containing the text, subreddit, and date. In format of [['text', subreddit, date], [...]]
    :param word_cloud_file: path for word cloud image
    :param subs_file: path for image of graph of subreddits
    :param dest_dir: destination directory
    """

    # create pdf object
    pdf = FPDF()  # A4 (210 by 297 mm)
    username = ftfy.fix_text(username)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=3)
    add_rectangle_NN(pdf)
    write_logo_NN(pdf, 'cornell.png')
    create_title_NN(pdf, username)

    pdf.write(5, '\nPossible suicidal/depressed posts or comments have been spotted for ' + username + '\n'
            + '\nHere are the posts that have been flagged, followed by the date posted, the subreddit posted on'
              ', and the negative score it was given.\n\n')

    # writes the posts containing signs of depression or suicidal ideation
    i = 1
    for post in depressed:
        text = post[0]
        date = post[1]
        new_date = datetime.datetime.fromtimestamp(date).strftime('%c')
        sub = post[2]
        score = float(post[3]) * 100
        pdf.write(5, '\n' + str(i) + ')  ')
        pdf.write(5, text + '\n\n[ date posted : ' + str(new_date) +
                  '] | [ subreddit : ' + str(sub) + '] | [' + 'probability of depression : ' + str(score) + ' % ]\n')
        i += 1

    # writes an image of word cloud for the redditor in question
    pdf.write(5, '\n\n\nBelow is a Word Cloud tracking the different words used in ' + username
              + "'s posts.\n\n\n")
    pdf.image(word_cloud_file, w=WIDTH/1.5)
    # deletes the file once it is written to the report
    os.remove(word_cloud_file)

    # writes an image of a graph showing the different subreddits posted and commented
    # on for the redditor in question
    pdf.write(5, '\n\n\nBelow is a graph showing all of the subreddits that ' + username
              + ' is active in.\n\n\n')
    pdf.image(subs_file, w=WIDTH/1.5)
    # deletes the file once it is written to the report
    os.remove(subs_file)

    # saves the report in the destination directory
    file_name = dest_dir + '/' + username + '_report.pdf'
    pdf.output(file_name, 'F')