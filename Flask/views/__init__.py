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
from functions import *
from emod import send_mail
from sdb import cur, con

def before_request():
    ip = request.environ.get('REMOTE_ADDR')
    cur.execute(f"SELECT ip FROM ipbans WHERE ip = '{ip}'")
    res = cur.fetchone()
    if res != None:
        abort(403)
    else:
        if "sbtoken" in request.cookies:
            val = checkban(request.cookies.get("sbtoken"))
            if val != False:
                return render_template("banned.html", reason=val)
        else:
            pass

def after_request(response):
    con.commit()
    response.headers["server"] = "Scratchblox Web Server"
    return response

def index():
    return redirect(url_for("home"))

def home():
    val = validate()
    if val == False:
        return redirect(url_for("login"))
    else:
        chk = checkban(request.cookies.get("sbtoken"))
        if chk == False:
            coins = getsbcoin(val)
            print(coins)
            return render_template("home.html", username=val, sbcoins=coins)
        else:
            return render_template("banned.html", reason=chk)

def login():
    if request.method == "POST":
        if "method" in request.form and request.form.get("method") == "2step":
            username = request.form.get("username")
            password = request.form.get("password")
            code = request.form.get("code")
            res = check2step(username)
            if res == False:
                return redirect(url_for("home"))
            else:
                cur.execute(f"SELECT sbtoken FROM users WHERE username='{username}' AND password='{password}' AND code='{code}'")
                res = cur.fetchone()
                if res == None:
                    return render_template("twostep.html", message="Incorrect code!", username=username, password=password)
                else:
                    response = make_response(redirect(url_for("home")))
                    response.set_cookie("sbtoken", res[0])
                    return response
        else:
            username = request.form.get("username")
            pswdraw = request.form.get("password")
            password = sha256(pswdraw.encode()).hexdigest()
            cur.execute(f"SELECT sbtoken FROM users WHERE username='{username}' AND password='{password}'")

            res = cur.fetchone()
            if res == None:
                return render_template("login.html", message="Username or Password is invalid.")
            else:
                res = check2step(username)
                if res != False:
                    code = random.randint(1000, 9999)
                    cur.execute(f"UPDATE users SET code = '{code}' WHERE username='{username}' ")
                    send_mail(res, "no-reply", f"This is your Scratchblox verification code: {code}.")
                    con.commit()
                    return render_template("twostep.html", username=username, password=password)
                else:
                    cur.execute(f"SELECT sbtoken FROM users WHERE username='{username}' AND password='{password}'")

                    res = cur.fetchone()
                    response = make_response(redirect(url_for("home")))
                    response.set_cookie("sbtoken", res[0])
                    return response
    else:
        val = validate()
        if val == False:
            return render_template("login.html")
        else:
            return redirect(url_for("home"))

def register():
    if request.method == "POST":
        username = request.form.get("username")
        pswdraw = request.form.get("password")
        password = sha256(pswdraw.encode()).hexdigest()
        cur.execute(f"SELECT username FROM users WHERE username = '{username}'")
        res = cur.fetchone()
        if res == None:
            if len(username) > 3:
                if len(username) < 12:
                    newtoken = gen_token(24)
                    cur.execute("SELECT COUNT(*) FROM users")
                    newid = cur.fetchone()[0] + 1
                    cur.execute("INSERT INTO users (id, username, password, friends, banned, rank, reason, character, sbtoken, twostep, email, verified, code, ip, claimedemail, sbcoins) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (newid, username, password, "[]", "False", 1, None, None, newtoken, "False", None, "False", 0000, request.environ.get('REMOTE_ADDR'), "False", 0))
                    con.commit()
                    response = make_response(redirect(url_for("home")))
                    response.set_cookie("sbtoken", newtoken)
                    return response
                else:
                    return render_template("register.html", message="Username must be less than 11 chars!")
            else:
                 return render_template("register.html", message="Username must be more than 3 chars!")
        else:
            return render_template("register.html", message="Username is taken!")
    else:
        val = validate()
        if val == False:
            return render_template("register.html")
        else:
            return redirect(url_for("home"))

def verify(token):
    cur.execute(f"SELECT for FROM verifytokens WHERE token='{token}'")
    res = cur.fetchone()
    cur.execute(f"SELECT claimedemail, sbcoins FROM users WHERE username='{validate()}'")
    claimedemail = cur.fetchone()
    if res == None:
        return abort(404)
    else:
        if claimedemail[0] == "False":
            cur.execute(f"UPDATE users SET verified = 'True' WHERE username = '{res[0]}'")
            cur.execute(f"DELETE FROM verifytokens WHERE token='{token}'")
            cur.execute(f"UPDATE users SET sbcoins = '{claimedemail[1] + 100}' WHERE username = '{res[0]}'")
            cur.execute(f"UPDATE users SET claimedemail = 'True' WHERE username = '{res[0]}'")
            con.commit()
            return "Successfully Verified! 100 sbcoins! Have been added to your account"
        else:
            cur.execute(f"UPDATE users SET verified = 'True' WHERE username = '{res[0]}'")
            cur.execute(f"DELETE FROM verifytokens WHERE token='{token}'") 
            con.commit()
            return "Successfully Verified!"

def settings(setting):
    val = validate()
    username = val
    if val == False:
        return redirect(url_for("login"))
    else:
        settings = ['twostep']
        if setting in settings:
            if setting == "twostep":
                if request.method == "POST":
                    email = request.form.get("email")
                    passraw = request.form.get("password")
                    password = sha256(passraw.encode()).hexdigest()
                    cur.execute(f"SELECT id FROM users WHERE username = '{username}' AND password='{password}'")
                    res = cur.fetchone()
                    if res == None:
                        return render_template("twostepset.html", status="Incorrect password please try again.", style="color: red;")
                    else:
                        cur.execute(f"UPDATE users SET email = '{email}' WHERE username = '{username}' AND password='{password}'")
                        cur.execute(f"UPDATE users SET verified = 'False' WHERE username = '{username}' AND password='{password}'")
                        cur.execute(f"UPDATE users SET twostep = 'True' WHERE username = '{username}' AND password='{password}'")
                        token = gen_token(24)
                        con.commit()
                        cur.execute("INSERT INTO verifytokens (token, for) VALUES (?, ?)", (token, username))
                        send_mail(email, "no-reply", "Click this link to verify: https://scratchblox.tk/verify/" + token)
                        con.commit()

                        return render_template("twostepset.html", status=f"Verify this email: {email}", style="color: green;")
                else:
                    cur.execute(f"SELECT verified, email, twostep FROM users WHERE username = '{username}'")
                    res = cur.fetchone()
                    if res[2] == "False":
                        return render_template("twostepset.html", status="2 step verification is turned off.")
                    elif res[2] == "True" and res[0] == "False":
                        return render_template("twostepset.html", status=f"2 step verification is turned on but your email is not verified, email: {res[1]}.")
                    elif res[2] == "True" and res[0] == "True":
                        return render_template("twostepset.html", status=f"2 step verification is turned on. Email: {res[1]}.")
                    
        else:
            abort(404)

def sitemap():
    rules = []
    for rule in app.url_map.iter_rules():
        numbers = []
        for letter in rules:
            i = 0
            if letter == "<":
                while True:
                    numbers.append(i)
                    if rule[i] == ">":
                        break
                    i += 1
                i += 1
        editingrule = list(rule)
        x = 0
        for number in numbers:
            editingrule[number] = ""
            if len(editingrule) == number + 1:
                editingrule[number] = "*"
            x += 1
        editedrule = "".join(editingrule)
        rules.append("https://scratchblox.tk" + editedrule)
    return rules

def logout():
    if "referer" in request.headers:
        try:
            request.headers.get("referer").index("scratchblox.tk")
            response = make_response(redirect(url_for("login")))
            response.set_cookie("sbtoken", "", max_age=0)
            return response
        except:
            return abort(404)
    else:
        return abort(404)

def user_ban():
    if request.method == 'POST':
        val = validate_admin()
        if val == False:
            return abort(404)
        else:
            usertoban = request.form.get("username")
            reason = request.form.get("reason")

            if reason == "" or None:
                return render_template("banner.html", username=val[0], color="red", message="Username reason cannot be left blank.")
            else:
                cur.execute(f"SELECT banned, rank FROM users WHERE username='{usertoban}'")
                res = cur.fetchone()
                if res == None:
                    return render_template("banner.html", username=val[0], color="red", message=f"User {usertoban} does not exsist.")
                else:
                    if res[1] >= val[1]:
                        return render_template("banner.html", username=val[0], color="red", message="Cannot ban or unban user with more or equal power than you.")
                    else:
                        if res[0] == "True":
                            cur.execute(f"UPDATE users SET banned='False' WHERE username='{usertoban}'")
                            con.commit()
                            return render_template("banner.html", username=val[0], color="green", message=f"Unbanned {usertoban}.")
                        else:
                            cur.execute(f"UPDATE users SET banned='True' WHERE username='{usertoban}'")
                            cur.execute(f"UPDATE users SET reason='{reason}' WHERE username='{usertoban}'")
                            con.commit()
                            return render_template("banner.html", username=val[0], color="yellow", message=f"Banned {usertoban}.")
    else:
        val = validate_admin()
        if val == False:
            return abort(404)
        else:
            return render_template("banner.html", username=val[0])
  
def user_ipban():
    if request.method == 'POST':
        val = validate_admin()
        if val == False:
            return abort(404)
        else:
            usertoban = request.form.get("username")
            reason = request.form.get("reason")

            if reason == "" or None:
                return render_template("banner.html", username=val[0], color="red", message="Username reason cannot be left blank.")
            else:
                cur.execute(f"SELECT ip, rank FROM users WHERE username='{usertoban}'")
                ip_rank = cur.fetchone()
                if ip_rank == None:
                    return render_template("banner.html", username=val[0], color="red", message=f"User {usertoban} does not exsist.")
                else:
                    if ip_rank >= val[1]:
                        return render_template("banner.html", username=val[0], color="red", message="Cannot ip ban or unban user with more or equal power than you.")
                    else:
                        cur.execute("SELECT ip FROM ipbans WHERE ip='{ip}'")
                        res = cur.fetchone()
                        if not res == None:
                            cur.execute(f"DELETE FROM ipbans WHERE ip='{ip_rank[0]}'")
                            con.commit()
                            return render_template("banner.html", username=val[0], color="green", message=f"Unipbanned {usertoban}.")
                        else:
                            cur.execute(f"INSERT INTO ipbans (ip, reason) VALUES (?, ?)", (ip_rank[0], reason))
                            con.commit()
                            return render_template("banner.html", username=val[0], color="yellow", message=f"Banned {usertoban}.")
    else:
        val = validate_admin()
        if val == False:
            return abort(404)
        else:
            return render_template("banner.html", username=val[0])

def users(id):
    cur.execute(f"SELECT username, rank FROM users WHERE id='{id}'")
    res = cur.fetchone()
    if res == None:
        return abort(404)
    else:
        if res[1] >= 5:
            if id == "1":
                return render_template("user.html", username=res[0] + "☑️", img="https://u.cubeupload.com/Oooof/Webcapture2142021155.jpeg")
            else:
                return render_template("user.html", username=res[0] + "☑️")
        else:
            return render_template("user.html", username=res[0])

def redeem():
    if request.method == "POST":
        pass
    else:
        val = validate()
        if val == False:
            return redirect(url_for("login"))