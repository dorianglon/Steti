from selenium import webdriver


def get_bots(driver, url, destination):
    """
    Function uses selenium to scrape bots' usernames from B0tRank
    """

    not_bots = ['Rank', 'Bot Name', 'Score', 'Good Bot Votes', 'Bad Bot Votes', 'Comment Karma', 'Link Karma']
    page = 1

    while page <= 144:

        this_url = url + str(page)
        driver.get(this_url)

        table = driver.find_element_by_xpath("//table[@class='table']")
        links = table.find_elements_by_tag_name('a')
        for link in links:
            bot = link.text
            if bot not in not_bots:
                with open(destination, 'a+') as f:
                    f.write(bot + '\n')
        page += 1


def main():
    destination = '/Users/dorianglon/Desktop/Steti_Tech/bots.txt'
    url = 'https://botrank.pastimes.eu/?sort=rank&page='
    driver = webdriver.Safari()
    get_bots(driver, url, destination)


if __name__ == '__main__':
    main()