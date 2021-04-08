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

    if len(df) > chunk_size:
        chunks = list()
        num_chunks = len(df) // chunk_size + 1
        for i in range(num_chunks):
            chunks.append(df[i * chunk_size:(i + 1) * chunk_size])
        return chunks
    else:
        return [df]


def clean_posts(df):
    """
    Function makes sures that string are in ascii encoding
    :param df: dataframe to operate on
    :return: cleaned dataframe
    """

    dfs = split_dataframe(df)
    for df in dfs:
        for index,row in df.iterrows():
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
    pos_subs = ['bio', 'bg', 'bks', '49', 'bapc', 'cc', 'cm', 'cfe', 'comp', 'ckg', 'dogs', 'kto', 'la', 'ml'
                , 'math', 'nba', 'nsq', 'pf', 'pt', 'pton', 'run', 'st', 'sca', 'stk', 'tchs', 'tm', 'trvl'
                , 'box', 'lol', '30sc', 'f1', 'pd', 'hw', 'nasa', 'mma', 'atc', 'as']
    neg_sub = 'axty'
    for index, row in df.iterrows():
        scores = analyzer.polarity_scores(row[0])
        pos = scores['pos']
        neg = scores['neg']
        row[2] = pos
        row[3] = neg
        if row.subreddit == neg_sub:
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
    directory = 'drive/MyDrive/clean_dataframes'
    if not os.path.isdir(directory):
        os.mkdir(directory)

    pos_subs = ['bio', 'bg', 'bks', '49', 'bapc', 'cc', 'cm', 'cfe', 'comp', 'ckg', 'dogs', 'kto', 'la', 'ml'
        , 'math', 'nba', 'nsq', 'pf', 'pt', 'pton', 'run', 'st', 'sca', 'stk', 'tchs', 'tm', 'trvl'
        , 'box', 'lol', '30sc', 'f1', 'pd', 'hw', 'nasa', 'mma', 'atc', 'as']
    neg_sub = 'axty'

    # Eliminates false positives and false negatives
    count = 1
    for df in dataframes:
        file_name = directory + '/clean_dataframe_' + str(count) + '.pkl'
        for index, row in df.iterrows():
            if row.neg > 0.1 and row.subreddit in pos_subs:
                df.drop(index, inplace=True)
            elif row.pos > 0.1 and row.subreddit == neg_sub:
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
        os.remove(full_path)
    final_df = pd.concat(frames)
    os.rmdir(directory)

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

    os.mkdir(directory)

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
    :param df: dataframe
    :param y_train_path: path to save one hot encodings for training batch
    :param y_test_path: path to save one hot encodings for testing batch
    :param split_test_dir: directory to dump split test posts
    :param split_train_dir: directory to dump split training posts
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
    for post in df:
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
                embeddings = np.concatenate([embeddings, new_array])
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

    model.compile(
        loss='categorical_crossentropy',
        optimizer=keras.optimizers.Adam(0.001),
        metrics=['accuracy']
    )

    # train the model
    history = model.fit(
        X_train, y_train,
        epochs=3,
        batch_size=2,
        validation_split=0.2,
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

    if not os.path.isdir(dir_for_encodings):
        os.mkdir(dir_for_encodings)

    if training:
        curr_count = 1
        while curr_count <= total_num_files:
            try:
                saved_file = 'X_train_posts_' + str(curr_count) + '.pkl'
                one_by_one_encoding(use, dir_posts, dir_for_encodings, curr_count, saved_file, 'X_train_encodings')
                curr_count += 1
            except Exception:
                pass
    if testing:
        curr_count = 1
        while curr_count <= total_num_files:
            try:
                saved_file = 'X_test_posts_' + str(curr_count) + '.pkl'
                one_by_one_encoding(use, dir_posts, dir_for_encodings, curr_count, saved_file, 'X_test_encodings')
                curr_count += 1
            except Exception:
                pass


def get_file_amount(directory):
    """
    Function counts number of files in some folder
    """

    count = 0
    for file in os.listdir(directory):
        count += 1

    return count


def main():
    main_data_file = 'drive/MyDrive/Steti_Tech/Anxiety_mid_final.txt'
    original_dataframe_file = 'drive/MyDrive/Steti_Tech/original_dataframe.pkl'
    clean_dataframe_file = 'drive/MyDrive/Steti_Tech/clean_dataframe.pkl'

    test_posts_dir = 'drive/MyDrive/Steti_Tech/test_posts'
    train_posts_dir = 'drive/MyDrive/Steti_Tech/train_posts'
    test_encodings_dir = 'drive/MyDrive/Steti_Tech/test_encodings'
    train_encodings_dir = 'drive/MyDrive/Steti_Tech/train_encodings'

    y_train_path = 'drive/MyDrive/Steti_Tech/y_train.pkl'
    y_test_path = 'drive/MyDrive/Steti_Tech/y_test.pkl'
    X_train_path = 'drive/MyDrive/Steti_Tech/X_train.pkl'
    X_test_path = 'drive/MyDrive/Steti_Tech/X_test.pkl'

    use = hub.load('https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3')
    model_path = 'drive/MyDrive/Steti_Tech/Anxiety_Predictor_for_MidLength_Posts'

    if not os.path.isfile(X_test_path):
        if not os.path.isdir(train_posts_dir):
            df = make_dataframe(main_data_file, original_dataframe_file, clean_dataframe_file)
            pickle_datasets(df, y_train_path, y_test_path, train_posts_dir, test_posts_dir)

        do_sentence_encodings(get_file_amount(train_posts_dir), use, train_posts_dir, train_encodings_dir,
                              training=True)
        do_sentence_encodings(get_file_amount(test_posts_dir), use, test_posts_dir, test_encodings_dir, testing=True)
        concat_embeddings(test_encodings_dir, get_file_amount(test_posts_dir), X_test_path)
        concat_embeddings(train_encodings_dir, get_file_amount(train_posts_dir), X_train_path)

    if not os.path.isdir(model_path):
        y_train, y_test, X_train, X_test = load_pickled_datasets(X_train_path, X_test_path, y_train_path, y_test_path)
        model = train_and_save_model(y_train, y_test, X_train, X_test, model_path)
    else:
        model = load_model(model_path)


if __name__ == '__main__':
    main()