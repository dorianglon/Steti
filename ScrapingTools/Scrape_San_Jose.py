from ScrapingTools.Scraping import *


def main():
    file_name = '/Users/dorianglon/Desktop/BPG_limited/San_Jose_Gun_Owners.txt'
    San_Jose = GetRedditorsFromSub('SanJose', 1382468218, file_name)
    San_Jose.extract_gun_owner_redditors_from_city(sort_type='created_utc', sort='asc', size=100000)


if __name__ == '__main__':
    main()