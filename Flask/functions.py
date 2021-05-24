from app import *
from flask import(
    Flask,
    render_template,
    make_response,
    abort,
    redirect,
    url_for,
    request
)
from hashlib import sha256
from emod import send_mail
from secrets import token_urlsafe as gen_token
import random
from datetime import datetime, timedelta
from app import *
from sdb import cur, con
from functions import *
from emod import send_mail

def validate():
    if "sbtoken" in request.cookies:
        cur.execute(f"SELECT username FROM users WHERE sbtoken = '{request.cookies.get('sbtoken')}'")
        res = cur.fetchone()
        if res == None:
            return False
        else:
            return res[0]
    else:
        return False

def validate_admin():
    if "sbtoken" in request.cookies:
        cur.execute(f"SELECT username, rank FROM users WHERE sbtoken = '{request.cookies.get('sbtoken')}'")
        res = cur.fetchone()
        if res == None:
            return False
        else:
            if res[1] >= 5:
                return res[0], res[1]
            else:
                return False
    else:
        return False

def check2step(username):
    cur.execute(f"SELECT twostep, verified, email FROM users WHERE username = '{username}'")
    res = cur.fetchone()
    if res[0] == "True" and res[1] == "True":
        return res[2]
    else:
        return False

def checkban(token):
    cur.execute(f"SELECT banned, reason FROM users WHERE sbtoken = '{request.cookies.get('sbtoken')}'")
    res = cur.fetchone()
    if res != None:
        if res[0] == "True":
            return res[1]
        else:
            return False
    else:
        return False

def getsbcoin(username):
    cur.execute(f"SELECT sbcoins FROM users WHERE username = '{username}'")
    res = cur.fetchone()
    return res[0]