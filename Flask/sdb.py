import sqlite3
con = sqlite3.connect("main.sdb", check_same_thread=False)
cur = con.cursor()