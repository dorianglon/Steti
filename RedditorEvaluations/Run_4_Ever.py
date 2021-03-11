from ScrapingTools.Scraping import *
import time
import math
import os
from datetime import date


def check_for_new_redditors(subreddit_of_U, path_to_redditors_from_U):
    """
    Function checks for new redditors from a subreddit every 5 minutes
    """
    # get list of redditors from this school
    curr_redditors = []
    with open(path_to_redditors_from_U, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line.strip('\n')
            curr_redditors.append(line)

    # initial condition, get posts on sub from the last 6 hours
    latest_post = math.floor(time.time() - 21600)

    while True:
        check_for_redditors = GetRedditorsFromUSub(subreddit_of_U, latest_post, path_to_redditors_from_U)
        data = check_for_redditors.fetch_posts(sort_type='created_utc', sort='asc', size=1000)
        if data is not None:
            check_for_redditors.extract_redditors_from_U_sub_live_mode(data)
            post_to_check = data[-len(data)]
            date_of_post = post_to_check['created_utc']
            latest_post = date_of_post
        time.sleep(300)


def make_directory_for_the_day(university, parent_directory):
    """
    Function creates a directory within the parent directory. It will contain file of redditors from that specific time frame
    """
    today = str(date.today())
    new_dir = parent_directory + '/' + university + '_' + today
    os.mkdir(new_dir)
    return new_dir


def check_for_redditor_posts_and_comments(university, path_to_redditors_from_U, parent_directory):
    curr_redditors = []
    with open(path_to_redditors_from_U, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line.strip('\n')
            curr_redditors.append(line)

    curr_day = int(date.today().strftime('%d'))
    check_after = math.floor(time.time() - 300)
    directory_path = make_directory_for_the_day(university, parent_directory)

    while True:
        check_if_new_day = int(date.today().strftime('%d'))
        if check_if_new_day == (curr_day + 1):
            curr_day = check_if_new_day
            directory_path = make_directory_for_the_day(university, parent_directory)

        for redditor in curr_redditors:
            redditor_file_path = directory_path + '/' + redditor + '.txt'
            redditor_data = ScrapeRedditorData(redditor, check_after, redditor_file_path)
            redditor_data.extract_redditor_data(sort_type='created_utc', sort='asc', size=1000, posts=True,
                                                comments=True)
