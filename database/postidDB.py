import sqlite3


def create_connection_post(db_file):
    conn = None

    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)

    return conn


def list_post_ids(conn):
    cur = conn.cursor()

    cur.execute('SELECT * FROM numComments')
    res = cur.fetchall()

    if not res:
        return []
    else:
        post_ids = []
        for r in res:
            post_ids.append(r[0])
        return post_ids


def find_post_id(conn, post_id):
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM numComments WHERE post_id=?', (post_id,))
    except sqlite3.OperationalError:
        pass
    res = cur.fetchone()

    return res


def update_post_id(conn, post_id, num_comments):
    cur = conn.cursor()

    if find_post_id(conn, post_id):
        cur.execute('UPDATE numComments SET num_comments=? WHERE post_id=?', (num_comments, post_id))
    else:
        cur.execute('INSERT INTO numComments VALUES (?, ?)', (post_id, num_comments))

    conn.commit()


def clean__post_db(conn):
    cur = conn.cursor()

    cur.execute('DELETE FROM numComments')


def create_post_db(conn):
    conn.execute('CREATE TABLE numComments (post_id TEXT PRIMARY KEY, num_comments INTEGER);')