from ScrapingTools.Scraping import ScrapeRedditorData
import os


def check_length():
    with open('/Users/dorianglon/Desktop/BPG_limited/De_Anza.txt', 'r') as f:
        lines = f.readlines()
        f.close()
        count = 0
        for line in lines:
            count += 1
        print('Current count in De_Anza.txt : ' + str(count))

    with open('/Users/dorianglon/Desktop/BPG_limited/De_Anza_full_list.txt', 'r') as f:
        lines = f.readlines()
        f.close()
        count = 0
        for line in lines:
            count += 1
        print('Current count in De_Anza_full_list.txt : ' + str(count))

    with open('/Users/dorianglon/Desktop/BPG_limited/San_Jose_full_list.txt', 'r') as f:
        lines = f.readlines()
        f.close()
        count = 0
        for line in lines:
            count += 1
        print('Current count in San_Jose_full_List.txt : ' + str(count))

    if os.path.isfile('/Users/dorianglon/Desktop/BPG_limited/San_Jose_Gun_Owners.txt'):
        with open('/Users/dorianglon/Desktop/BPG_limited/San_Jose_Gun_Owners.txt', 'r') as f:
            lines = f.readlines()
            f.close()
            count = 0
            for line in lines:
                count += 1
            print('Current count in San_Jose_Gun_Owners.txt : ' + str(count))


def Dead_Redditors():
    path = '/Users/dorianglon/Desktop/BPG_limited/Dead_Redditors.txt'
    dead_redditors = []
    with open(path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            new_line = line.replace('\n', '')
            dead_redditors.append(new_line)

    save_dir = '/Users/dorianglon/Desktop/Dead_Redditors_data'
    for redditor in dead_redditors:
        file_path = save_dir + '/' + redditor + '.txt'
        redditor_data = ScrapeRedditorData(redditor, search_after=1136073600, save_to_file=file_path)
        redditor_data.extract_redditor_data(sort_type='created_utc', sort='asc', size=1000, posts=True, comments=False,
                                            for_finding_redditors=False)


if __name__ == '__main__':
    check_length()
