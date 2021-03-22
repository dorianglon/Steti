from ScrapingTools.Scraping import *
import time
import math
import os
import datetime
from database.userDb import *
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text
import numpy as np
import json


def check_for_new_uni_redditors(subreddit_of_U, path_to_database, all_time_list, subreddit_creation_timestamp,
                                university=True, college=True):
    """
    Function checks for new redditors from a subreddit every 5 minutes
    :param subreddit_of_U: subreddit for uni/college
    :param path_to_database: path to this subreddit's redditor database
    :param all_time_list:
    :param subreddit_creation_timestamp:
    :param university: boolean, true if university
    :param college: boolean, true if college
    """

    check_for_redditors = GetRedditorsFromSub(subreddit_of_U, subreddit_creation_timestamp, path_to_database, all_time_list)

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


def load_model(model_path):
    """
    Function loads our model
    """
    from tensorflow import keras
    return keras.models.load_model(model_path)


def make_sure_text_is_in_correct_encoding(list_of_text_objects):
    """
    Function makes sure text we analyze is in ascii encoding, if not it cleans it
    """
    index = 0
    while index < len(list_of_text_objects):
        text = list_of_text_objects[index][0].encode("ascii", "ignore")
        decoded_text = text.decode()
        list_of_text_objects[index][0] = decoded_text
    return list_of_text_objects


def write_base_json(file_name, institution, month, day):
    """
    Function makes new json file for a new day of analysis
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


def analyze_redditor_posts_and_comments(database_file, institution):
    """
    Function runs forever analyzing the contents from redditors of a certain institution
    """

    # get current month as a string and current day of the month as an int
    month = datetime.now().strftime('%B')
    day = datetime.datetime.today().day

    # define directory where we store the json files
    directory = '/Users/dorianglon/Desktop/BPG_limited/Universities-Colleges_jsons/'
    # define current directory for the json of this institution for this day
    current_json = directory + institution + month + str(day) + '.json'

    # loop forever
    while True:
        # check if the month and day is still the same, if not then change month & day & json file
        check_month = datetime.now().strftime('%B')
        check_day = datetime.datetime.today().day
        if check_month != month:
            month = check_month
            day = check_day
            current_json = directory + month + str(day) + '.json'
        if check_month == month and check_day > day:
            day = check_day
            current_json = directory + month + str(day) + '.json'

        # get list of redditors from this institution from database
        conn = create_connection(database_file)
        with conn:
            curr_redditors = list_users(conn)

        # loop through every redditor in the list of redditors
        for redditor in curr_redditors:
            last_checked = find_user(conn, redditor)[1]
            if time.time() > last_checked:

                # instantiate redditor scraper object and scrape this redditor's posts and or comments
                this_redditor = ScrapeRedditorData(redditor, last_checked)
                posts = this_redditor.extract_redditor_data(for_analysis=True, posts=True, comments=False)
                # update the last time we checked this redditor in the database
                finished_running = math.floor(time.time())
                with conn:
                    update_user(conn, redditor, finished_running)

                # if list of posts from this redditor is not empty then proceed with analyzing them
                if posts:
                    posts = make_sure_text_is_in_correct_encoding(posts)
                    use = hub.load('https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3')
                    model = load_model('/Users/dorianglon/Desktop/BPG_limited/TRAINED_SUICIDE_&_DEPRESSION_NEW')

                    # encode the posts
                    post_embeddings = []
                    for post in posts:
                        emb = use(post[0])
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
                                neg_posts.append([posts[index][0], posts[index][1], posts[index][2], score])
                        index += 1

                    # if the redditor had negative post proceed with json functions
                    if neg_posts:
                        if os.path.isfile(current_json):
                            update_json(current_json, redditor, neg_posts)
                        else:
                            write_base_json(current_json, institution, month, day)
                            update_json(current_json, redditor, neg_posts)