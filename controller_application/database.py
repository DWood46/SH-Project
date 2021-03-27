#!venv/Scripts/python.exe
import sqlite3
import globals
import threading
import os

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
    except sqlite3.Error as e:
        print(e)
    return conn
    
def execute(query, *args):
    """
    Execute a query and return the data retrieved
    :param query:   The query to execute
    :param args:    Arguments to be passed to cursor (for sanitization)
    :return:        The data retrieved, if any
    """
    try:
        #acquire mutex to ensure ACID
        globals.mutex.acquire()
        try:
            c = globals.db_conn.cursor()
            if len(args) == 0:
                c.execute(query)
            else:
                c.execute(query, args)
            globals.db_conn.commit()
            return c.fetchall()
        finally:
            globals.mutex.release()
    except sqlite3.Error as e:
        print(e)

        
def setup():
    database = "database.db"
    globals.db_conn = create_connection(database)
    if globals.db_conn is None:
        print("Error: cannot connect to database")
        return

    query = """CREATE TABLE IF NOT EXISTS users (username text PRIMARY KEY, games_won integer);"""
    execute(query)
    # create tables
    """files = [os.path.join('sql', f) for f in os.listdir('sql') if os.path.isfile(os.path.join('sql', f))]
    for file in files:
        with open(file) as sql_file:
            execute(sql_file.read())"""