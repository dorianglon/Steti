import requests
import json
from tqdm import tqdm
import os
import pandas as pd
import time
from Databases.userDb import *
from Databases.postidDB import *
import math
from Shared_Resources.resources import *


class ScrapeSubreddit:
    """
    CLASS USED TO DOWNLOAD POSTS AND OR COMMENTS FROM A SPECIFIC SUBREDDIT
    JUST USED FOR OBTAINING DATA TO TRAIN MODEL
    """

    def __init__(self, subreddit, subreddit_abbrev, search_after):
        self.subreddit = subreddit
        self.subreddit_abbrev = subreddit_abbrev
        self.original_search_after = search_after
        self.search_after = search_after
        self.pushshift_url = PUSHSHIFT

    def fetch_objects(self, type, sort_type, sort, size):
        """
        Function gets posts or comments from subreddit of choice, orders them by id
        :param type: either reddit submissions or comments, (type=submission || type=comments)
        :param sort_type: Default sorts by date
        :param sort: Default is asc
        :param size: maximum amount of objects request returns. Default is 100(max)
        :return: list of posts or comments from subreddit
        """

        # default parameters for API query
        if type == 'submission':
            params = {
                'sort_type': sort_type,
                'sort': sort,
                'size': size,
                'subreddit': self.subreddit,
                'after': self.search_after
            }
        elif type == 'comment':
            params = {
                'sort_type': sort_type,
                'sort': sort,
                'size': size,
                'subreddit': self.subreddit,
                'after': self.original_search_after
            }

        # perform an API request
        r = requests.get(self.pushshift_url + '/' + type + '/search/', params=params, timeout=120)

        # check the status code, if successful,, process the data
        if r.status_code == 200:
            print(params)
            response = json.loads(r.text)
            data = response['data']
            sorted_data_by_id = sorted(data, key=lambda x: int(x['id'], 36))
            return sorted_data_by_id

    def extract_reddit_posts(self, sort_type='created_utc', sort='asc', size=100):
        """
        Function scrapes the subreddit's posts and saves them in a text file.
        :param sort_type: default is asc
        :param sort: by date
        :param size: size of max return per request
        """

        max_id = 0

        # open a file for output
        file_name = '/Users/dorianglon/Desktop/Steti_Tech/Data/' + self.subreddit + '_posts.txt'
        if not os.path.isfile(file_name):
            with open(file_name, 'a+') as file:
                file.write('combined' + '\t' + 'subreddit\n')
                file.close()

        while 1:
            nothing_processed = True
            objects_not_full = True
            while objects_not_full:
                objects = self.fetch_objects(type='submission', sort_type=sort_type, sort=sort, size=size)
                if objects is not None:
                    objects_not_full = False
                    # loop the returned data, ordered by date
                    for object in objects:
                        id = int(object['id'], 36)
                        if id > max_id:
                            nothing_processed = False
                            created_utc = object['created_utc']
                            max_id = id
                            if created_utc > self.search_after:
                                self.search_after = created_utc
                            if 'selftext' not in object or 'is_self' not in object or 'stickied' not in object:
                                continue
                            # check if the post is empty and that it is not a picture or video
                            elif object['is_self'] and len(object['selftext']) != 0 and not object['stickied']:
                                if object['selftext'] == '[removed]' or object['selftext'] == '[deleted]':
                                    continue
                                else:
                                    # if len(object['selftext']) > 40:
                                    if object['title'] == 0:
                                        text = object['selftext'].replace('\t', '')
                                        new_text = text.replace('\n', '')
                                        with open(file_name, 'a+') as file:
                                            file.write(new_text + '\t' + self.subreddit_abbrev + '\n')
                                            file.close()
                                    else:
                                        title = object['title'].replace('\t', '') + ' '
                                        body = object['selftext'].replace('\t', '')
                                        new_text = title.replace('\n', '') + body.replace('\n', '')
                                        with open(file_name, 'a+') as file:
                                            file.write(new_text + '\t' + self.subreddit_abbrev + '\n')
                                            file.close()

                    # exit if nothing happened
                    if nothing_processed: return
                    self.search_after -= 1

    def extract_reddit_comments(self, sort_type='created_utc', sort='asc', size=100):
        """
        Function scrapes the subreddit's comments and saves them in a text file.
        :param sort_type: default is asc
        :param sort: by date
        :param size: size of max return per request
        """

        max_id = 0

        # open a file for output
        file_name = '/Users/dorianglon/Desktop/Steti_Tech/Data/' + self.subreddit + '_comments.txt'
        if not os.path.isfile(file_name):
            with open(file_name, 'a+') as file:
                file.write('combined' + '\t' + 'subreddit\n')
                file.close()
        # while loop for recursive function
        while 1:

            nothing_processed = True
            objects_not_full = True
            while objects_not_full:
                objects = self.fetch_objects(type='comment', sort_type=sort_type, sort=sort, size=size)
                if objects is not None:
                    objects_not_full = False
                    # loop the returned data, ordered by date
                    for object in objects:
                        id = int(object['id'], 36)
                        if id > max_id:
                            nothing_processed = False
                            created_utc = object['created_utc']
                            max_id = id
                            if created_utc > self.original_search_after:
                                self.original_search_after = created_utc
                            if 'body' not in object:
                                continue
                            # check if the post is empty and that it is not a picture or video
                            elif len(object['body']) != 0:
                                if object['body'] == '[removed]' or object['body'] == '[deleted]':
                                    continue
                                else:
                                    body = object['body'].replace('\t', '')
                                    new_text = body.replace('\n', '')
                                    with open(file_name, 'a+') as file:
                                        file.write(new_text + '\t' + self.subreddit_abbrev + '\n')
                                        file.close()

                    # exit if nothing happened
                    if nothing_processed: return
                    self.original_search_after -= 1


class GetRedditorsFromSub:
    """
    CLASS USED TO COMPILE A DATABASE OF REDDITORS, OR INTERACT WITH IT, FROM A SPECIFIC UNIVERSITY/COLLEGE
    """

    def __init__(self, subreddit, search_after, user_database, all_time_list):
        """
        Provide instance with the school's sub, a starting unix timestamp, database file to store redditors,
        text file to store every redditor program comes across, and a file with names of reddit bots so we skip over
        them.
        """
        self.subreddit = subreddit
        self.search_after = search_after
        self.user_database = user_database
        self.all_time_list = all_time_list
        self.bots_file = BOTS
        self.pushshift_url = PUSHSHIFT

    def fetch_posts(self, sort_type, sort, size, last_checked_f):
        """
        Function grabs submissions from a subreddit
        :param sort_type: Default sorts by date
        :param sort: Default is asc
        :param size: maximum amount of posts per request. Default is 100(max)
        :param last_checked_f: file where value for last time checked is stored
        :return: list of posts from subreddit
        """

        # default parameters for API query
        params = {
            'sort_type': sort_type,
            'sort': sort,
            'size': size,
            'subreddit': self.subreddit,
            'after': self.search_after
        }

        if os.path.isfile(last_checked_f):
            os.remove(last_checked_f)

        with open(last_checked_f, 'a+') as f1:
            f1.write(str(self.search_after))

        # perform an API request
        r = requests.get(self.pushshift_url + '/submission/search/', params=params, timeout=30)

        # check the status code, if successful,, process the data
        if r.status_code == 200:
            print(params)
            response = json.loads(r.text)
            data = response['data']
            sorted_data_by_id = sorted(data, key=lambda x: int(x['id'], 36))
            return sorted_data_by_id

    def fetch_comments_by_id(self, submission_id, max_size=100):
        """
        Function  grabs all the comments from a particular post, specific to post id
        :param submission_id: post id to grab comments from
        :param max_size: maximum amount of comments to return
        :return: list of comments
        """

        # perform an API request
        r = requests.get(self.pushshift_url + '/' + 'comment/' + 'search/?link_id=' + submission_id + '&limit='
                         + str(max_size))
        if r.status_code == 200:
            response = json.loads(r.text)
            data = response['data']
            return data

    def extract_redditors_from_post_ids(self, reddit, post_ids, post_id_conn, university, college):
        """
        Function extracts new authors from new comments in a post if present.
        :param reddit: praw instance to work with
        :param post_ids: list of post ids
        :param post_id_conn: connection to Database with post ids
        :param university: (True if university)
        :param college: (True if college)
        """

        bots = []
        with open(self.bots_file, 'r') as f1:
            bots_ = f1.readlines()
            for bot in bots_:
                new_bot = bot.replace('\n', '')
                bots.append(new_bot)

        redditors = []
        if os.path.isfile(self.all_time_list):
            with open(self.all_time_list, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    new_line = line.replace('\n', '')
                    redditors.append(new_line)

        # loop through the post ids
        for id in post_ids:
            submission = reddit.submission(id=id)
            num_comments = submission.num_comments
            with post_id_conn:
                old_num_comments = find_post_id(post_id_conn, id)[1]
                # if there are more comments now compared to last time we checked then check the comments' authors
                if num_comments >= old_num_comments:
                    # update_post_id(post_id_conn, id, num_comments)
                    try:
                        submission.comments.replace_more(limit=None)
                        for comment in submission.comments.list():
                            if comment.author is not None:
                                comment_author = comment.author.name
                                if comment_author not in redditors and comment_author != '[deleted]' \
                                        and comment_author not in bots:
                                    redditors.append(comment_author)
                                    with open(self.all_time_list, 'a+') as f:
                                        f.write(comment_author + '\n')
                                        f.close()
                                    try:
                                        # check if this is a university subreddit then check if redditor from comment
                                        # goes to university. If they do then add them to list
                                        if university:
                                            check = redditor_at_uni(redditor=comment_author,
                                                                    subreddit_of_uni=self.subreddit)
                                            if check:
                                                user_db_conn = create_connection(self.user_database)
                                                with user_db_conn:
                                                    check = math.floor(time.time())
                                                    update_user(user_db_conn, comment_author, check)
                                        # instead if this is a community college subreddit then check if the redditor
                                        # from comment goes to college. If they do then add them to list
                                        elif college:
                                            check = redditor_at_cc(redditor=comment_author,
                                                                   subreddit_of_cc=self.subreddit)
                                            if check:
                                                user_db_conn = create_connection(self.user_database)
                                                with user_db_conn:
                                                    check = math.floor(time.time())
                                                    update_user(user_db_conn, comment_author, check)
                                    except Exception as e:
                                        print(e)
                    except Exception:
                        # pass because most likely a connection issue, doesn't affect big picture.
                        pass

    def extract_uni_redditors_live_(self, reddit, post_id_conn, university, college):
        """
        Function looks for new posts in the school's subreddit and adds new authors to Database
        :param reddit: praw instance that we are using
        :param post_id_conn: path to post_id Database
        :param university: (True if university)
        :param college: (True if college)
        """

        bots = []
        with open(self.bots_file, 'r') as f1:
            bots_ = f1.readlines()
            for bot in bots_:
                new_bot = bot.replace('\n', '')
                bots.append(new_bot)

        redditors = []
        if os.path.isfile(self.all_time_list):
            with open(self.all_time_list, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    new_line = line.replace('\n', '')
                    redditors.append(new_line)

        latest_post = self.search_after
        subreddit = reddit.subreddit(self.subreddit)
        for submission in subreddit.new(limit=None):
            if submission.created_utc > self.search_after:
                latest_post = submission.created_utc
                if submission.author is not None:
                    author = submission.author.name
                    if author not in redditors and author != '[deleted]' and author not in bots:
                        redditors.append(author)
                        with open(self.all_time_list, 'a+') as f:
                            line = author + '\n'
                            f.write(line)
                            f.close()
                        try:
                            # check if this is a university subreddit then check if redditor from post goes to
                            # university. If they do then add them to Databases
                            if university:
                                check = redditor_at_uni(redditor=author, subreddit_of_uni=self.subreddit)
                                if check:
                                    user_db_conn = create_connection(self.user_database)
                                    with user_db_conn:
                                        check = math.floor(time.time())
                                        update_user(user_db_conn, author, check)
                            # instead if this is a community college subreddit then check if the redditor from post
                            # goes to college. If they do then add them to list
                            elif college:
                                check = redditor_at_cc(redditor=author, subreddit_of_cc=self.subreddit)
                                if check:
                                    user_db_conn = create_connection(self.user_database)
                                    with user_db_conn:
                                        check = math.floor(time.time())
                                        update_user(user_db_conn, author, check)
                        except Exception:
                            pass
                    try:
                        submission.comments.replace_more(limit=None)
                        comments = submission.comments.list()
                        with post_id_conn:
                            update_post_id(post_id_conn, submission.id, len(comments))
                        for comment in comments:
                            if comment.author is not None:
                                comment_author = comment.author.name
                                if comment_author not in redditors and comment_author != '[deleted]' \
                                        and comment_author not in bots:
                                    redditors.append(comment_author)
                                    with open(self.all_time_list, 'a+') as f:
                                        line = comment_author + '\n'
                                        f.write(line)
                                        f.close()
                                    # check if this is a university subreddit then check if redditor from comment
                                    # goes to university. If they do then add them to list
                                    if university:
                                        check = redditor_at_uni(redditor=comment_author,
                                                                subreddit_of_uni=self.subreddit)
                                        if check:
                                            user_db_conn = create_connection(self.user_database)
                                            with user_db_conn:
                                                check = math.floor(time.time())
                                                update_user(user_db_conn, comment_author, check)
                                    # check if this is a community college subreddit then check if the redditor from
                                    # comment goes to college. If they do then add them to list
                                    elif college:
                                        check = redditor_at_cc(redditor=comment_author,
                                                               subreddit_of_cc=self.subreddit)
                                        if check:
                                            user_db_conn = create_connection(self.user_database)
                                            with user_db_conn:
                                                check = math.floor(time.time())
                                                update_user(user_db_conn, comment_author, check)
                    except Exception:
                        pass
            else:
                break
        return latest_post

    def extract_uni_redditors(self, last_checked_f, university, college, sort_type='created_utc',
                              sort='asc', size=100):
        """
        Function grabs redditors from University subreddit that it believes attend that University. This function
        is not for live use, it is to compile a list before live use.
        :param last_checked_f: path where we store timestamp of last time we scraped into past
        :param university: boolean value to denote if we are dealing with a university sub
        :param college: boolean value to denote if we are dealing with a community college sub
        :param sort_type: Default sorts by date
        :param sort: Default is asc
        :param size: maximum amount of posts requests returns. Default is 100
        """

        bots = []
        with open(self.bots_file, 'r') as f1:
            bots_ = f1.readlines()
            for bot in bots_:
                new_bot = bot.replace('\n', '')
                bots.append(new_bot)

        redditors = []

        if os.path.isfile(self.all_time_list):
            with open(self.all_time_list, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    new_line = line.replace('\n', '')
                    redditors.append(new_line)

        max_id = 0
        while 1:

            nothing_processed = True
            objects_not_full = True

            # loop as long as request is returning nothing
            while objects_not_full:
                objects = self.fetch_posts(sort_type=sort_type, sort=sort, size=size, last_checked_f=last_checked_f)

                # proceed if we have posts
                if objects is not None:
                    objects_not_full = False

                    # loop through the posts
                    for object in objects:
                        author = object['author']
                        # write post author to file
                        if author not in redditors and author != '[deleted]' and author not in bots:
                            redditors.append(author)
                            with open(self.all_time_list, 'a+') as f:
                                line = author + '\n'
                                f.write(line)
                                f.close()
                            try:
                                if university:
                                    # check if this is a university subreddit then check if redditor from post goes
                                    # to university. If they do then add them to list
                                    check = redditor_at_uni(redditor=author, subreddit_of_uni=self.subreddit)
                                    if check:
                                        conn = create_connection(self.user_database)
                                        with conn:
                                            _time = math.floor(time.time())
                                            update_user(conn, author, _time)
                                elif college:
                                    # instead if this is a community college subreddit then check if the redditor from
                                    # post goes to college. If they do then add them to list
                                    check = redditor_at_cc(redditor=author, subreddit_of_cc=self.subreddit)
                                    if check:
                                        conn = create_connection(self.user_database)
                                        with conn:
                                            _time = math.floor(time.time())
                                            update_user(conn, author, _time)
                            except Exception:
                                pass
                        id = int(object['id'], 36)
                        if id > max_id:
                            nothing_processed = False
                            created_utc = object['created_utc']
                            max_id = id
                            if created_utc > self.search_after:
                                self.search_after = created_utc
                            comments_not_full = True
                            # loop as long as request is returning nothing
                            while comments_not_full:
                                comments = self.fetch_comments_by_id(object['id'])

                                # if we have comments then proceed
                                if comments is not None:
                                    comments_not_full = False

                                    # loop through comments
                                    for comment in comments:
                                        comment_author = comment['author']
                                        if comment_author not in redditors and comment_author != '[deleted]' \
                                                and comment_author not in bots:
                                            redditors.append(comment_author)
                                            with open(self.all_time_list, 'a+') as f:
                                                line = comment_author + '\n'
                                                f.write(line)
                                                f.close()
                                            try:
                                                # check if this is a university subreddit then check if redditor from
                                                # comment goes to university. If they do then add them to list
                                                if university:
                                                    check = redditor_at_uni(redditor=comment_author,
                                                                            subreddit_of_uni=self.subreddit)
                                                    if check:
                                                        conn = create_connection(self.user_database)
                                                        with conn:
                                                            _time = math.floor(time.time())
                                                            update_user(conn, comment_author, _time)
                                                # instead if this is a community college subreddit then check if the
                                                # redditor from comment goes to college. If they do then add them to
                                                # list
                                                elif college:
                                                    check = redditor_at_cc(redditor=comment_author,
                                                                           subreddit_of_cc=self.subreddit)
                                                    if check:
                                                        conn = create_connection(self.user_database)
                                                        with conn:
                                                            _time = math.floor(time.time())
                                                            update_user(conn, comment_author, _time)
                                            except Exception:
                                                pass

                    # exit if nothing happened
                    if nothing_processed: return
                    self.search_after -= 1


class LiveRedditorAnalysisPraw:
    """
    CLASS USED TO LOOK FOR A REDDITOR'S NEW POSTS OR COMMENTS
    """

    def __init__(self, reddit, redditor, last_checked):
        self.reddit = reddit
        self.redditor = redditor
        self.last_checked = last_checked

    def get_latest_posts(self):
        """
        Function gets the author's latest posts
        """

        submissions = []
        try:
            for submission in self.reddit.redditor(self.redditor).submissions.new(limit=None):
                if submission.created_utc > self.last_checked:
                    if not submission.stickied and len(submission.selftext) > 0:
                        if submission.selftext != '[removed]':
                            submissions.append([submission.title, submission.selftext, submission.id
                                                , submission.created_utc - 14400, submission.subreddit.display_name
                                                , submission.url])
                else:
                    break
        except Exception:
            pass
        return submissions

    def get_latest_comments(self):
        """
        Function gets newest comments from a certain redditor
        """

        comments = []
        try:
            for comment in self.reddit.redditor(self.redditor).comments.new(limit=None):
                if comment.created_utc > self.last_checked:
                    if len(comment.body) > 0:
                        if comment.body != '[removed]':
                            comments.append([comment.body, comment.id, comment.created_utc - 14400
                                            , comment.subreddit.display_name])
                else:
                    break
        except Exception:
            pass
        return comments

    def extract_redditor_data_praw(self, posts=True, comments=True):
        """
        Function determines what we get from redditor
        """

        if posts and comments:
            posts = self.get_latest_posts()
            comments = self.get_latest_comments()
            return posts, comments
        elif posts and not comments:
            return self.get_latest_posts()
        elif comments and not posts:
            return self.get_latest_comments()


class ScrapeRedditorData:
    """
    CLASS USED TO SCRAPE A SPECIFIC REDDITOR'S POSTS, COMMENTS. USED IN DETERMINING IF A REDDITOR ATTENDS A CERTAIN
    UNIVERSITY OR COLLEGE
    """

    def __init__(self, redditor, search_after):
        self.redditor = redditor
        self.search_after = search_after
        self.original_search_after = search_after
        self.pushshift_url = PUSHSHIFT

    def fetch_objects(self, type, sort_type='created_utc', sort='asc', size=100):
        """
        Function gets posts or comments from subreddit of choice, orders them by id
        :param type: either reddit submissions or comments, (type=submission || type=comments)
        :param sort_type: Default sorts by date
        :param sort: Default is asc
        :param size: maximum amount of objects request returns. Default is 1000(max)
        :return: list of posts or comments from subreddit
        """
        # default parameters for API query
        if type == 'submission':
            params = {
                'sort_type': sort_type,
                'sort': sort,
                'size': size,
                'author': self.redditor,
                'after': self.search_after
            }
        elif type == 'comment':
            params = {
                'sort_type': sort_type,
                'sort': sort,
                'size': size,
                'author': self.redditor,
                'after': self.original_search_after
            }

        # perform an API request
        r = requests.get(self.pushshift_url + '/' + type + '/search/', params=params, timeout=30)

        # check the status code, if successful,, process the data
        if r.status_code == 200:
            response = json.loads(r.text)
            data = response['data']
            sorted_data_by_id = sorted(data, key=lambda x: int(x['id'], 36))
            return sorted_data_by_id

    def get_posts_to_determine_if_user_goes_to_U(self, sort_type, sort, size, file_name):
        """
        Function scrapes redditor's posts only for checking if redditor goes to the university we are scraping
        :param sort: default is asc
        :param sort_type: default is by date
        :param size: how much per requests
        :param file_name:
        because we are interested in the user's subreddit activity
        """

        # specifically the start timestamp
        max_id = 0
        # write the opening line to file; which are the column titles
        with open(file_name, 'a+') as file:
            line_one = 'text\tsubreddit\tdate\n'
            file.write(line_one)
            file.close()

        while 1:
            nothing_processed = True
            objects_not_full = True
            while objects_not_full:
                objects = self.fetch_objects(type='submission', sort_type=sort_type, sort=sort, size=size)
                if objects is not None:
                    objects_not_full = False
                    # loop the returned data, ordered by date
                    for object in objects:
                        try:
                            id = int(object['id'], 36)
                            if id > max_id:
                                nothing_processed = False
                                created_utc = object['created_utc']
                                max_id = id
                                if created_utc > self.search_after:
                                    self.search_after = created_utc

                                try:
                                    if 'selftext' not in object or 'is_self' not in object or 'stickied' not in object or \
                                            'subreddit' not in object or 'created_utc' not in object:
                                        text = 'no text for post found\t'
                                        to_write = text + object['subreddit'] + '\t' + str(object['created_utc'])
                                        # write to file
                                        with open(file_name, 'a+') as file:
                                            file.write(to_write)
                                            file.write('\n')
                                    # check if the post is empty and that it is not a picture or video
                                    elif object['is_self'] and len(object['selftext']) != 0 and not object['stickied']:
                                        if object['selftext'] == '[removed]' or object['selftext'] == '[deleted]':
                                            text = 'no text for post found\t'
                                            to_write = text + object['subreddit'] + '\t' + str(object['created_utc'])
                                            # write to file
                                            with open(file_name, 'a+') as file:
                                                file.write(to_write)
                                                file.write('\n')
                                        else:
                                            if object['title'] == 0:
                                                # take out all newline and tabs
                                                text = object['selftext'].replace('\t', '')
                                                new_text = text.replace('\n', '')
                                                # concatenate post content, subreddit posted on, and date posted on
                                                to_write = new_text + '\t' + object['subreddit'] + '\t' + str(
                                                    object['created_utc'])
                                                # write to file
                                                with open(file_name, 'a+') as file:
                                                    file.write(to_write)
                                                    file.write('\n')
                                                    file.close()
                                            else:
                                                title = object['title'].replace('\t', '') + ' '
                                                body = object['selftext'].replace('\t', '')
                                                new_text = title.replace('\n', '') + body.replace('\n', '')
                                                to_write = new_text + '\t' + object['subreddit'] + '\t' + str(
                                                    object['created_utc'])
                                                # write to file
                                                with open(file_name, 'a+') as file:
                                                    file.write(to_write)
                                                    file.write('\n')
                                                    file.close()
                                    else:
                                        try:
                                            text = 'no text for post found\t'
                                            to_write = text + object['subreddit'] + '\t' + str(object['created_utc'])
                                            # write to file
                                            with open(file_name, 'a+') as file:
                                                file.write(to_write)
                                                file.write('\n')
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                        except Exception:
                            pass

                    # exit if nothing happened
                    if nothing_processed: return
                    self.original_search_after -= 1

    def get_comments_to_determine_if_user_goes_to_U(self, sort_type, sort, size, file_name, both=False):
        """
        Function write the author's comments
        :param sort:
        :param sort_type:
        :param size: how much per requests
        :param file_name:
        :param both: to check if title is already written if we wrote posts before
        """

        max_id = 0

        if not both:
            # write the opening line to file; which are the column titles
            with open(file_name, 'a+') as file:
                line_one = 'text\tsubreddit\tdate\n'
                file.write(line_one)
                file.close()

        while 1:
            nothing_processed = True
            comments_not_full = True
            while comments_not_full:
                comments = self.fetch_objects(type='comment', sort_type=sort_type, sort=sort, size=size)
                if comments is not None:
                    comments_not_full = False
                    # loop the returned data, ordered by date
                    for comment in comments:
                        try:
                            id = int(comment['id'], 36)
                            if id > max_id:
                                nothing_processed = False
                                created_utc = comment['created_utc']
                                max_id = id

                                try:
                                    if created_utc > self.original_search_after:
                                        self.original_search_after = created_utc
                                    # check if the post is empty and that it is not a picture or video
                                    if 'body' not in comment or 'subreddit' not in comment or 'created_utc' not in \
                                            comment:
                                        text = 'no text for comment found\t'
                                        to_write = text + comment['subreddit'] + '\t' + str(comment['created_utc'])
                                        # write to file
                                        with open(file_name, 'a+') as file:
                                            file.write(to_write)
                                            file.write('\n')
                                    else:
                                        # take out all newline and tabs
                                        text = comment['body'].replace('\t', '')
                                        new_text = text.replace('\n', '')
                                        # concatenate post content, subreddit posted on, and date posted on
                                        to_write_comment = new_text + '\t' + comment['subreddit'] + '\t' + str(
                                            comment['created_utc'])
                                        # write to file
                                        with open(file_name, 'a+') as file:
                                            file.write(to_write_comment)
                                            file.write('\n')
                                except Exception:
                                    pass
                        except Exception:
                            pass

                    # exit if nothing happened
                    if nothing_processed: return
                    self.original_search_after -= 1

    def extract_redditor_data(self, file_name='', sort_type='created_utc', sort='asc', size=100
                              , posts=True, comments=True):

        if posts and comments:
            self.get_posts_to_determine_if_user_goes_to_U(sort_type, sort, size, file_name)
            self.get_comments_to_determine_if_user_goes_to_U(sort_type, sort, size, file_name, both=True)
        elif posts and not comments:
            self.get_posts_to_determine_if_user_goes_to_U(sort_type, sort, size, file_name)
        elif comments and not posts:
            self.get_comments_to_determine_if_user_goes_to_U(sort_type, sort, size, file_name)


def get_max_val_dict(dictionary):
    """
    Function gets the largest value in dictionary of universities as keys
    :param dictionary: dictionary operated on
    :return: largest value
    """

    max = 0
    for key in dictionary:
        if dictionary[key] > max:
            max = dictionary[key]
    return max


def redditor_at_uni(redditor, subreddit_of_uni):
    """
    Function makes a prediction regarding whether a redditor currently attends the university in question
    :param redditor: redditor to check
    :param subreddit_of_uni: subreddit of institution
    """

    now = time.time()
    reddit_creation_unix = 1119657672

    # reads the csv file of university subreddits
    universities_df = pd.read_csv(UNIVERSITYSUBS, delimiter=',')
    U_subreddits = universities_df['subreddit'].tolist()
    # eliminates the university we care about from list of university subreddits
    if subreddit_of_uni in U_subreddits:
        U_subreddits.remove(subreddit_of_uni)

    # extract all of the redditor's comments and posts
    file_name = redditor + '.txt'
    try:
        redditor_scraper = ScrapeRedditorData(redditor, reddit_creation_unix)
        redditor_scraper.extract_redditor_data(file_name=file_name, posts=True, comments=True)
    except Exception:
        pass

    author_df = pd.read_csv(file_name, delimiter='\t')
    os.remove(file_name)
    # creates a dataframe of the subreddits visited by redditor and the dates active
    subs_df = author_df[['subreddit', 'date']].copy()
    del author_df

    occurrences = 0
    dict_of_other_occurrences = dict()
    # counts how many times the redditor posts/comments in institution we care about compared to other universities
    for index, row in subs_df.iterrows():
        curr_sub = row['subreddit']
        if curr_sub == subreddit_of_uni:
            occurrences += 1
        if curr_sub in U_subreddits:
            if curr_sub in dict_of_other_occurrences:
                dict_of_other_occurrences[curr_sub] += 1
            else:
                dict_of_other_occurrences[curr_sub] = 1

    # if the redditor posts more on other university's subreddits then drop him
    other_school_posts = get_max_val_dict(dict_of_other_occurrences)
    if other_school_posts > occurrences:
        return False

    # continue with the process if the user posts more on the university's subreddit
    # check when the user's first post was on the university's subreddit
    Mar_1_2017 = 1488391200
    first_post_on_sub = 2000000000
    for index, row in subs_df.iterrows():
        if row['subreddit'] == subreddit_of_uni:
            if row['date'] < first_post_on_sub:
                first_post_on_sub = row['date']

    # if first post on sub was before decision time for what would now be undergrad seniors
    if first_post_on_sub < Mar_1_2017:
        grad_subs = []
        with open(GRADUATESUBS, 'r') as f:
            subs = f.readlines()
            for sub in subs:
                grad_subs.append(sub.replace('\n', ''))
        grad_student = False
        after = now - 31536000
        for index, row in subs_df.iterrows():
            if row['subreddit'] in grad_subs:
                if row['date'] > after:
                    grad_student = True
        # if the redditor's first post was before decision time 4 years ago and user has not posted on
        # gradschool subs within the last year than drop him, otherwise keep him
        if grad_student:
            return True
        elif not grad_student:
            return False

    # if first post was within decision time 4 years ago
    elif first_post_on_sub > Mar_1_2017:
        college_app_subs = []
        with open(ADMISSIONSUBS, 'r') as f:
            subs = f.readlines()
            for sub in subs:
                college_app_subs.append(sub.replace('\n', ''))
        Aug_1_2020 = 1596304800
        highschooler = False
        # check if posted on college applications sub since this August when school universities opened back up
        for index, row in subs_df.iterrows():
            if row['subreddit'] in college_app_subs:
                if row['date'] > Aug_1_2020:
                    highschooler = True
        # if the user has posted to admission subs within nearest university session then drop them
        if highschooler:
            return False
        # if user posted to admission subs prior to the date then check which uni was posted to the most
        # in the last year
        elif not highschooler:
            after = now - 31536000
            institution_posts = 0
            other_U_posts = 0
            for index, row in subs_df.iterrows():
                if row['date'] >= after:
                    if row['subreddit'] in U_subreddits:
                        other_U_posts += 1
                    if row['subreddit'] == subreddit_of_uni:
                        institution_posts += 1
            if institution_posts > other_U_posts:
                return True
            elif other_U_posts > institution_posts:
                return False


def redditor_at_cc(redditor, subreddit_of_cc):
    """
    Function makes a prediction regarding whether a redditor currently attends the college in question
    :param redditor: redditor to check
    :param subreddit_of_cc: subreddit of community college
    """
    now = time.time()
    reddit_creation_unix = 1119657672

    # reads the csv file of university subreddits
    universities_df = pd.read_csv(UNIVERSITYSUBS, delimiter=',')
    U_subreddits = universities_df['subreddit'].tolist()
    # eliminates the institution we care about from list of university subreddits
    if subreddit_of_cc in U_subreddits:
        U_subreddits.remove(subreddit_of_cc)

    # extract all of the redditor's comments and posts
    file_name = redditor + '.txt'
    try:
        redditor_scraper = ScrapeRedditorData(redditor, reddit_creation_unix)
        redditor_scraper.extract_redditor_data(file_name=file_name, posts=True, comments=True)
    except Exception:
        pass
    author_df = pd.read_csv(file_name, delimiter='\t')
    os.remove(file_name)
    # creates a dataframe of the subreddits visited by redditor and the dates active
    subs_df = author_df[['subreddit', 'date']].copy()
    del author_df

    occurrences = 0
    dict_of_other_occurrences = dict()
    # counts how many times the redditor posts/comments in college we care about compared to other universities
    for index, row in subs_df.iterrows():
        curr_sub = row['subreddit']
        if curr_sub == subreddit_of_cc:
            occurrences += 1
        if curr_sub in U_subreddits:
            if curr_sub in dict_of_other_occurrences:
                dict_of_other_occurrences[curr_sub] += 1
            else:
                dict_of_other_occurrences[curr_sub] = 1

    # if the redditor posts more on other college's subreddits then drop him
    other_school_posts = get_max_val_dict(dict_of_other_occurrences)
    if other_school_posts > occurrences:
        return False

    # continue with the process if the user posts more on the college's subreddit
    # check when the user's first post was on the college's subreddit
    Sept_23_2019 = 1569196800
    first_post_on_sub = 2000000000
    for index, row in subs_df.iterrows():
        if row['subreddit'] == subreddit_of_cc:
            if row['date'] < first_post_on_sub:
                first_post_on_sub = row['date']

    # if first post on sub was before start of fall quarter 2 years ago
    # then they probably transferred. So check to which institution they posted to the most
    # in the last year
    if first_post_on_sub < Sept_23_2019:
        after = now - 31536000
        institution_posts = 0
        other_U_posts = 0
        for index, row in subs_df.iterrows():
            if row['date'] >= after:
                if row['subreddit'] in U_subreddits:
                    other_U_posts += 1
                if row['subreddit'] == subreddit_of_cc:
                    institution_posts += 1
        if institution_posts > other_U_posts:
            return True
        elif other_U_posts > institution_posts:
            return False

    elif first_post_on_sub > Sept_23_2019:
        return True


def get_subreddit_creation_date(subreddit):
    """
    Function returns timestamp when subreddit was created
    """

    url = 'https://www.reddit.com/r/' + subreddit + '/about.json'
    while True:
        r = requests.get(url)
        if r.status_code == 200:
            data = json.loads(r.text)
            return int(data['data']['created_utc'])
        time.sleep(5)
