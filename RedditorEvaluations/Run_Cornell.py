from Run_4_Ever import *
import datetime


def main():
    # all_time_list = '/Users/dorianglon/Desktop/BPG_limited/Cornellians_full_list.txt'
    database = '/Users/dorianglon/Desktop/BPG_limited/Cornell_users.db'
    # start = 1616533953
    #
    # look_for_new_redditors('Cornell', database, all_time_list, start, university=True, college=False)

    analyze_redditor_posts_and_comments(database, 'Cornell')


if __name__ == '__main__':
    main()