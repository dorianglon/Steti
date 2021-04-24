from Scraping import *


def get_posts_from_sub(subreddit, abbrev):
    date_created = get_subreddit_creation_date(subreddit)
    data = ScrapeSubreddit(subreddit, abbrev, date_created)
    data.extract_reddit_posts()


def get_comments_from_sub(subreddit, abbrev):
    date_created = get_subreddit_creation_date(subreddit)
    data = ScrapeSubreddit(subreddit, abbrev, 1400000000)
    data.extract_reddit_comments()


def main():

    subs = []

    for sub in subs:
        get_posts_from_sub(sub[0], sub[1])
        get_comments_from_sub(sub[0], sub[1])


if __name__ == '__main__':
    main()
