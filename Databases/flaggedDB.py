import sqlite3


def create_connection_flagged_post(db_file):
    """
    Function connects to Database
    """

    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
    return conn


def list_flagged_posts(conn):
    """
    Function returns list of all flagged posts
    """

    cur = conn.cursor()
    cur.execute('SELECT * FROM flagged')
    res = cur.fetchall()
    if not res:
        return []
    else:
        return res


def add_flagged_post(conn, title, post, id, date, subreddit, score):
    """
    Function adds a new flagged post to database
    """

    cur = conn.cursor()
    cur.execute('INSERT INTO flagged VALUES (?, ?, ?, ?, ?, ?)', (id, title, post, date, subreddit, score))
    conn.commit()


def clean_flagged_posts_db(conn):
    """
    Function deletes all elements in the Database
    """

    cur = conn.cursor()
    cur.execute('DELETE FROM flagged')


def create_flagged_posts_db(conn):
    """
    Function creates Database
    """

    conn.execute('CREATE TABLE flagged (id TEXT PRIMARY KEY, title TEXT, submission TEXT, date INTEGER, subreddit '
                 'TEXT, score TEXT);')