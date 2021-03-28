from ScrapingTools.Scraping import *
import time
import math
import os
import datetime
from database.userDb import *
from database.postidDB import *
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text
import numpy as np
import json
from tqdm import tqdm
import praw
from multiprocessing import Process
from reportGeneration.pdf_generator import *


def build_initial_database(subreddit_of_U, path_to_user_database, all_time_list, subreddit_creation_timestamp,
                           university=True, college=True):
    """
    Function builds the founding database of redditors for a specific school
    :param subreddit_of_U: subreddit of university we are monitoring
    :param path_to_user_database: path to redditor database for this school
    :param all_time_list: path to list with all posters and commenters on the school's subreddit
    :param subreddit_creation_timestamp: when the subreddit was created
    :param university: (True if this is a university) vice versa
    :param college: (True if this is a college) vice versa
    """

    conn = create_connection(path_to_user_database)
    with conn:
        create_db(conn)
    redditors = GetRedditorsFromSub(subreddit_of_U, subreddit_creation_timestamp, path_to_user_database
                                    , all_time_list)
    redditors.extract_uni_redditors(university, college)


def build_redditor_database(subreddit_of_U, path_to_user_database, path_to_post_database, all_time_list,
                            university=True, college=True):
    """
    Function works with Scraping classes to build and maintain an up to date database of redditors from the university/
    college we are monitoring
    :param subreddit_of_U: subreddit for university/college
    :param path_to_user_database: path to database with users
    :param path_to_post_database: path to database with post ids from the subreddit
    :param all_time_list: path to text file which holds every redditor to ever post on the subreddit
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
        username="bpglimitedd",
        password="bpgpassword",
    )

    # check if database with post ids exists, if not create it
    if not os.path.isfile(path_to_post_database):
        conn2 = create_connection_post(path_to_post_database)
        with conn2:
            create_post_db(conn2)

    # loop forever, checks for new posts in the institution's subreddit and checks for new comments in old posts
    # adds new authors from institution to database as it finds them
    while True:
        check_for_redditors = GetRedditorsFromSub(subreddit_of_U, latest_post, path_to_user_database, all_time_list)

        try:
            post_id_conn = create_connection_post(path_to_post_database)
            with post_id_conn:
                post_ids = list_post_ids(post_id_conn)
                if len(post_ids) >= 200:
                    first_200 = post_ids[:200]
                    check_for_redditors.extract_redditors_from_post_ids(reddit, first_200, post_id_conn, university,
                                                                        college)
                elif len(post_ids) < 200 and len(post_ids) != 0:
                    check_for_redditors.extract_redditors_from_post_ids(reddit, post_ids, post_id_conn, university,
                                                                        college)
        except Exception:
            pass

        try:
            latest_post = check_for_redditors.extract_uni_redditors_live_(reddit, path_to_post_database, university,
                                                                          college)
        except Exception:
            pass

        time.sleep(420)


def load_model(model_path):
    """
    Function loads our model
    :param model_path: path to model
    """
    from tensorflow import keras
    return keras.models.load_model(model_path)


def make_sure_text_is_in_correct_encoding(list_of_text_objects):
    """
    Function makes sure text we analyze is in ascii encoding, if not it cleans it
    :param list_of_text_objects: list of posts to check
    """

    index = 0
    while index < len(list_of_text_objects):
        text = list_of_text_objects[index][0].encode("ascii", "ignore")
        decoded_text = text.decode()
        list_of_text_objects[index][0] = decoded_text
        index += 1
    return list_of_text_objects


def write_base_json(file_name, institution, month, day):
    """
    Function makes new json file for a new day of analysis
    :param file_name: json file path
    :param institution: school we are monitoring
    :param month: current month
    :param day: current day
    """

    initial_dic = {
        'institution': institution,
        'month': month,
        'day': day,
        'users': []
    }

    with open(file_name, 'w') as f:
        json.dump(initial_dic, f, indent=1)
        f.close()


def update_json(file_name, redditor, neg_posts):
    """
    Function adds new negative posts to the daily json for a specific redditor. If redditor is already in json it just updates
    the negative posts. If redditor is not present then it adds him to json.
    :param file_name: json file path
    :param redditor: redditor we are updating json for
    :param neg_posts: list of negative posts from this redditor
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
                user.get('top_neg_posts').append(neg_posts)
                with open(file_name, 'w') as f:
                    json.dump(data, f, indent=1)
                    f.close()
        # if user isn't in json then add him and his posts
        if not user_present:
            data['users'].append({
                'username': redditor,
                'top_neg_posts': neg_posts
            })
            with open(file_name, 'w') as f:
                json.dump(data, f, indent=1)
                f.close()
    # if list of users is empty then add this redditor as the first one on that list
    else:
        data['users'].append({
            'username': redditor,
            'top_neg_posts': neg_posts
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


def analyze_redditor_posts_and_comments(user_database_file, institution, main_directory):
    """
    Function runs forever analyzing the contents from redditors of a certain institution
    :param user_database_file: database with redditors from this school
    :param institution: the school we are monitoring
    :param main_directory: directory with all BPG files
    """

    # get current month as a string and current day of the month as an int
    month = datetime.datetime.now().strftime('%B')
    day = datetime.datetime.today().day

    # define and make directory where we store the json files for this school
    jsons_directory = main_directory + institution + '_jsons/'
    os.mkdir(jsons_directory)

    # define and make directory for output pdfs for this school
    pdfs_directory = main_directory + institution + '_pdfs/'
    os.mkdir(pdfs_directory)

    # define current directory for the json of this institution for this day
    current_json = jsons_directory + institution + month + str(day) + '.json'

    use = hub.load('https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3')

    model_path = main_directory + 'TRAINED_SUICIDE_&_DEPRESSION_NEW'
    model = load_model(model_path)

    reddit = praw.Reddit(
        client_id="PYhBZnomUNnE9w",
        client_secret="qC3PhLNu3Uarls1MnyanVxa3cWDlTA",
        user_agent="BPGhelperv1",
        username="bpglimitedd",
        password="bpgpassword",
    )

    # loop forever
    while True:
        # check if the month and day is still the same, if not, create the daily pdf for the day
        # then change month & day & json file
        check_month = datetime.datetime.now().strftime('%B')
        check_day = datetime.datetime.today().day
        if check_month != month:
            curr_data = load_current_json(current_json)
            out_file = pdfs_directory + institution + month + str(day) + '.pdf'
            report = CreateDailyPDF(curr_data, institution, out_file, main_directory)
            report.make_pdf()
            month = check_month
            day = check_day
            current_json = jsons_directory + month + str(day) + '.json'
        if check_month == month and check_day > day:
            curr_data = load_current_json(current_json)
            out_file = jsons_directory + institution + month + str(day) + '.pdf'
            report = CreateDailyPDF(curr_data, institution, out_file, main_directory)
            report.make_pdf()
            day = check_day
            current_json = jsons_directory + month + str(day) + '.json'

        # get list of redditors from this institution from database
        conn = create_connection(user_database_file)
        with conn:
            curr_redditors = []
            while not curr_redditors:
                try:
                    curr_redditors = list_users(conn)
                except Exception:
                    time.sleep(1)

        # loop through every redditor in the list of redditors
        for redditor in tqdm(curr_redditors):
            last_checked = find_user(conn, redditor)[1]
            if math.floor(time.time()) > last_checked:

                # instantiate redditor scraper object and scrape this redditor's posts and or comments
                this_redditor = LiveRedditorAnalysisPraw(reddit, redditor, last_checked)
                posts = this_redditor.extract_redditor_data_praw(posts=True, comments=False)
                # update the last time we checked this redditor in the database
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
                if posts is not None:
                    posts = make_sure_text_is_in_correct_encoding(posts)

                    # encode the posts
                    post_embeddings = []
                    for post in posts:
                        emb = use(post[1])
                        post_emb = tf.reshape(emb, [-1]).numpy()
                        post_embeddings.append(post_emb)
                    post_embeddings = np.array(post_embeddings)

                    # make a prediction for each post
                    neg_posts = []
                    index = 0
                    while index < len(post_embeddings):
                        prediction = model.predict(post_embeddings[index:index + 1])
                        if np.argmax(prediction) == 0:
                            score = np.amax(prediction)
                            # only flag the posts that are negative scores of 0.9 and higher
                            if score > .9:
                                # list contains the post, date posted, subreddit, and score respectively
                                neg_posts.append([posts[index][0], posts[index][1], posts[index][2], posts[index][3],
                                                  str(math.floor(score * 100))])
                        index += 1

                    # if the redditor had negative post proceed with json functions
                    if neg_posts:
                        if os.path.isfile(current_json):
                            update_json(current_json, redditor, neg_posts)
                        else:
                            write_base_json(current_json, institution, month, day)
                            update_json(current_json, redditor, neg_posts)


def monitor_school(school, university=True, college=True):
    """
    Function encapsulates all previous functions and classes and monitors a school's subreddit
    """

    main_directory = '/Users/dorianglon/Desktop/BPG_limited/'
    all_time_list = main_directory + school + '_all_time_redditors.txt'
    user_database = main_directory + school + '_users.db'
    post_id_database = main_directory + school + '_post_ids.db'
    start = get_subreddit_creation_date(school)

    build_initial_database(school, user_database, all_time_list, start, university, college)

    p1 = Process(target=build_redditor_database(school, user_database, post_id_database, all_time_list, start
                                                , university, college))
    p1.start()
    p2 = Process(target=analyze_redditor_posts_and_comments(user_database, school))
    p2.start()