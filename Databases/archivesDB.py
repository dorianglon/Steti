import sqlite3


def create_connection_archives(db_file):
    """
    Function connects to Database
    """

    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception:
        pass
    return conn


def list_authors(conn):
    """
    Function returns list of all authors from Database
    """

    cur = conn.cursor()
    cur.execute('SELECT * FROM archives')
    res = cur.fetchall()
    if not res:
        return []
    else:
        authors = []
        for r in res:
            authors.append(r[0])
        return authors


def find_author(conn, author):
    """
    Function finds row from given author
    """

    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM archives WHERE author=?', (author,))
    except sqlite3.OperationalError:
        pass
    res = cur.fetchone()
    return res


def update_author_report_value(conn, author, reported):
    """
    Function updates existing author's reported status
    """

    cur = conn.cursor()
    cur.execute('UPDATE archives SET reported=? WHERE author=?', (reported, author))
    conn.commit()


def update_author_flagged_value(conn, author):
    """
    Function updates an author's stats
    """

    cur = conn.cursor()
    _author = find_author(conn, author)
    if _author:
        cur.execute('UPDATE archives SET flagged=? WHERE author=?', (_author[1] + 1, author))
    else:
        cur.execute('INSERT INTO archives VALUES (?, ?, ?)', (author, 1, 0))
    conn.commit()


def clean_archives_db(conn):
    """
    Function deletes all elements in the Database
    """

    cur = conn.cursor()
    cur.execute('DELETE FROM archives')


def create_archives_db(conn):
    """
    Function creates Database
    """

    conn.execute('CREATE TABLE archives (author TEXT PRIMARY KEY, flagged INTEGER, reported INTEGER);')