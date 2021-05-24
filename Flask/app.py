from hashlib import sha256
from emod import send_mail
from secrets import token_urlsafe as gen_token
import random
from datetime import datetime, timedelta
from flask import Flask
import sqlite3
import os
import views

con = sqlite3.connect("main.sdb", check_same_thread=False)

cur = con.cursor()

app = Flask(__name__, template_folder="views")

app.add_url_rule('/', view_func=views.index)
app.add_url_rule('/login', view_func=views.login, methods=["GET", "POST"])
app.add_url_rule('/register', view_func=views.register, methods=["GET", "POST"])
app.add_url_rule('/settings/<setting>', view_func=views.settings, methods=["GET", "POST"])
app.add_url_rule('/', view_func=views.index)
app.add_url_rule('/home', view_func=views.home)
app.add_url_rule('/verify/<token>', view_func=views.verify)
app.add_url_rule('/logout', view_func=views.logout)
app.add_url_rule('/users/ban', view_func=views.user_ban, methods=["GET", "POST"])
app.add_url_rule('/users/<id>', view_func=views.users)
app.add_url_rule('/users/ipban', view_func=views.user_ipban, methods=["GET", "POST"])
app.before_request(views.before_request)
app.after_request(views.after_request)

if __name__ == "__main__":
    app.run("0.0.0.0", 8080)