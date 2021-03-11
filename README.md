# Project_BPG

So far we have scraping tools for reddit and a script that predicts redditors mental health and creates pdf reports if the redditor is sus.

* [Usage](#usage)

### Usage

First I'll show the various scraping tools and how to quickly get them to action. I made three classes: ScrapeSubreddit, ScrapeRedditorData, and GetRedditorsFromUSub

Starting with the first one which scrapes a subreddit. We don't really need this anymore because it was mostly for obtaining the training data.

```python
from ScrapeTools.Scraping import ScrapeSubreddit

# create instance, three parameters are the subreddit, an abbreviation for the subreddit(prefereably no more then 4 chars), and unix timestamp which denotes from when we should start scraping.
subreddit_scraper = ScrapeSubreddit(subreddit='AskReddit', subreddit_abbrev='ask', search_after=1600000000)

# this method will get all of the submissions on the subreddit posted after 'search after'. Creates a text file for the posts. No need to pass anything.
subreddit_scraper.extract_reddit_posts()

#this method will get all of the comments on the subreddit posted after 'search after'. Creates a text file for the posts. No need to pass anything.
subreddit_scraper.extract_reddit_comments()
```

Now I'll show how to use the ScrapeRedditorData class. This one just scrapes information about a specific redditor.

```python
from ScrapeTools.Scraping import ScrapeRedditorData

# declare some path where you want to store the data, create instance. Three parameters are the redditor, timestamp we start scraping from, and file to save data
file = 'some_redditor.txt'
redditor_scraper = ScrapeRedditorData(redditor='some_redditor', search_after=1600000000, save_to_file=file)

# then just use the extract_redditor_data method. The only two parameters that you should declare are posts and comments. Default are both true.
# Will scrape for both if nothing is changed.
redditor_scraper.extract_redditor_data(posts=True, comments=False)
```

And now the GetRedditorsFromUSub class. This class is used to compile a list of redditors from an institution's subreddit that are believed to attend that institution

```python
from ScrapeTools.Scraping import GetRedditorsFromUSub

# declare some path where you want to store the usernames of believed attendees, create instance. Three parameters, institution's subreddit, timestamp we start scraping from
# and file to save the data to
file = 'kids_that_go_to_cornell.txt'
subreddit_redditor_scraper = GetRedditorsFromUSub('Cornell', 1600000000, file)

# then just run the extract_redditors_from_sub method. This will take a long time.
subreddit_redditor_scraper.extract_redditors_from_U_sub_past_mode()

# if you run over multiple days you might want to make sure that no username appears twice. Just run this method.
subreddit_redditor_scraper.eliminate_repeats()
```

We will mainly be using instances from those last two classes in our script that will be running 24/7
The module RedditorEvaluation is what we need to work on. The file NN_on_redditors_file.py is a rough sketch of what we will have. It loads the model, and predicts users' mental health, and then creates a pdf if user is depressed. This script already assumes that we have scraped data on those users for the last n days.
