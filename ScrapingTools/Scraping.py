import requests
import json
import os
import ftfy
import Alumn_HS_Detection
from tqdm import tqdm


class ScrapeSubreddit:
    """
    CLASS USED TO DOWNLOAD POSTS AND OR COMMENTS FROM A SPECIFIC SUBREDDIT
    """

    def __init__(self, subreddit, subreddit_abbrev, search_after):
        self.subreddit = subreddit
        self.subreddit_abbrev = subreddit_abbrev
        self.original_search_after = search_after
        self.search_after = search_after
        self.pushshift_url = 'http://api.pushshift.io/reddit'

    def fetch_objects(self, type, sort_type, sort, size):
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

        # print API query parameters
        print(params)

        # perform an API request
        r = requests.get(self.pushshift_url + '/' + type + '/search/', params=params, timeout=30)

        # check the status code, if successful,, process the data
        if r.status_code == 200:
            response = json.loads(r.text)
            data = response['data']
            sorted_data_by_id = sorted(data, key=lambda x: int(x['id'], 36))
            return sorted_data_by_id

    def extract_reddit_posts(self, sort_type='created_utc', sort='asc', size=1000):
        """
        Function scrapes the subreddit's posts and saves them in a text file.
        :param sort_type: default is asc
        :param sort: by date
        :param size: size of max return per request
        """
        # specifically the start timestamp
        max_id = 0

        # open a file for JSON output
        file_name = '/Users/dorianglon/Desktop/BPG_limited/' + self.subreddit + '_posts.txt'
        if not os.path.isfile(file_name):
            first = 'combined' + '\t' + 'subreddit\n'
            with open(file_name, 'a+') as file:
                file.write(first)
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
                                        output_string = new_text + '\t' + self.subreddit_abbrev + '\n'
                                        with open(file_name, 'a+') as file:
                                            file.write(output_string)
                                            file.close()
                                    else:
                                        title = object['title'].replace('\t', '') + ' '
                                        body = object['selftext'].replace('\t', '')
                                        new_text = title.replace('\n', '') + body.replace('\n', '')
                                        output_string = new_text + '\t' + self.subreddit_abbrev + '\n'
                                        with open(file_name, 'a+') as file:
                                            file.write(output_string)
                                            file.close()

                    # exit if nothing happened
                    if nothing_processed: return
                    self.search_after -= 1

    def extract_reddit_comments(self, sort_type='created_utc', sort='asc', size=1000):
        """
        Function scrapes the subreddit's comments and saves them in a text file.
        :param sort_type: default is asc
        :param sort: by date
        :param size: size of max return per request
        """
        # specifically the start timestamp
        max_id = 0

        # open a file for JSON output
        file_name = '/Users/dorianglon/Desktop/BPG_limited/' + self.subreddit + '_comments.txt'
        if not os.path.isfile(file_name):
            first = 'combined' + '\t' + 'subreddit\n'
            with open(file_name, 'a+') as file:
                file.write(first)
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
                                if object['body'] == '[removed]':
                                    continue
                                else:
                                    if len(object['body']) > 40:
                                        body = object['body'].replace('\t', '')
                                        new_text = body.replace('\n', '')
                                        output_string = new_text + '\t' + self.subreddit_abbrev + '\n'
                                        with open(file_name, 'a+') as file:
                                            file.write(output_string)
                                            file.close()

                    # exit if nothing happened
                    if nothing_processed: return
                    self.original_search_after -= 1


class GetRedditorsFromUSub:
    """
    CLASS USED TO COMPILE A LIST OF REDDITORS FROM A SPECIFIC UNIVERSITY SUBREDDIT AND CAN MAKE SURE THEY ACTUALLY GO TO
    THE UNIVERSITY STILL
    """

    def __init__(self, subreddit, search_after, save_to_file_for_U):
        self.subreddit = subreddit
        self.search_after = search_after
        self.file_name_for_U_redditors = save_to_file_for_U
        self.pushshift_url = 'http://api.pushshift.io/reddit'

    def fetch_posts(self, sort_type, sort, size):
        """
        **
        Function grabs submissions from a subreddit
        **
        :param sort_type: Default sorts by date
        :param sort: Default is asc
        :param size: maximum amount of posts requests returns. Default is 1000(max)
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
        print(params)

        # perform an API request
        r = requests.get(self.pushshift_url + '/submission/search/', params=params, timeout=30)

        # check the status code, if successful,, process the data
        if r.status_code == 200:
            response = json.loads(r.text)
            data = response['data']
            sorted_data_by_id = sorted(data, key=lambda x: int(x['id'], 36))
            return sorted_data_by_id

    def fetch_comments(self, submission_id, max_size=1000):
        """
        **
        Function  grabs all the comments from a particular post, specific to post id
        **
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

    def extract_redditors_from_sub(self, sort_type='created_utc', sort='asc', size=1000):
        """
        **
        Function grabs all of the redditors from a specific subreddit and stores the usernames into a file
        **
        :param sort_type: Default sorts by date
        :param sort: Default is asc
        :param size: maximum amount of posts requests returns. Default is 1000
        """
        redditors = []
        if os.path.isfile(self.file_name_for_U_redditors):
            with open(self.file_name_for_U_redditors, 'r') as f:
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
                objects = self.fetch_posts(sort_type=sort_type, sort=sort, size=size)

                # proceed if we have posts
                if objects is not None:
                    objects_not_full = False

                    # print how many submissions we have to extract from
                    count = 0
                    for object in objects:
                        count += 1
                    print(str(count) + ' submissions to extract comments from.')

                    # loop through the posts
                    for object in objects:
                        author = object['author']
                        # write post author to file
                        if author not in redditors and author != '[deleted]' and 'bot' not in author.lower():
                            redditors.append(author)
                            try:
                                check = Alumn_HS_Detection.user_at_uni(redditor_username=author
                                                                           , subreddit_of_institution=self.subreddit)
                                if check:
                                    with open(self.file_name_for_U_redditors, 'a+') as f:
                                        line = author + '\n'
                                        f.write(line)
                                        f.close()
                            except Exception as e:
                                print('Error : ', e)
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
                                comments = self.fetch_comments(object['id'])

                                # if we have comments then proceed
                                if comments is not None:
                                    comments_not_full = False

                                    # loop through comments
                                    for comment in tqdm(comments):
                                        comment_author = comment['author']
                                        if comment_author not in redditors and comment_author != '[deleted]' and 'bot' \
                                                not in comment_author.lower():
                                            redditors.append(comment_author)
                                            try:
                                                check = Alumn_HS_Detection.user_at_uni(redditor_username=
                                                                                           comment_author
                                                                                           , subreddit_of_institution=
                                                                                           self.subreddit)
                                                if check:
                                                    with open(self.file_name_for_U_redditors, 'a+') as f:
                                                        line = comment_author + '\n'
                                                        f.write(line)
                                                        f.close()
                                            except Exception as e:
                                                print('Error : ', e)

                    # exit if nothing happened
                    if nothing_processed: return
                    self.search_after -= 1

    def eliminate_repeats(self):
        """
        **
        Function just gets rid of repeats in our redditors file
        **
        """

        original_authors = []
        new_authors = []

        # open existing file with redditors
        with open(self.filename, 'r+') as file:
            lines = file.readlines()
            # stores original redditors into original_authors list
            for line in lines:
                original_authors.append(line)
            # empty file contents
            file.truncate(0)
            file.close()

        # loops through our list of redditors
        for author in original_authors:
            author = author.strip('\n')
            author = author.strip('\t')
            # stores authors in new list only once
            if author == '[deleted]' or author in new_authors:
                continue
            else:
                new_authors.append(author)

        # reopens same file and dumps the redditors into it
        with open(self.filename, 'a+') as write_file:
            for new_author in new_authors:
                write_file.write(new_author + '\n')


class ScrapeRedditorData:

    def __init__(self, redditor, search_after, save_to_file):
        self.redditor = redditor
        self.search_after = search_after
        self.original_search_after = search_after
        self.file_name = save_to_file
        self.pushshift_url = 'http://api.pushshift.io/reddit'

    def fetch_objects(self, type, sort_type, sort, size):
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

        # print API query parameters
        # print(params)

        # perform an API request
        r = requests.get(self.pushshift_url + '/' + type + '/search/', params=params, timeout=30)

        # check the status code, if successful,, process the data
        if r.status_code == 200:
            response = json.loads(r.text)
            data = response['data']
            sorted_data_by_id = sorted(data, key=lambda x: int(x['id'], 36))
            return sorted_data_by_id

    def check_file_content(self):
        """
        **
        Function checks if file with user data is empty. Deletes it if it is.
        **
        """

        # get the lines in file
        check_len = open(self.file_name, 'r')
        lines = check_len.readlines()
        total = 0
        for line in lines:
            total += 1

        # if the only line in file is the column names, then delete the file
        if total == 1:
            os.remove(self.file_name)

    def write_posts(self, sort_type, sort, size):
        """
        Function write the author's posts
        :param sort:
        :param sort_type:
        :param size: how much per requests
        """

        # specifically the start timestamp
        max_id = 0

        # write the opening line to file; which are the column titles
        with open(self.file_name, 'a+') as file:
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
                        id = int(object['id'], 36)
                        if id > max_id:
                            nothing_processed = False
                            created_utc = object['created_utc']
                            max_id = id
                            if created_utc > self.search_after:
                                self.search_after = created_utc
                            if 'selftext' not in object or 'is_self' not in object or 'stickied' not in object or \
                                    'subreddit' not in object or 'created_utc' not in object:
                                text = 'no text for post found\t'
                                to_write = text + object['subreddit'] + '\t' + str(object['created_utc'])
                                # write to file
                                with open(self.file_name, 'a+') as file:
                                    file.write(to_write)
                                    file.write('\n')
                            # check if the post is empty and that it is not a picture or video
                            elif object['is_self'] and len(object['selftext']) != 0 and not object['stickied']:
                                if object['selftext'] == '[removed]' or object['selftext'] == '[deleted]':
                                    text = 'no text for post found\t'
                                    to_write = text + object['subreddit'] + '\t' + str(object['created_utc'])
                                    # write to file
                                    with open(self.file_name, 'a+') as file:
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
                                        clean_to_write = ftfy.fix_text(to_write)
                                        # write to file
                                        with open(self.file_name, 'a+') as file:
                                            file.write(clean_to_write)
                                            file.write('\n')
                                            file.close()
                                    else:
                                        title = object['title'].replace('\t', '') + ' '
                                        body = object['selftext'].replace('\t', '')
                                        new_text = title.replace('\n', '') + body.replace('\n', '')
                                        to_write = new_text + '\t' + object['subreddit'] + '\t' + str(
                                            object['created_utc'])
                                        clean_to_write = ftfy.fix_text(to_write)
                                        # write to file
                                        with open(self.file_name, 'a+') as file:
                                            file.write(clean_to_write)
                                            file.write('\n')
                                            file.close()
                            else:
                                try:
                                    text = 'no text for post found\t'
                                    to_write = text + object['subreddit'] + '\t' + str(object['created_utc'])
                                    # write to file
                                    with open(self.file_name, 'a+') as file:
                                        file.write(to_write)
                                        file.write('\n')
                                except Exception as e:
                                    print('Error : ', e)

                    # exit if nothing happened
                    if nothing_processed: return
                    self.search_after -= 1

    def write_comments(self, sort_type, sort, size, both=False):
        """
        Function write the author's comments
        :param sort:
        :param sort_type:
        :param size: how much per requests
        :param both: to check if title is already written if we wrote posts before
        """

        max_id = 0

        if not both:
            # write the opening line to file; which are the column titles
            with open(self.file_name, 'a+') as file:
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
                        id = int(comment['id'], 36)
                        if id > max_id:
                            nothing_processed = False
                            created_utc = comment['created_utc']
                            max_id = id
                            if created_utc > self.original_search_after:
                                self.original_search_after = created_utc
                            if 'body' not in comment or 'subreddit' not in comment or 'created_utc' not in comment:
                                text = 'no text for comment found\t'
                                to_write = text + comment['subreddit'] + '\t' + str(comment['created_utc'])
                                # write to file
                                with open(self.file_name, 'a+') as file:
                                    file.write(to_write)
                                    file.write('\n')
                            # check if the post is empty and that it is not a picture or video
                            else:
                                # take out all newline and tabs
                                text = comment['body'].replace('\t', '')
                                new_text = text.replace('\n', '')
                                # concatenate post content, subreddit posted on, and date posted on
                                to_write_comment = new_text + '\t' + comment['subreddit'] + '\t' + str(
                                    comment['created_utc'])
                                # write to file
                                with open(self.file_name, 'a+') as file:
                                    file.write(to_write_comment)
                                    file.write('\n')

                    # exit if nothing happened
                    if nothing_processed: return
                    self.original_search_after -= 1

    def extract_redditor_data(self, sort_type='created_utc', sort='asc', size=1000, posts=True, comments=True):
        """
        **
        Function gets posts and comments(if requested) from a specific reddit user and stores the data into files
        **
        :param sort:
        :param sort_type:
        :param size: maximum amount of returned posts/comments per request. Default is 1000
        :param posts: are we scraping posts? Default is True
        :param comments: are we scraping comments? Default is True
        """

        if posts and comments:
            self.write_posts(sort_type, sort, size)
            self.write_comments(sort_type, sort, size, both=True)
            # self.check_file_content()
        elif posts and not comments:
            self.write_posts(sort_type, sort, size)
            self.check_file_content()
        elif comments and not posts:
            self.write_comments(sort_type, sort, size)
            self.check_file_content()


def main():
    file_name = '/Users/dorianglon/Desktop/BPG_limited/Cornellians.txt'
    Cornell = GetRedditorsFromUSub('Cornell', 1491792582, file_name)
    Cornell.extract_redditors_from_sub()


if __name__ == '__main__':
    main()