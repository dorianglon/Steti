import matplotlib.pyplot as plt
import pandas as pd


def make_graph_of_subreddits(subs, file_name):
    """
    Function makes horizontal bar-ish graph for subreddit activity for a redditor
    :param subs: list of subreddits posted or commented on by redditor in question
    :param file_name: path for which to save the graph to
    """

    # set font
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = 'Helvetica'

    # set the style of the axes and the text color
    plt.rcParams['axes.edgecolor'] = '#333F4B'
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['xtick.color'] = '#333F4B'
    plt.rcParams['ytick.color'] = '#333F4B'
    plt.rcParams['text.color'] = '#333F4B'

    x_val = []
    y_val = []
    for sub in subs:
        x_val.append(sub[0])
        y_val.append(sub[1])
    occurrences = pd.Series(y_val, index=x_val)
    df = pd.DataFrame({'occurrences': occurrences})
    df = df.sort_values(by='occurrences')
    my_range = list(range(1, len(df.index) + 1))
    fig, ax = plt.subplots(figsize=(5, 3.5))
    plt.hlines(y=my_range, xmin=0, xmax=df['occurrences'], color='#007ACC', alpha=0.2, linewidth=5)
    plt.plot(df['occurrences'], my_range, "o", markersize=5, color='#007ACC', alpha=0.6)
    ax.set_xlabel('Occurrence', fontsize=15, fontweight='black', color='#333F4B')
    ax.set_ylabel('')

    # set axis
    ax.tick_params(axis='both', which='major', labelsize=12)
    plt.yticks(my_range, df.index)

    fig.text(-0.23, 0.96, 'Subreddit', fontsize=15, fontweight='black', color='#333F4B')

    # change the style of the axis spines
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.spines['left'].set_smart_bounds(True)
    ax.spines['bottom'].set_smart_bounds(True)

    # set the spines position
    ax.spines['bottom'].set_position(('axes', -0.04))
    ax.spines['left'].set_position(('axes', 0.015))

    plt.savefig(file_name, dpi=300, bbox_inches='tight')
