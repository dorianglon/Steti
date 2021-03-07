import os
import pandas as pd
from ScrapingTools.Scraping import ScrapeRedditorData
import time


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


def user_at_uni(redditor_username, subreddit_of_institution):
    """
    Function makes sure that redditor goes to the institution in question
    :param redditor_username: redditor to check
    :param subreddit_of_institution: subreddit of institution
    """

    now = time.time()
    reddit_creation_unix = 1119657672

    # reads the csv file of university subreddits
    universities_df = pd.read_csv('/Users/dorianglon/Desktop/BPG_limited/colleges.csv', delimiter=',')
    U_subreddits = universities_df['subreddit'].tolist()
    # eliminates the institution we care about from list of university subreddits
    if subreddit_of_institution in U_subreddits:
        U_subreddits.remove(subreddit_of_institution)

    # extract all of the redditor's comments and posts
    file_name = redditor_username + '.txt'
    redditor_scraper = ScrapeRedditorData(redditor_username, reddit_creation_unix, file_name)
    redditor_scraper.extract_redditor_data(posts=True, comments=True)
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
        if curr_sub == subreddit_of_institution:
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

    # continue with the process if the user posts more on the institution's subreddit
    # check when the user's first post was on the institution's subreddit
    Mar_1_2017 = 1488391200
    first_post_on_sub = 2000000000
    for index, row in subs_df.iterrows():
        if row['subreddit'] == subreddit_of_institution:
            if row['date'] < first_post_on_sub:
                first_post_on_sub = row['date']

    # if first post on sub was before decision time for what would now be undergrad seniors
    if first_post_on_sub < Mar_1_2017:
        with open('/Users/dorianglon/Desktop/BPG_limited/college_grad_subs.txt', 'r') as f:
            grad_subs = f.readlines()
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
        with open('/Users/dorianglon/Desktop/BPG_limited/uni_admissions_subs.txt', 'r') as f:
            college_app_subs = f.readlines()
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
            for index, row in subs_df.itterows():
                if row['date'] >= after:
                    if row['subreddit'] in U_subreddits:
                        other_U_posts += 1
                    if row['subreddit'] == subreddit_of_institution:
                        institution_posts += 1
            if institution_posts > other_U_posts:
                return True
            elif other_U_posts > institution_posts:
                return False
