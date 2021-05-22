import sqlite3


"""
Database to store the active redditors from a school
"""


def create_connection(db_file):
    """
    Function connects to Database
    """

    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
    return conn


def list_users(conn):
    """
    Function returns list of all redditors from Database
    """

    cur = conn.cursor()
    cur.execute('SELECT * FROM userUpdated')
    res = cur.fetchall()
    if not res:
        return []
    else:
        redditors = []
        for r in res:
            redditors.append(r[0])
        return redditors


def find_user(conn, username):
    """
    Function finds redditor in Database
    """

    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM userUpdated WHERE username=?', (username,))
    except sqlite3.OperationalError:
        pass
    res = cur.fetchone()
    return res


def update_user(conn, username, timestamp):
    """
    Function updates the timestamp for a redditor or creates new row if redditor not found
    """

    cur = conn.cursor()
    if find_user(conn, username):
        cur.execute('UPDATE userUpdated SET updated=? WHERE username=?', (timestamp, username))
    else:
        cur.execute('INSERT INTO userUpdated VALUES (?, ?)', (username, timestamp))
    conn.commit()


def clean_db(conn):
    """
    Function deletes all elements in Database
    """

    cur = conn.cursor()
    cur.execute('DELETE FROM userUpdated')


def remove_redditor(conn, username):
    """
    Function removes a certain redditor from the table
    """
    cur = conn.cursor()
    cur.execute('DELETE FROM userUpdated WHERE username=?', (username,))


def create_db(conn):
    """
    Function creates new redditor Database
    """

    conn.execute('CREATE TABLE userUpdated (username TEXT PRIMARY KEY, updated INTEGER);')
