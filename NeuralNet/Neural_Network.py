import numpy as np
import tensorflow as tf
from tensorflow import keras
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import seaborn as sns
from pylab import rcParams
from tqdm import tqdm
import tensorflow_text
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
from sklearn.model_selection import train_test_split
import tensorflow_hub as hub
import os
import pickle
import math
import re

register_matplotlib_converters()
sns.set(style='whitegrid', palette='muted', font_scale=1.2)

HAPPY_COLORS_PALETTE = ["#01BEFE", "#FFDD00", "#FF7D00", "#FF006D", "#ADFF02", "#8F00FF"]
sns.set_palette(sns.color_palette(HAPPY_COLORS_PALETTE))

rcParams['figure.figsize'] = 12, 8

RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)


def round_down(x):
    """
    Function rounds down number to nearest hundred
    :param x: number
    :return: rounded down to nearest hundred
    """

    return int(math.floor(x / 100.0)) * 100


def split_dataframe(df, chunk_size=25000):
    """
    Function splits dataframe into smaller ones
    :param df: dataframe
    :param chunk_size: how many sub dataframes
    :return: list of dataframes
    """

    chunks = list()
    num_chunks = len(df) // chunk_size + 1
    for i in range(num_chunks):
        chunks.append(df[i * chunk_size:(i + 1) * chunk_size])
    return chunks


def clean_posts(df):
    """
    Function makes sures that string are in ascii encoding
    :param df: dataframe to operate on
    :return: cleaned dataframe
    """

    dfs = split_dataframe(df)
    for df in tqdm(dfs):
        for index, row in df.iterrows():
            post = row['combined']
            encoded_post = post.encode("ascii", "ignore")
            decoded_post = encoded_post.decode()
            df['combined'].replace(to_replace=post, value=decoded_post, inplace=True)

    final_df = pd.concat(dfs)
    return final_df


def make_initial_df(data_file, original_dataframe_file):
    """
    Function labels our posts and puts into dataframe format
    :param data_file: file with data
    :param original_dataframe_file: output file for serialized dataframe
    """

    # Build Pandas DataFrame
    df = pd.read_csv(data_file, delimiter='\t')
    df["pos"] = ""
    df["neg"] = ""
    df["label"] = ""
    df.head()
    df = df.dropna(how='any', axis=0)

    # Perform Sentiment Analysis on Training Data and Populate Pandas DataFrame
    analyzer = SentimentIntensityAnalyzer()
    pos_subs = ['as', 'bio', 'bg', 'bks', 'bapc', 'cc', 'cm', 'cfe', 'cmp', 'ckng', 'dogs', 'hsty', 'ah'
        , 'keto', 'la', 'lgst', 'ml', 'math', 'nba', 'nsq', 'pf', 'pt_m', 'pd', 'pton', 'run'
        , 'st', 'sca', 'stk', 'tchs', 'tech', 'tm', 'trvl', 'ecah']
    neg_subs = ['sw', 'dpn', 'dpd']
    for index, row in tqdm(df.iterrows()):
        scores = analyzer.polarity_scores(row[0])
        pos = scores['pos']
        neg = scores['neg']
        row[2] = pos
        row[3] = neg
        if row.subreddit in neg_subs:
            row.label = 0
        elif row.subreddit in pos_subs:
            row.label = 1
    df.to_pickle(original_dataframe_file)


def eliminate_noise(original_dataframe_file, clean_dataframe_file):
    """
    Eliminates false negatives and positives from original dataframe and splits the dataframe into smaller sub
    dataframes. Merges cleaned sub dataframes and saves it.
    :param original_dataframe_file: where serialized original df is stored
    :param clean_dataframe_file: new path for serialized dataframe :return: dataframe
    """

    original_df = read_dataframe(original_dataframe_file)
    # os.remove(original_dataframe_file)

    # split dataframe into smaller ones because runtime is exponentially shorter
    dataframes = split_dataframe(original_df)
    directory = 'clean_dataframes'

    pos_subs = ['as', 'bio', 'bg', 'bks', 'bapc', 'cc', 'cm', 'cfe', 'cmp', 'ckng', 'dogs', 'hsty', 'ah'
        , 'keto', 'la', 'lgst', 'ml', 'math', 'nba', 'nsq', 'pf', 'pt_m', 'pd', 'pton', 'run'
        , 'st', 'sca', 'stk', 'tchs', 'tech', 'tm', 'trvl', 'ecah']
    neg_subs = ['sw', 'dpn', 'dpd']

    # Eliminates false positives and false negatives
    count = 1
    for df in dataframes:
        file_name = directory + '/clean_dataframe_' + str(count) + '.pkl'
        for index, row in tqdm(df.iterrows()):
            if row.neg > 0.1 and row.subreddit in pos_subs:
                df.drop(index, inplace=True)
            elif row.pos > 0.1 and row.subreddit in neg_subs:
                df.drop(index, inplace=True)
            else:
                pass
        df.to_pickle(file_name)
        count += 1

    # gather all small and clean datasets and merge them
    frames = []
    for file in os.listdir(directory):
        full_path = directory + '/' + file
        df = read_dataframe(full_path)
        frames.append(df)
    final_df = pd.concat(frames)

    # randomly choose pos and neg posts from dataframe and evenly split the two
    # then combine and save the dataframe
    casual = final_df[final_df.label == 1]
    casual_length = len(casual.index)
    suicidal_or_depressed = final_df[final_df.label == 0]
    suicidal_or_depressed_length = len(suicidal_or_depressed.index)

    # make the size of each dataframe equal to whichever label is smallest
    if casual_length > suicidal_or_depressed_length:
        size = round_down(suicidal_or_depressed_length)
        print('Size : ' + str(size))
    elif suicidal_or_depressed_length > casual_length:
        size = round_down(casual_length)
        print('Size : ' + str(size))
    elif suicidal_or_depressed_length == casual_length:
        size = round_down(casual_length)
        print('Size : ' + str(size))

    # create final clean dataframe and save it
    suicidal_or_depressed_df = suicidal_or_depressed.sample(n=size, replace=True, random_state=RANDOM_SEED)
    casual_df = casual.sample(n=size, replace=True, random_state=RANDOM_SEED)
    new_df = casual_df.append(suicidal_or_depressed_df).reset_index(drop=True)
    new_df.to_pickle(clean_dataframe_file)
    return new_df


def read_dataframe(df_filename):
    """
    Function reads dataframe from file
    :param df_filename: file where the dataframe is located
    :return: dataframe lol
    """

    return pd.read_pickle(df_filename)


def divide_and_conquer(directory, data, training=False, testing=False):
    """
    Function splits the post into smaller sub files in order to be able to encode
    sentences more efficiently
    :param directory: directory to dump posts in
    :param data: dataframe to split
    :param training: boolean value to signal we are splitting training set
    :param testing: boolean value to signal we are splitting testing set
    """

    file_name = ''
    if training:
        file_name = 'X_train_posts'
    elif testing:
        file_name = 'X_test_posts'

    dataframes = split_dataframe(data, chunk_size=10000)
    index = 1
    for df in dataframes:
        path = directory + '/' + file_name + '_' + str(index) + '.pkl'
        with open(path, 'wb') as f:
            pickle.dump(df, f)
            f.close()
        index += 1


def pickle_datasets(df, y_train_path, y_test_path, split_train_dir, split_test_dir):
    """
    Function splits into testing and training set. Then it splits the training and testing dataframes
    and saves the training and testing label encodings
    :param split_test_dir: directory to dump split test posts
    :param split_train_dir: directory to dump split training posts
    :param df: dataframe
    :param y_train_path: path to save one hot encodings for training batch
    :param y_test_path: path to save one hot encodings for testing batch
    """

    from sklearn.preprocessing import OneHotEncoder

    # encode data from dataframe. Example : positive = [1, 0], neg = [0, 1]
    type_one_hot = OneHotEncoder(sparse=False).fit_transform(df.label.to_numpy().reshape(-1, 1))

    # split data into training and testing
    train_posts, test_posts, y_train, y_test = train_test_split(
        df.combined,
        type_one_hot,
        test_size=.1,
        random_state=RANDOM_SEED
    )

    divide_and_conquer(split_train_dir, train_posts, training=True, testing=False)
    divide_and_conquer(split_test_dir, test_posts, training=False, testing=True)

    # pickle one hot encodings for training set
    with open(y_train_path, 'wb') as f:
        pickle.dump(y_train, f)
        f.close()

    # pickle one hot encodings for testing set
    with open(y_test_path, 'wb') as f:
        pickle.dump(y_test, f)
        f.close()


def one_by_one_encoding(use, directory_saved, directory_to_save, index, file_saved, file_to_save):
    """
    Function encodes our sentences using universal sentence encoder
    :param use: universal sentence encoder
    :param directory_saved: directory where the posts are
    :param directory_to_save: directory to save encodings
    :param index: current index for posts (which was split previously)
    :param file_saved: path where the specific file with posts is located
    :param file_to_save: path in which to save encodings
    :return:
    """
    file_path = directory_saved + '/' + file_saved
    df = read_dataframe(file_path)

    encodings = []
    for post in tqdm(df):
        emb = use(post)
        post_emb = tf.reshape(emb, [-1]).numpy()
        encodings.append(post_emb)
    encodings_np = np.array(encodings)

    path_to_save = directory_to_save + '/' + file_to_save + '_' + str(index) + '.pkl'
    with open(path_to_save, 'wb') as f:
        pickle.dump(encodings_np, f)
        f.close()
    encodings_np = None
    encodings.clear()


def load_first_np_array(directory_with_embeddings):
    """
    Functions reads in the first numpy array of training/testing encodings
    :param directory_with_embeddings: self explanatory
    :return: numpy array of encodings
    """

    for file in os.listdir(directory_with_embeddings):
        this_index = re.findall(r'\d+', file)
        if this_index[0] == '1':
            path = directory_with_embeddings + '/' + file
            file = open(path, 'rb')
            array = pickle.load(file)
            file.close()
            return array


def concat_embeddings(directory_with_embeddings, amount_of_embeddings, path_to_save):
    """
    Function concatenates all of the encoded sentences as one numpy array fro training/testing encodings
    :param directory_with_embeddings:  self explanatory
    :param amount_of_embeddings: how many total small files there are of encoded sentences for either training or testing set
    :param path_to_save: path to pickle concatenated numpy array of encodings
    """
    count = 2
    embeddings = load_first_np_array(directory_with_embeddings)
    while count <= amount_of_embeddings:
        for file in os.listdir(directory_with_embeddings):
            this_index = re.findall(r'\d+', file)
            if this_index[0] == str(count):
                path = directory_with_embeddings + '/' + file
                file = open(path, 'rb')
                new_array = pickle.load(file)
                file.close()
                np.concatenate([embeddings, new_array])
                count += 1
                break

    with open(path_to_save, 'wb') as f:
        pickle.dump(embeddings, f)
        f.close()


def load_pickled_datasets(train_encodings_path, test_encodings_path, y_train_path, y_test_path):
    """
    function loads all of our necessary data to train and test model
    :param train_encodings_path: path to save training posts encoding
    :param test_encodings_path: path to save testing posts encoding
    :param y_train_path: path to save one hot encodings for training batch
    :param y_test_path: path to save one hot encodings for testing batch
    :return: necessary data to train and test model
    """

    file = open(y_train_path, 'rb')
    y_train = pickle.load(file)
    file.close()

    file = open(y_test_path, 'rb')
    y_test = pickle.load(file)
    file.close()

    file = open(train_encodings_path, 'rb')
    X_train = pickle.load(file)
    file.close()

    file = open(test_encodings_path, 'rb')
    X_test = pickle.load(file)
    file.close()

    return y_train, y_test, X_train, X_test


def train_and_save_model(y_train, y_test, X_train, X_test, model_path):
    """
    :param y_train: label encodings for the training set
    :param y_test: label encodings for the testing set
    :param X_train: sentence encodings for the training set
    :param X_test: sentence encodings for the testing set
    :param model_path: path to save model
    :return:
    """

    # create Sequential model and add layers
    model = keras.Sequential()

    model.add(
        keras.layers.Dense(
            units=256,
            input_shape=(X_train.shape[1],),
            activation='relu'
        )
    )
    model.add(
        keras.layers.Dropout(rate=0.5)
    )

    model.add(
        keras.layers.Dense(
            units=128,
            activation='relu'
        )
    )
    model.add(
        keras.layers.Dropout(rate=0.5)
    )
    model.add(keras.layers.Dense(2, activation='softmax'))

    #
    model.compile(
        loss='categorical_crossentropy',
        optimizer=keras.optimizers.Adam(0.001),
        metrics=['accuracy']
    )

    # train the model
    history = model.fit(
        X_train, y_train,
        epochs=6,
        batch_size=8,
        validation_split=0.1,
        verbose=1,
        shuffle=True
    )

    plt.plot(history.history['loss'], label='train loss')
    plt.plot(history.history['val_loss'], label='val loss')
    plt.xlabel("epoch")
    plt.ylabel("Cross-entropy loss")
    plt.legend()
    plt.show()

    plt.plot(history.history['accuracy'], label='train accuracy')
    plt.plot(history.history['val_accuracy'], label='val accuracy')
    plt.xlabel("epoch")
    plt.ylabel("accuracy")
    plt.legend()
    plt.show()

    print(model.evaluate(X_test, y_test))

    model.save(model_path)
    return model


def load_model(model_path):
    """
    Function loads model if it already exists
    :param model_path: path where model is saved
    :return:
    """
    from tensorflow import keras
    return keras.models.load_model(model_path)


def cc_or_sw(y_pred):
    if np.argmax(y_pred) == 1:
        print('Casual Conversation. Score : ', np.amax(y_pred))
    else:
        print('Suicidal or depressed. Score : ', np.amax(y_pred))


def run_model(model, use):
    """
    Function tests model on user given posts
    :param model: model to use
    :param use: sentence encoder
    """

    test_posts = ["I only have a few people who care about me. "
                  "I know they would be devastated if I left this life, "
                  "and I feel like they are all I have that helps me to hold "
                  "on for just a little longer. If I lost them, either literally or "
                  "if they lost my trust, respect, etc, I wouldn't even hesitate to "
                  "end it all.I'm writing this at 1AM, days away from my 23rd birthday, "
                  "and I feel like I'm ready to end my life.I want to go, but I can't. "
                  "My loved ones won't let me go, and I can't let go of them. I feel stuck and I don't know what to "
                  "do. I wish there was an easy way out of this."
        , "I want to sit inside a hole, One that's dark and deep. Not for death, not for stay, Hell not "
          "even to think. Inside the hole I'll cry and scream Every God forsaken obscenity. I want to sit "
          "to be alone But don't want to be by myself, I want my emotions understood And not shoved up on a "
          "shelf. When things go bad and depression creeps I want to sit inside a hole, the one inside of "
          "me."
        , "Hi guys just wanted to put things in perspective for you all since some of "
          "you seem to be quite nervous with the recent week of stock movement. "
          "I've summarised a list all stock market crashes since 1950. There has been 7 stock market "
          "''crashes since 1950, averaging one every 10 years. The stock market crashes ranges from "
          "inflation (10%+), to oil price rises (4x) due to war, dot com bubble, housing market collapse, "
          "covid-19 etc."
        , "So I found out about hack this site and sites like it where you do ctf. It really caught my eye "
          "as a beginner programmer. I know a little about ethical hacking but not alot so i want to get "
          "into the field. Im at a point where my interests change rapidly. Is hacking something i have to "
          "be invested in for a long time or is it something i can try out and see if i like it?"
        , 'Goodbye everyone, its been a long ride.'
        , 'pretty stressed out for the test tomorrow. Its been a long time since I have taken an in class '
            'exam. Studied hard though so everything should be fine. Does anyone know how difficult '
            ' this professors tests are?'
        , 'God I am so stressed right now, just had five classes and my chem professor is crazy. Literally like 70 '
          'percent of the class is failing. RIP']

    X_test = []
    for r in tqdm(test_posts):
        emb = use(r)
        post_emb = tf.reshape(emb, [-1]).numpy()
        X_test.append(post_emb)
    X_test = np.array(X_test)

    i = 0
    while i < len(test_posts):
        print(test_posts[i])
        y_pred = model.predict(X_test[i:i+1])
        cc_or_sw(y_pred)
        i += 1


def make_dataframe(main_data_file, original_dataframe_file, clean_dataframe_file):
    """
    Function makes or returns our final dataframe(made to clean up main())
    :param main_data_file: file with our raw original data
    :param original_dataframe_file: original dataframe that has yet to be cleaned
    :param clean_dataframe_file: final clean dataframe
    :return: final dataframe
    """

    if not os.path.isfile(original_dataframe_file) and not os.path.isfile(clean_dataframe_file):
        make_initial_df(main_data_file, original_dataframe_file)
        df = eliminate_noise(original_dataframe_file, clean_dataframe_file)
    elif os.path.isfile(original_dataframe_file) and not os.path.isfile(clean_dataframe_file):
        df = eliminate_noise(original_dataframe_file, clean_dataframe_file)
    elif os.path.isfile(original_dataframe_file) and os.path.isfile(clean_dataframe_file):
        df = read_dataframe(clean_dataframe_file)
    return df


def do_sentence_encodings(total_num_files, use, dir_posts, dir_for_encodings, training=False, testing=False):
    """
    Function runs the sentence encoding modules(made to clean up main())
    :param total_num_files: amount of file in the split posts directory
    :param use: sentence encoder
    :param dir_posts: directory containing the posts
    :param dir_for_encodings: directory for which to save the embeddings
    :param training: boolean value if we are operating on training set
    :param testing: boolean value if we are operating on testing set
    """

    if training:
        curr_count = 1
        while curr_count <= total_num_files:
            try:
                saved_file = 'X_train_posts_' + str(curr_count) + '.pkl'
                one_by_one_encoding(use, dir_posts, dir_for_encodings, curr_count, saved_file, 'X_train_encodings')
                curr_count += 1
            except Exception as e:
                print('Error occurred at : ' + str(curr_count))
                break
    if testing:
        curr_count = 1
        while curr_count <= total_num_files:
            try:
                saved_file = 'X_test_posts_' + str(curr_count) + '.pkl'
                one_by_one_encoding(use, dir_posts, dir_for_encodings, curr_count, saved_file, 'X_test_encodings')
                curr_count += 1
            except Exception as e:
                print('Error occurred at : ' + str(curr_count))
                break


def main():
    main_data_file = '/Users/dorianglon/Desktop/Steti_Tech/main_data.txt'
    original_dataframe_file = '/Users/dorianglon/Desktop/Steti_Tech/original_dataframe.pkl'
    clean_dataframe_file = '/Users/dorianglon/Desktop/Steti_Tech/clean_dataframe.pkl'

    test_posts_dir = '/Users/dorianglon/Desktop/Steti_Tech/test_posts'
    train_posts_dir = '/Users/dorianglon/Desktop/Steti_Tech/train_posts'
    test_encodings_dir = '/Users/dorianglon/Desktop/Steti_Tech/test_encodings'
    train_encodings_dir = '/Users/dorianglon/Desktop/Steti_Tech/train_encodings'

    y_train_path = '/Users/dorianglon/Desktop/Steti_Tech/y_train.pkl'
    y_test_path = '/Users/dorianglon/Desktop/Steti_Tech/y_test.pkl'
    X_train_path = '/Users/dorianglon/Desktop/Steti_Tech/X_train.pkl'
    X_test_path = '/Users/dorianglon/Desktop/Steti_Tech/X_test.pkl'
    
    use = hub.load('https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3')
    model_path = '/Users/dorianglon/Desktop/Steti_Tech/TRAINED_SUICIDE_&_DEPRESSION_NEW'

    if not os.path.isfile(X_test_path):
        if not os.path.isfile(train_posts_dir):
            df = make_dataframe(main_data_file, original_dataframe_file, clean_dataframe_file)
            pickle_datasets(df, y_train_path, y_test_path, train_posts_dir, test_posts_dir)
        do_sentence_encodings(113, use, train_posts_dir, train_encodings_dir, training=True)
        do_sentence_encodings(13, use, test_posts_dir, test_encodings_dir, testing=True)
        concat_embeddings(test_encodings_dir, 13, X_test_path)
        concat_embeddings(train_encodings_dir, 113, X_train_path)

    if not os.path.isdir(model_path):
        y_train, y_test, X_train, X_test = load_pickled_datasets(X_train_path, X_test_path, y_train_path, y_test_path)
        model = train_and_save_model(y_train, y_test, X_train, X_test, model_path)
        run_model(model, use)
    else:
        model = load_model(model_path)
        run_model(model, use)


if __name__ == '__main__':
    main()