import sqlite3


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
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

    cur.execute('SELECT * FROM userUpdated WHERE username=?', (username,))
    res = cur.fetchone()

    # if not res:
    # 	print('No results for username:', username)

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
    database = 'users.db' # CREATE TABLE userUpdated (username TEXT PRIMARY KEY, updated INTEGER);
    conn = create_connection(database)

    with conn:
        print(find_user(conn, 'dorian'))
        update_user(conn, 'dorian', 69)

        print(find_user(conn, 'dorian'))
        update_user(conn, 'dorian', 420)
        
        print(find_user(conn, 'dorian'))
        update_user(conn, 'david', 666)

        list_users(conn)
        clean_db(conn)