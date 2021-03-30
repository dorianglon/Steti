import sqlite3


def create_connection(db_file):
    """
    Function connects to database
    """

    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)
    return conn


def list_users(conn):
    """
    Function returns list of all redditors from database
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
    Function finds redditor in database
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
    Function deletes all elements in database
    """

    cur = conn.cursor()
    cur.execute('DELETE FROM userUpdated')


def create_db(conn):
    """
    Function creates new redditor database
    """

    conn.execute('CREATE TABLE userUpdated (username TEXT PRIMARY KEY, updated INTEGER);')


if __name__ == '__main__':
    cornell_db_path = '/Users/dorianglon/Desktop/BPG_limited/Cornell_users.db'
    cornell_path_all_time = '/Users/dorianglon/Desktop/BPG_limited/Cornell_all_time_redditors.txt'
    deanza_db_path = '/Users/dorianglon/Desktop/BPG_limited/DeAnza_users.db'
    deanza_path_all_time = '/Users/dorianglon/Desktop/BPG_limited/DeAnza_all_time_redditors.txt'
    ucsc_db_path = '/Users/dorianglon/Desktop/BPG_limited/UCSC_users.db'
    ucsc_all_time = '/Users/dorianglon/Desktop/BPG_limited/UCSC_all_time_redditors.txt'

    cornell_conn = create_connection(cornell_db_path)
    with cornell_conn:
        out = 'Cornell active students : ' + str(len(list_users(cornell_conn)))
        print(out)
    with open(cornell_path_all_time, 'r') as f:
        lines = f.readlines()
        i = 0
        for line in lines:
            i += 1
        out = 'Cornell all time : ' + str(i)
        print(out)

    de_anza_conn = create_connection(deanza_db_path)
    with de_anza_conn:
        out = '\nDe Anza active students : ' + str(len(list_users(de_anza_conn)))
        print(out)
    with open(deanza_path_all_time, 'r') as f:
        lines = f.readlines()
        i = 0
        for line in lines:
            i += 1
        out = 'De Anza all time : ' + str(i)
        print(out)

    ucsc_conn = create_connection(ucsc_db_path)
    with ucsc_conn:
        out = '\nUCSC active students : ' + str(len(list_users(ucsc_conn)))
        print(out)
    with open(ucsc_all_time, 'r') as f:
        lines = f.readlines()
        i = 0
        for line in lines:
            i += 1
        out = 'UCSC all time : ' + str(i)
        print(out)