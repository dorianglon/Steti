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


def build_initial_database(subreddit_of_U, last_checked_f, path_to_user_database, all_time_list,
                           subreddit_creation_timestamp, bots_file, university=True, college=True, first_run=True):
    """
    Function builds the founding Databases of redditors for a specific school
    :param subreddit_of_U: subreddit of university we are monitoring
    :param last_checked_f: file containing last time we checked
    :param path_to_user_database: path to redditor Databases for this school
    :param all_time_list: path to list with all posters and commenters on the school's subreddit
    :param subreddit_creation_timestamp: when the subreddit was created
    :param bots_file: file containing known bots on reddit
    :param university: (True if this is a university) vice versa
    :param college: (True if this is a college) vice versa
    :param first_run: True if first time running for school
    """

    conn = create_connection(path_to_user_database)
    with conn:
        if first_run:
            create_db(conn)
    redditors = GetRedditorsFromSub(subreddit_of_U, subreddit_creation_timestamp, path_to_user_database
                                    , all_time_list, bots_file)
    redditors.extract_uni_redditors(last_checked_f, university, college)


def build_redditor_database(subreddit_of_U, path_to_user_database, path_to_post_database, all_time_list,
                            bots_file, university=True, college=True):
    """
    Function works with Scraping classes to build and maintain an up to date Databases of redditors from the university/
    college we are monitoring
    :param subreddit_of_U: subreddit for university/college
    :param path_to_user_database: path to Databases with users
    :param path_to_post_database: path to Databases with post ids from the subreddit
    :param all_time_list: path to text file which holds every redditor to ever post on the subreddit
    :param bots_file: file of reddit bots
    :param university: (True if this is a university) vice versa
    :param college: (True if this is a college) vice versa
    """

    # initial condition, get posts on sub from the last 6 hours
    latest_post = math.floor(time.time() - 21600)

    # create praw instance when working with new posts and comments
    reddit = praw.Reddit(
        client_id="PYhBZnomUNnE9w",
        client_secret="qC3PhLNu3Uarls1MnyanVxa3cWDlTA",
        user_agent="BPGhelperv1",
        username="BPGlimited",
        password="bpgpassword",
    )

    # check if Databases with post ids exists, if not create it
    if not os.path.isfile(path_to_post_database):
        conn2 = create_connection_post(path_to_post_database)
        with conn2:
            create_post_db(conn2)

    # adds new authors from institution to Databases as it finds them
    check_for_redditors = GetRedditorsFromSub(subreddit_of_U, latest_post, path_to_user_database, all_time_list,
                                              bots_file)

    try:
        post_id_conn = create_connection_post(path_to_post_database)
        with post_id_conn:
            post_ids = list_post_ids(post_id_conn)
            if len(post_ids) >= 200:
                first_200 = post_ids[:200]
                check_for_redditors.extract_redditors_from_post_ids(reddit, first_200, post_id_conn,
                                                                    university, college)
            elif len(post_ids) < 200 and len(post_ids) != 0:
                check_for_redditors.extract_redditors_from_post_ids(reddit, post_ids, post_id_conn,
                                                                    university, college)
    except Exception:
        pass

    try:
        latest_post = check_for_redditors.extract_uni_redditors_live_(reddit, path_to_post_database,
                                                                      university, college)
    except Exception:
        pass


def load_model(model_path):
    """
    Function loads our model
    :param model_path: path to model
    """
    from tensorflow import keras
    return keras.models.load_model(model_path)


def make_sure_text_is_in_correct_encoding_comments(comments):
    """
    Function makes sure comments we analyze is in ascii encoding, if not it cleans it
    :param comments: list of posts to check
    """

    index = 0
    while index < len(comments):
        text = comments[index][0].encode('ascii', 'ignore')
        decoded_text = text.decode()
        comments[index][0] = decoded_text
        index += 1
    return comments


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


def write_base_json(file_name, institution, date):
    """
    Function makes new json file for a new day of analysis
    :param file_name: json file path
    :param institution: school we are monitoring
    :param date:
    """

    initial_dic = {
        'institution': institution,
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


def week_of_month():
    """
    Returns the week of the month
    """

    n = datetime.now()
    cal = Calendar()
    weeks = cal.monthdayscalendar(n.year, n.month)
    for x in range(len(weeks)):
        if n.day in weeks[x]:
            return x + 1


def split_redditors(curr_redditors, reddit_accounts_df):
    final = []
    length = len(reddit_accounts_df.index)
    intervals = math.floor(len(curr_redditors) / length)
    index = 0
    for i in range(length):
        if i < (length - 1):
            final.append(curr_redditors[index:index + intervals])
            index += intervals
        else:
            final.append(curr_redditors[index:])

    return final


@ray.remote
def analyze_redditors(redditors, user_database_file, school_directory, current_json
                      , main_directory, archives_db, relevant_files_dir
                      , institution, date, accounts_db, i):
    conn = create_connection(user_database_file)
    use = hub.load('https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3')
    model_for_posts_path = main_directory + 'Models/Model_For_Posts'
    model_for_comments_path = main_directory + 'Models/Model_For_Comments'
    model_for_posts = load_model(model_for_posts_path)
    model_for_comments = load_model(model_for_comments_path)

    # loop through every redditor in the list of redditors
    for redditor in redditors:
        last_checked = find_user(conn, redditor)[1]
        if math.floor(time.time()) > last_checked:

            reddit = praw.Reddit(
                client_id=accounts_db.iloc[i]['client_id'],
                client_secret=accounts_db.iloc[i]['client_secret'],
                user_agent=accounts_db.iloc[i]['user_agent'],
                username=accounts_db.iloc[i]['username'],
                password=accounts_db.iloc[i]['password'],
            )

            # instantiate redditor scraper object and scrape this redditor's posts and or comments
            this_redditor = LiveRedditorAnalysisPraw(reddit, redditor, last_checked)
            posts, comments = this_redditor.extract_redditor_data_praw(posts=True, comments=True)
            # update the last time we checked this redditor in the Databases
            finished_running = math.floor(time.time())
            with conn:
                updated = False
                while not updated:
                    try:
                        update_user(conn, redditor, finished_running)
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
                        # only flag the posts that are negative scores of 0.9 and higher
                        if score > .92:
                            # list contains the post, date posted, subreddit, and score respectively
                            try:
                                neg_post.append(
                                    ['Post', posts[index][0], posts[index][1], posts[index][2], posts[index][3]
                                        , posts[index][4], str(math.floor(score * 100))])
                            except Exception:
                                pass
                    index += 1

                # if the redditor had negative post proceed with json functions
                if neg_post:
                    check_for_archives_path = school_directory + 'archives_exists.txt'
                    archives_conn = create_connection_archives(archives_db)
                    if not os.path.isfile(check_for_archives_path):
                        create_archives_db(archives_conn)
                        with open(check_for_archives_path, 'a+') as f:
                            f.write('exists')
                    with archives_conn:
                        update_author_flagged_value(archives_conn, redditor)

                    if os.path.isfile(current_json):
                        update_json(current_json, redditor, neg_post)
                    else:
                        write_base_json(current_json, institution, date)
                        update_json(current_json, redditor, neg_post)

            # if list of comments from this redditor is not empty then proceed with analyzing them
            if comments:
                comments = make_sure_text_is_in_correct_encoding_comments(comments)
                key_phrases_file = relevant_files_dir + 'key_phrases.txt'

                phrases = []
                with open(key_phrases_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.replace('\n', '')
                        phrases.append(line)

                comments_with_key = []
                for comment in comments:
                    for phrase in phrases:
                        if phrase in comment[0]:
                            comments_with_key.append(comment)

                # encode the comments
                comment_embeddings = []
                for comment in comments_with_key:
                    try:
                        emb = use(comment[0])
                        post_emb = tf.reshape(emb, [-1]).numpy()
                        comment_embeddings.append(post_emb)
                    except Exception:
                        pass
                comment_embeddings = np.array(comment_embeddings)

                # make a prediction for each post
                neg_comments = []
                index = 0
                while index < len(comment_embeddings):
                    prediction = model_for_comments.predict(comment_embeddings[index:index + 1])
                    if np.argmax(prediction) == 0:
                        score = np.amax(prediction)
                        # only flag the posts that are negative scores of 0.9 and higher
                        if score > .92:
                            # list contains the post, date posted, subreddit, and score respectively
                            try:
                                neg_comments.append(['Comment', comments_with_key[index][0], comments_with_key[index][1]
                                                        , comments_with_key[index][2], comments_with_key[index][3],
                                                     str(math.floor(score * 100))])
                            except Exception:
                                pass
                    index += 1

                # if the redditor had negative post proceed with json functions
                if neg_comments:
                    check_for_archives_path = school_directory + 'archives_exists.txt'
                    archives_conn = create_connection_archives(archives_db)
                    if not os.path.isfile(check_for_archives_path):
                        create_archives_db(archives_conn)
                        with open(check_for_archives_path, 'a+') as f:
                            f.write('exists')
                    with archives_conn:
                        update_author_flagged_value(archives_conn, redditor)

                    if os.path.isfile(current_json):
                        update_json(current_json, redditor, neg_comments)
                    else:
                        write_base_json(current_json, institution, date)
                        update_json(current_json, redditor, neg_comments)


def analyze_redditor_posts_and_comments(user_database_file, institution, school_directory, main_directory
                                        , archives_db, relevant_files_dir, current_json, date):
    """
    Function runs forever analyzing the contents from redditors of a certain institution
    :param user_database_file: Databases with redditors from this school
    :param institution: the school we are monitoring
    :param school_directory:
    :param main_directory: directory with all BPG files
    :param archives_db:
    :param relevant_files_dir:
    :param current_json:
    :param date
    """

    # get list of redditors from this institution from user Database
    conn = create_connection(user_database_file)
    with conn:
        curr_redditors = []
        while not curr_redditors:
            try:
                curr_redditors = list_users(conn)
            except Exception:
                time.sleep(1)

    reddit_accounts = relevant_files_dir + 'reddit_accounts.csv'
    accounts_df = pd.read_csv(reddit_accounts)
    redditors = list(split_redditors(curr_redditors, accounts_df))
    length = len(redditors)
    ray.init()
    function_calls = [analyze_redditors.remote(redditors[i], user_database_file, school_directory
                                               , current_json, main_directory, archives_db, relevant_files_dir
                                               , institution, date, accounts_df, i) for i in range(length)]
    ray.get(function_calls)
    ray.shutdown()


def monitor_school(school, university=True, college=True):
    """
    Function encapsulates all previous functions and classes and monitors a school's subreddit
    """

    main_directory = '/Users/dorianglon/Desktop/Steti_Tech/'
    relevant_files_dir = main_directory + 'Relevant_Files/'
    school_directory = main_directory + 'Universities&Colleges/' + school + '/'
    if not os.path.isdir(school_directory):
        os.mkdir(school_directory)
    all_time_list = school_directory + school + '_all_time_redditors.txt'
    user_database = school_directory + school + '_users.db'
    post_id_database = school_directory + school + '_post_ids.db'
    archives_db = school_directory + school + '_archives.db'
    last_checked_path = school_directory + school + '_last_checked.txt'
    bots_file = relevant_files_dir + 'bots.txt'

    if not os.path.isfile(last_checked_path):
        start = get_subreddit_creation_date(school)
        build_initial_database(school, last_checked_path, user_database, all_time_list, start, bots_file,
                               university, college, first_run=True)
    else:
        with open(last_checked_path) as f1:
            last_checked = int(f1.readlines()[0])
            build_initial_database(school, last_checked_path, user_database, all_time_list, last_checked, bots_file
                                   , university, college, first_run=False)

    # get current month as a string and current day of the month as an int
    month = datetime.now().strftime('%B')
    day = datetime.today().day

    # how many flagged users are in a specific batch each time the system passes the json to pdf maker
    num_users_flagged = 0

    while True:

        date = month + ' ' + str(day)

        # define and make directory where we store the json files for this school if not already made
        jsons_directory = school_directory + school + '_jsons/'
        if not os.path.isdir(jsons_directory):
            os.mkdir(jsons_directory)

        # define and make directory for output pdfs for this school if not already made
        pdfs_directory = school_directory + school + '_pdfs/'
        if not os.path.isdir(pdfs_directory):
            os.mkdir(pdfs_directory)

        # define current directory for the json of this institution for this day
        current_json = jsons_directory + school + month + str(day) + '.json'
        out_file = pdfs_directory + school + month + str(day) + '.pdf'

        # check if the month and day is still the same, if not, create the daily pdf for the day
        # then change month & day & json file
        # also set num_users_flagged to 0 because it is a new day
        check_month = datetime.now().strftime('%B')
        check_day = datetime.today().day
        if check_month != month:
            month = check_month
            day = check_day
            current_json = jsons_directory + month + str(day) + '.json'
            num_users_flagged = 0
        if check_month == month and check_day > day:
            day = check_day
            current_json = jsons_directory + month + str(day) + '.json'
            num_users_flagged = 0

        analyze_redditor_posts_and_comments(user_database, school, school_directory, main_directory
                                            , archives_db, relevant_files_dir, current_json, date)
        curr_data = load_current_json(current_json)
        report = CreateDailyPDF(curr_data, school, out_file, main_directory, archives_db, num_users_flagged)
        num_users_flagged = report.make_pdf()
        build_redditor_database(school, user_database, post_id_database, all_time_list, bots_file, university, college)
