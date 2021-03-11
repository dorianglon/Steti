from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

REDDIT_LOGIN_URL = 'https://www.reddit.com/login/'


class BPG_SMART_BOT:
    def __init__(self, bot_username, bot_password, redditor, message):
        self.bot_username = bot_username
        self.bot_password = bot_password
        self.redditor = redditor
        self.message = message
        self.driver = webdriver.Safari()

    def login(self):
        try:
            self.driver.get(REDDIT_LOGIN_URL)
            time.sleep(1.5)
            username = self.driver.find_element_by_id(id_='loginUsername')
            username.send_keys(self.bot_username)
            password = self.driver.find_element_by_id(id_='loginPassword')
            password.send_keys(self.bot_password)
            password.send_keys(Keys.RETURN)
            time.sleep(5)
        except Exception as e:
            print(e)

    def go_to_redditor(self):
        try:
            current_page = self.driver.current_url
            add_on = 'user/' + self.redditor + '/'
            user_page = current_page + add_on
            self.driver.get(user_page)
            time.sleep(2)
        except Exception as e:
            print(e)

    def start_chatting(self):
        try:
            chat = self.driver.find_element_by_xpath("""//a[@class="_1x6pySZ2CoUnAfsFhGe7J1"]""")
            chat.click()
            time.sleep(4)
            text = self.driver.find_element_by_xpath(
                """//textarea[@class="_24sbNUBZcOO5r5rr66_bs4 TqpfKgK2FdKbljZzdRLIU"]""")
            text.send_keys(self.message)
            time.sleep(1)
            text.send_keys(Keys.RETURN)
            time.sleep(4)
        except Exception as e:
            print(e)


def main():
    redditor = 'Far-Examination4638'
    message = 'Hey there, just testing the BOT capabilities.'
    bot = BPG_SMART_BOT('Testing_Capabilities', 'randompassword', redditor, message)
    bot.login()
    bot.go_to_redditor()
    bot.start_chatting()


if __name__ == '__main__':
    main()