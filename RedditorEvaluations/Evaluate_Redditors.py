import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
import seaborn as sns
from pylab import rcParams
import numpy as np
from tqdm import tqdm
import os
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text
from wordcloud import WordCloud, STOPWORDS
from RedditorEvaluations.make_graph import make_graph_of_subreddits
from RedditorEvaluations.make_pdf import create_analytics_report_NN
import ftfy
import time
import logging

logger = logging.getLogger()
temps_debut = time.time()

register_matplotlib_converters()
sns.set(style='whitegrid', palette='muted', font_scale=1.2)

HAPPY_COLORS_PALETTE = ["#01BEFE", "#FFDD00", "#FF7D00", "#FF006D", "#ADFF02", "#8F00FF"]
sns.set_palette(sns.color_palette(HAPPY_COLORS_PALETTE))

rcParams['figure.figsize'] = 12, 8


def word_cloud(df, file_name):
    """
    Function makes a wordcloud and saves it
    :param df: dataframe
    :param file_name: where to save worldcloud
    """
    text = ' '.join(df.to_numpy().tolist())
    cloud = WordCloud(stopwords=STOPWORDS, background_color='white').generate(text)
    plt.figure(figsize=(16, 10))
    plt.imshow(cloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig(file_name)


def read_user_data(file_path):
    """
    Function reads user data, posts or comments or both
    :param file_path: path where this data is located
    :return: dataframe with data
    """
    df = pd.read_csv(file_path, delimiter='\t')
    return df


def load_model(model_path):
    """
    Function loads our model
    :param model_path: path where model is located
    :return: model
    """
    from tensorflow import keras
    return keras.models.load_model(model_path)


def get_subreddit_list(df):
    """
    Function makes a list of subreddits that user is active in
    :param df: dataframe
    :return: list with subreddits( format : [['python', 5]]. The # is the occurrences)
    """
    subs = []
    for subreddit in df:
        # if subreddit isn't already present then add it to list with a count of 1
        if not subs:
            subs.append([subreddit, 1])
        # if it is present then add one to count
        else:
            in_subs = False
            for sub in subs:
                if sub[0] == subreddit:
                    sub[1] += 1
                    in_subs = True
            if not in_subs:
                subs.append([subreddit, 1])
    return subs


def analyze_posts_and_comments(df, model, use, username, dest_dir):
    """
    Function assembles necessary data for pdf reports. Uses pretrained model to analyze redditor's
    posts or comments or both
    :param df: dataframe with the user's data
    :param model: pretrained model
    :param use: sentence encoder
    :param username: redditor username
    :param dest_dir: destination directory for pdf if system thinks the person is a a possible
    danger to himself
    """

    # read in the appropriate data from df
    try:
        text = df.text
        dates = df.date
        subreddits = df.subreddit
        user_text = []
        # iterate through the posts and encode them
        for r in tqdm(text):
            emb = use(r)
            post_emb = tf.reshape(emb, [-1]).numpy()
            user_text.append(post_emb)
        user_text = np.array(user_text)

        depressed = []
        index = 0
        while index < len(user_text):
            prediction = model.predict(user_text[index:index + 1])
            if np.argmax(prediction) == 0:
                score = np.amax(prediction)
                # only flag the posts that are negative scores of 0.9 and higher
                if score > .9:
                    new_text = ftfy.fix_text(text[index])
                    sub = ftfy.fix_text(subreddits[index])
                    depressed.append([new_text, dates[index], sub, score])
            index += 1

        # If there are any flagged posts at all then proceed to making a pdf report.
        if depressed:
            word_cloud_file_name = username + '_Word_Cloud.png'
            subs_file_name = username + '_subs.png'
            word_cloud(text, word_cloud_file_name)
            subs = get_subreddit_list(subreddits)
            make_graph_of_subreddits(subs, subs_file_name)
            create_analytics_report_NN(username, depressed, word_cloud_file_name, subs_file_name, dest_dir)
    except Exception as e:
        logger.error("Something went wrong. Complete error : %s", e)


def main():
    directory = '/Users/dorianglon/Desktop/Dead_Redditors_data'
    destination_directory = '/Users/dorianglon/Desktop/Dead_Redditors_reports'
    model_path = '/Users/dorianglon/Desktop/BPG_limited/TRAINED_SUICIDE_&_DEPRESSION_NEW'
    use = hub.load('https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3')
    model = load_model(model_path)
    for file in os.listdir(directory):
        try:
            file_path = directory + '/' + file
            df = read_user_data(file_path)
            df = df.dropna()
            username = file[:-4]
            username = ftfy.fix_text(username)
            analyze_posts_and_comments(df, model, use, username, destination_directory)
        except Exception as e:
            logger.error("Something went wrong. Complete error : %s", e)


if __name__ == '__main__':
    main()
