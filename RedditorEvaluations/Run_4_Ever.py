from ScrapingTools.Scraping import *
import time
import math
import os
from datetime import date
from database.userDb import *


def check_for_new_uni_redditors(subreddit_of_U, path_to_database, all_time_list, university=True, college=True):
    """
    Function checks for new redditors from a subreddit every 5 minutes
    :param subreddit_of_U: subreddit for uni/college
    :param path_to_database: path to this subreddit's redditor database
    :param all_time_list:
    :param university: boolean, true if university
    :param college: boolean, true if college
    """

    # initial condition, get posts on sub from the last 6 hours
    latest_post = math.floor(time.time() - 21600)

    while True:
        check_for_redditors = GetRedditorsFromSub(subreddit_of_U, latest_post, path_to_database, all_time_list)
        data = check_for_redditors.fetch_posts(sort_type='created_utc', sort='asc', size=1000)
        if data is not None:
            check_for_redditors.extract_uni_redditors_live(university, college, data)

            # if the latest post was posted after our variable "latest_post" then replace value with newer date
            post_to_check = data[-len(data)]
            date_of_post = post_to_check['created_utc']
            latest_post = date_of_post
        time.sleep(300)


def check_for_redditor_posts_and_comments(database_file):

    while True:
        conn = create_connection(database_file)
        curr_redditors = list_users(conn)
        for redditor in curr_redditors:
            last_checked = find_user(conn, redditor)[1]
            if time.time() > last_checked:
                file_to_save = 'temp_file.txt'
                this_redditor = ScrapeRedditorData(redditor, last_checked, file_to_save)
                new_data, finished_running = this_redditor.extract_redditor_data('created_utc', 'asc', 1000, True, False, False)
                update_user(conn, redditor, finished_running)
                if new_data:
                    # then predict user state of mind
                    pass
                else:
                    # then move onto the next
                    pass