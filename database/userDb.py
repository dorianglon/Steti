import sqlite3


def create_connection(db_file):
    conn = None

    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)

    return conn


def list_users(conn):
    cur = conn.cursor()

    cur.execute('SELECT * FROM userUpdated')
    res = cur.fetchall()

    if not res:
        print('Database is empty')
    else:
        print('All users:')
        for r in res:
            print(r)


def find_user(conn, username):
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM userUpdated WHERE username=?', (username,))
    except sqlite3.OperationalError:
        pass
    res = cur.fetchone()

    return res


def update_user(conn, username, timestamp):
    cur = conn.cursor()

    if find_user(conn, username):
        cur.execute('UPDATE userUpdated SET updated=? WHERE username=?', (timestamp, username))
    else:
        cur.execute('INSERT INTO userUpdated VALUES (?, ?)', (username, timestamp))

    conn.commit()


def clean_db(conn):
    cur = conn.cursor()

    cur.execute('DELETE FROM userUpdated')


if __name__ == '__main__':
    database = 'users.db'  # CREATE TABLE userUpdated (username TEXT PRIMARY KEY, updated INTEGER);
    connection = create_connection(database)

    with connection:
        print(find_user(connection, 'dorian'))
        update_user(connection, 'dorian', 69)

        print(find_user(connection, 'dorian'))
        update_user(connection, 'dorian', 420)

        print(find_user(connection, 'dorian'))
        update_user(connection, 'david', 666)

        list_users(connection)
        # clean_db(connection)
