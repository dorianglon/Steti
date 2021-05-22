from RedditTools.Reddit import *
import time
import math
import os
from datetime import datetime
from Databases.userDb import *
from Databases.postidDB import *
from Databases.archivesDB import *
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text
import numpy as np
import json
import praw
import ray
from PDFGeneration.pdf_generator import *
from calendar import Calendar
import pandas as pd
from Notifications.notifications_by_sms import *
from Shared_Resources.resources import *
from tensorflow import keras


def build_initial_database(school, start_timestamp, user_database, all_time_list, last_checked_pushshift_path
                           , university=True, college=True, first_run=True):
    """
    Function builds the founding Database of redditors for a certain school
    :param school: subreddit of university we are monitoring
    :param start_timestamp: when to start getting data from
    :param user_database: path to redditor Database for this school
    :param all_time_list: path to list with all posters and commenter's on the school's subreddit
    :param last_checked_pushshift_path: file containing timestamp that we left off with
    :param university: (True if this is a university) vice versa
    :param college: (True if this is a college) vice versa
    :param first_run: True if first time running for school
    """

    user_db_conn = create_connection(user_database)
    if first_run:
        with user_db_conn:
            create_db(user_db_conn)
    redditors = GetRedditorsFromSub(school, start_timestamp, user_database
                                    , all_time_list)
    redditors.extract_uni_redditors(last_checked_pushshift_path, university, college)


def build_redditor_database(school, path_to_user_database, path_to_post_database, all_time_list, last_checked_live_praw
                            , university=True, college=True):
    """
    Function works with Scraping classes to build and maintain an up to date Database of redditors from the university/
    college we are monitoring
    :param school: subreddit for university/college
    :param path_to_user_database: path to Database with users
    :param path_to_post_database: path to Database with post ids from the school's subreddit
    :param all_time_list: path to text file which holds every redditor to ever post on the school's subreddit
    :param last_checked_live_praw:
    :param university: (True if this is a university) vice versa
    :param college: (True if this is a college) vice versa
    """

    if not os.path.isfile(last_checked_live_praw):
        # initial condition, get posts on sub from the last 6 hours
        latest_post = math.floor(time.time() - 21600)
    else:
        with open(last_checked_live_praw, 'r') as f:
            latest_post = int(f.readlines()[0])
            f.close()

    # create praw instance when working with new posts and comments
    reddit = praw.Reddit(
        client_id="PYhBZnomUNnE9w",
        client_secret="qC3PhLNu3Uarls1MnyanVxa3cWDlTA",
        user_agent="BPGhelperv1",
        username="BPGlimited",
        password="bpgpassword",
    )

    # check if Database with post ids exists, if not create it
    if not os.path.isfile(path_to_post_database):
        post_id_conn = create_connection_post(path_to_post_database)
        with post_id_conn:
            create_post_db(post_id_conn)
    else:
        post_id_conn = create_connection_post(path_to_post_database)

    # adds new authors from institution to Database as it finds them
    check_for_redditors = GetRedditorsFromSub(school, latest_post, path_to_user_database, all_time_list)

    try:
        with post_id_conn:
            post_ids = list_post_ids(post_id_conn)
            if len(post_ids) >= 50:
                first_50 = post_ids[:50]
                check_for_redditors.extract_redditors_from_post_ids(reddit, first_50, post_id_conn,
                                                                    university, college)
            elif 0 < len(post_ids) < 50:
                check_for_redditors.extract_redditors_from_post_ids(reddit, post_ids, post_id_conn,
                                                                    university, college)
    except Exception as e:
        print(e)

    try:
        latest_post = int(check_for_redditors.extract_uni_redditors_live_(reddit, post_id_conn,
                                                                      university, college))

        if os.path.isfile(last_checked_live_praw):
            os.remove(last_checked_live_praw)

        with open(last_checked_live_praw, 'a+') as f:
            f.write(str(latest_post))
            f.close()
    except Exception:
        pass


def load_model(model_path):
    """
    Function loads our model
    :param model_path: path to model
    """

    return keras.models.load_model(model_path)


def make_sure_text_is_in_correct_encoding_posts(posts):
    """
    Function makes sure posts we analyze is in ascii encoding, if not it cleans it
    :param posts: list of posts to check
    """

    index = 0
    while index < len(posts):
        title = posts[index][0].encode('ascii', 'ignore')
        decoded_title = title.decode()
        posts[index][0] = decoded_title
        text = posts[index][1].encode("ascii", "ignore")
        decoded_text = text.decode()
        posts[index][1] = decoded_text
        index += 1
    return posts


def write_base_json(file_name, school, date):
    """
    Function makes new json file for a new day of analysis
    :param file_name: json file path
    :param school: school we are monitoring
    :param date:
    """

    initial_dic = {
        'institution': school,
        'date': date,
        'users': []
    }

    with open(file_name, 'w') as f:
        json.dump(initial_dic, f, indent=1)
        f.close()


def update_json(file_name, redditor, neg_posts):
    """
    Function adds new negative posts to the daily json for a specific redditor. If redditor is already in json it
    just updates the negative posts. If redditor is not present then it adds him to json. :param file_name: json file
    path :param redditor: redditor we are updating json for :param neg_posts: list of negative posts from this redditor
    """

    with open(file_name, 'r') as f:
        data = json.load(f)
        f.close()

    users = data.get('users')
    # if list of users flagged so far is not empty
    if users:
        user_present = False
        for user in users:
            # check if redditor we are dealing with is already in json
            if user.get('username') == redditor:
                # if so then add the new negative posts to his list of already present negative posts
                user_present = True
                user.get('top_neg_posts_and_comments').append(neg_posts)
                with open(file_name, 'w') as f:
                    json.dump(data, f, indent=1)
                    f.close()
        # if user isn't in json then add him and his posts
        if not user_present:
            data['users'].append({
                'username': redditor,
                'top_neg_posts_and_comments': neg_posts
            })
            with open(file_name, 'w') as f:
                json.dump(data, f, indent=1)
                f.close()
    # if list of users is empty then add this redditor as the first one on that list
    else:
        data['users'].append({
            'username': redditor,
            'top_neg_posts_and_comments': neg_posts
        })
        with open(file_name, 'w') as f:
            json.dump(data, f, indent=1)
            f.close()


def load_current_json(path):
    """
    Function loads data from json
    """

    with open(path, 'r') as f:
        return json.load(f)


def split_redditors(curr_redditors, reddit_accounts_df):
    """
    Splits the list of redditors in user database so that we can do parallel processing to speed up
    runtime
    """

    list_of_lists = []
    num_accounts = len(reddit_accounts_df.index)
    interval = math.floor(len(curr_redditors) / num_accounts)
    index = 0
    for i in range(num_accounts):
        if i < (num_accounts - 1):
            list_of_lists.append(curr_redditors[index:index + interval])
            index += interval
        else:
            list_of_lists.append(curr_redditors[index:])
    return list_of_lists


@ray.remote
def analyze_redditors(redditors, user_database_file, school_directory, current_json
                      , archives_db, new_ids_file
                      , school, date, accounts_db, account_index):
    """
    Function analyzes posts from each user in one of the split up list of users
    """

    user_db_conn = create_connection(user_database_file)
    use = hub.load('https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3')
    model_for_posts = load_model(POSTS_MODELS)

    # loop through every redditor in the list of redditors
    for redditor in redditors:
        last_checked = find_user(user_db_conn, redditor)[1]
        if math.floor(time.time()) > last_checked:

            reddit = praw.Reddit(
                client_id=accounts_db.iloc[account_index]['client_id'],
                client_secret=accounts_db.iloc[account_index]['client_secret'],
                user_agent=accounts_db.iloc[account_index]['user_agent'],
                username=accounts_db.iloc[account_index]['username'],
                password=accounts_db.iloc[account_index]['password'],
            )

            # instantiate redditor scraper object and scrape this redditor's posts and or comments
            this_redditor = LiveRedditorAnalysisPraw(reddit, redditor, last_checked)
            posts = this_redditor.extract_redditor_data_praw(posts=True, comments=False)
            # update the last time we checked this redditor in the Databases
            finished_running = math.floor(time.time())
            with user_db_conn:
                updated = False
                while not updated:
                    try:
                        update_user(user_db_conn, redditor, finished_running)
                        updated = True
                    except Exception:
                        time.sleep(1)

            # if list of posts from this redditor is not empty then proceed with analyzing them
            if posts:
                posts = make_sure_text_is_in_correct_encoding_posts(posts)

                # encode the posts
                post_embeddings = []
                for post in posts:
                    try:
                        full_string = post[0] + ' ' + post[1]
                    except Exception:
                        full_string = post[1]
                    emb = use(full_string)
                    post_emb = tf.reshape(emb, [-1]).numpy()
                    post_embeddings.append(post_emb)
                post_embeddings = np.array(post_embeddings)

                # make a prediction for each post
                neg_post = []
                index = 0
                while index < len(post_embeddings):
                    prediction = model_for_posts.predict(post_embeddings[index:index + 1])
                    if np.argmax(prediction) == 0:
                        score = np.amax(prediction)
                        # only flag the posts that are negative scores of 0.97 and higher
                        if score >= .97:
                            # list contains the type, title, post, post id, date posted, subreddit, url, and score
                            try:
                                neg_post.append(
                                    ['Post', posts[index][0], posts[index][1], posts[index][2], posts[index][3]
                                        , posts[index][4], posts[index][5], str(math.floor(score * 100))])
                            except Exception:
                                pass
                    index += 1

                # if the redditor had negative post(s) proceed with json functions and add new post(s) to new_ids file
                # so that we can mark them as new in the pdf
                if neg_post:
                    added = False
                    while not added:
                        try:
                            with open(new_ids_file, 'a+') as f:
                                for post in neg_post:
                                    f.write(post[3] + '\n')
                                f.close()
                            added = True
                        except Exception:
                            time.sleep(2)

                    archives_conn = create_connection_archives(archives_db)
                    with archives_conn:
                        update_author_flagged_value(archives_conn, redditor)

                    if os.path.isfile(current_json):
                        update_json(current_json, redditor, neg_post)
                    else:
                        write_base_json(current_json, school, date)
                        update_json(current_json, redditor, neg_post)


def analyze_redditor_posts_and_comments(user_database_file, school, school_directory
                                        , archives_db, current_json, date, new_ids_file):
    """
    Function
    :param user_database_file: Databases with redditors from this school
    :param school: the school we are monitoring
    :param school_directory:
    :param archives_db:
    :param current_json:
    :param date:
    :param new_ids_file:
    """

    # get list of redditors from this institution from user Database
    user_db_conn = create_connection(user_database_file)
    with user_db_conn:
        curr_redditors = []
        while not curr_redditors:
            try:
                curr_redditors = list_users(user_db_conn)
            except Exception:
                time.sleep(1)

    if not os.path.isfile(archives_db):
        archives_conn = create_connection_archives(archives_db)
        with archives_conn:
            create_archives_db(archives_conn)

    reddit_accounts = RELEVANT + 'reddit_accounts.csv'
    accounts_df = pd.read_csv(reddit_accounts)
    redditors = list(split_redditors(curr_redditors, accounts_df))
    ray.init()
    function_calls = [analyze_redditors.remote(redditors[account_index], user_database_file, school_directory
                                               , current_json, archives_db, new_ids_file
                                               , school, date, accounts_df, account_index) for account_index in
                      range(len(redditors))]
    ray.get(function_calls)
    ray.shutdown()


def monitor_school(school, university=True, college=True):
    """
    Function encapsulates all previous functions and classes and monitors a school's reddit activity
    """

    school_directory = UNIVERSITIES + school + '/'
    new_ids_file = school_directory + 'new_ids.txt'
    if not os.path.isdir(school_directory):
        os.mkdir(school_directory)
    all_time_list = school_directory + school + '_all_time_redditors.txt'
    user_database = school_directory + school + '_users.db'
    post_id_database = school_directory + school + '_post_ids.db'
    archives_db = school_directory + school + '_archives.db'
    last_checked_pushshift_path = school_directory + school + '_last_checked_pushshift.txt'
    last_checked_live_praw = school_directory + school + '_last_checked_praw.txt'

    admins = []
    with open(ADMINS, 'r') as f:
        lines = f.readlines()
        for line in lines:
            admins.append(line.replace('\n', ''))

    if not os.path.isfile(last_checked_pushshift_path):
        start_timestamp = get_subreddit_creation_date(school)
        build_initial_database(school, start_timestamp, user_database, all_time_list, last_checked_pushshift_path
                               , university, college, first_run=True)
    else:
        with open(last_checked_pushshift_path) as f1:
            last_checked = int(f1.readlines()[0])
            build_initial_database(school, last_checked, user_database, all_time_list, last_checked_pushshift_path
                                   , university, college, first_run=False)

    # define and make directory where we store the json files for this school
    jsons_directory = school_directory + school + '_jsons/'
    if not os.path.isdir(jsons_directory):
        os.mkdir(jsons_directory)

    # define and make directory for output pdfs for this school
    pdfs_directory = school_directory + school + '_pdfs/'
    if not os.path.isdir(pdfs_directory):
        os.mkdir(pdfs_directory)

    # get current month as a string and current day of the month as an int
    month = datetime.now().strftime('%B')
    day = datetime.today().day

    # define current directory for the json and pdf of this institution for this day
    current_json = jsons_directory + school + month + str(day) + '.json'
    current_pdf = pdfs_directory + school + month + str(day) + '.pdf'

    # how many flagged users are in a specific batch each time the system passes the json to pdf maker
    num_users_flagged = 0

    while True:

        # check if the month and day is still the same, if not, create the daily pdf for the day
        # then change month & day & json file
        # also set num_users_flagged to 0 because it is a new day
        check_month = datetime.now().strftime('%B')
        check_day = datetime.today().day
        if check_month != month:
            month = check_month
            day = check_day
            current_json = jsons_directory + school + month + str(day) + '.json'
            current_pdf = pdfs_directory + school + month + str(day) + '.pdf'
            num_users_flagged = 0
        if check_month == month and check_day > day:
            day = check_day
            current_json = jsons_directory + school + month + str(day) + '.json'
            current_pdf = pdfs_directory + school + month + str(day) + '.pdf'
            num_users_flagged = 0

        date = month + ' ' + str(day)

        analyze_redditor_posts_and_comments(user_database, school, school_directory
                                            , archives_db, current_json, date, new_ids_file)
        if os.path.isfile(current_json):
            if os.path.isfile(new_ids_file):
                curr_data = load_current_json(current_json)
                report = CreateDailyPDF(curr_data, school, current_pdf, archives_db, num_users_flagged
                                        , new_ids_file)
                num_users_flagged = report.make_pdf()
                os.remove(new_ids_file)
                notification = NotificationSMS()
                notification.send_admin_ms(admins)
        build_redditor_database(school, user_database, post_id_database, all_time_list, last_checked_live_praw
                                , university, college)
