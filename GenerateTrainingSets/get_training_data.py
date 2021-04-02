from ScrapingTools.Scraping import *
import math


def get_neg_posts():
    """
    Function builds datasets from SuicideWatch
    """
    neg_sub = 'SuicideWatch'
    created = get_subreddit_creation_date(neg_sub)

    text_lengths = ['min', 'mid', 'max']
    for length in text_lengths:
        if length == 'min':
            neg_data = ScrapeSubreddit(neg_sub, 'sw', 1441475833, length)
            neg_data.extract_reddit_posts(neg=True, pos=False)
        else:
            neg_data = ScrapeSubreddit(neg_sub, 'sw', created, length)
            neg_data.extract_reddit_posts(neg=True, pos=False)


def get_line_count(f_name):
    with open(f_name, 'r') as f:
        _lines = f.readlines()
        count = 0
        for _line in _lines:
            count += 1
        return count


def get_pos_posts():
    """
    Function builds datasets from 'happy' subs
    """

    neg_min_path = '/Users/dorianglon/Desktop/Training_Sets/SuicideWatch_min_posts.txt'
    neg_mid_path = '/Users/dorianglon/Desktop/Training_Sets/SuicideWatch_mid_posts.txt'
    neg_max_path = '/Users/dorianglon/Desktop/Training_Sets/SuicideWatch_max_posts.txt'

    neg_min_length = get_line_count(neg_min_path)
    neg_mid_length = get_line_count(neg_mid_path)
    neg_max_length = get_line_count(neg_max_path)

    subs = [['askscience', 'as'], ['biology', 'bio'], ['boardgames', 'bg'], ['books', 'bks'], ['49ers', '49']
        , ['buildapc', 'bapc'], ['CasualConversation', 'cc'], ['classicalmusic', 'cm'], ['Coffee', 'cfe']
        , ['computers', 'comp'], ['Cooking', 'ckg'], ['dogs', 'dogs'], ['EatCheapAndHealthy', 'ecah']
        , ['history', 'hsty'], ['keto', 'kto'], ['legaladvice', 'la'], ['linguistics', 'lng'], ['MachineLearning', 'ml']
        , ['math', 'math'], ['nba', 'nba'], ['NoStupidQuestions', 'nsq'], ['personalfinance', 'pf']
        , ['physicaltherapy', 'pt'], ['PoliticalDiscussion', 'pd'], ['python', 'pton'], ['running', 'run']
        , ['Showerthoughts', 'st'], ['SkincareAddiction', 'sca'], ['stocks', 'stk'], ['Teachers', 'tchs']
        , ['tech', 'tech'], ['teslamotors', 'tm'], ['travel_posts', 'tp']]

    text_lengths = ['min', 'mid', 'max']

    max_min = math.floor(neg_min_length/len(subs))
    max_mid = math.floor(neg_mid_length/len(subs))
    max_max = math.floor(neg_max_length/len(subs))

    for sub in subs:
        created = get_subreddit_creation_date(sub[0])
        for length in text_lengths:
            if length == 'min':
                pos_data = ScrapeSubreddit(sub[0], sub[1], created, length)
                pos_data.extract_reddit_posts(neg=False, pos=True, max_length=max_min)
            elif length == 'mid':
                pos_data = ScrapeSubreddit(sub[0], sub[1], created, length)
                pos_data.extract_reddit_posts(neg=False, pos=True, max_length=max_mid)
            elif length == 'max':
                pos_data = ScrapeSubreddit(sub[0], sub[1], created, length)
                pos_data.extract_reddit_posts(neg=False, pos=True, max_length=max_max)


if __name__ == '__main__':
    get_neg_posts()
    # get_pos_posts()
