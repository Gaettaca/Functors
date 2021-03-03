#!/usr/bin/python3
import os
import sys
import uuid
import urllib
import requests
import redis
import functools
import gitlab
import yaml
import pytz
import datetime
import re
import hmac

import logging.config

from flask import render_template, redirect, request, session, Flask, url_for, abort
from werkzeug.local import LocalProxy

import gdoc

# ================================================================================

SELF_URL=os.environ["CTF_SELF_URL"]
GITLAB_URL = "https://best-cpp-course-ever.ru"
GITLAB_REPO_NAME="prime/shad-cpp"

# For user auth
GITLAB_CLIENT_ID = os.environ["GITLAB_CLIENT_ID"]
GITLAB_CLIENT_SECRET = os.environ["GITLAB_CLIENT_SECRET"]
GITLAB_REDIRECT_URI = SELF_URL + "/login_finish"

# For user registration
GITLAB_ADMIN_TOKEN = os.environ["GITLAB_ADMIN_TOKEN"]
SHAD_REGISTRATION_SECRET = os.environ["SHAD_REGISTRATION_SECRET"]
GITLAB_GROUP = "students"

# Flask internal
FLASK_SECRET=os.environ["FLASK_SECRET"]

# For API
TESTER_TOKEN=os.environ["TESTER_TOKEN"]

# Crashmes
CRASHME_KEY=os.environ["CRASHME_KEY"].strip()

TZ_MOSCOW = pytz.timezone('Europe/Moscow')
TIME_PATTERN = "%d-%m-%Y %H:%M"

# ================================================================================

@LocalProxy
def wsgi_errors_stream():
    return request.environ['wsgi.errors'] if request else sys.stderr

logging.config.dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] [%(levelname)s] %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://web.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

logger = logging.getLogger("ctf")

redis = redis.StrictRedis()

gitlab_api = gitlab.Gitlab(GITLAB_URL, GITLAB_ADMIN_TOKEN)

app = Flask(__name__)
app.secret_key = FLASK_SECRET

# ================================================================================

# Fix resource caching
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if "gitlab" not in session:
            return redirect(url_for("signin"))

        return f(*args, **kwargs)
    return decorated


class GitlabOAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self._token = token

    def __call__(self, r):
        r.headers["Authorization"] = "Bearer " + self._token
        return r

# ================================================================================

def fetch_deadlines():
    raw_rsp = requests.get(GITLAB_URL + "/prime/shad-cpp/raw/master/.deadlines.yml",
       auth=GitlabOAuth(GITLAB_ADMIN_TOKEN))
    raw_rsp.raise_for_status()

    return yaml.load(raw_rsp.content)

# ================================================================================


def build_dashboard(deadlines):
    dashboard = []
    for group in deadlines:
        start_time = TZ_MOSCOW.localize(datetime.datetime.strptime(
            group["start"], TIME_PATTERN))

        # Don't show tasks that are not started yet.
        if not session["gitlab"]["is_admin"] and start_time > datetime.datetime.now(TZ_MOSCOW):
            continue
        
        dashboard_group = []
        for score, task_name in group["tasks"]:
            dashboard_group.append({"name": task_name, "score": score, "solved": False})

        dashboard.append({
            "name": group["name"],
            "deadline": group["deadline"],
            "tasks": dashboard_group
        })

    return dashboard


def fetch_submit_status(dashboard):
    pipe = redis.pipeline()
    for group in dashboard:
        for task in group["tasks"]:
            pipe.hget("result:{}:{}".format(session["gitlab"]["username"], task["name"]), "ok")

    statuses = pipe.execute()
    i = 0
    
    for group in dashboard:
        for task in group["tasks"]:
            task["solved"] = statuses[i] == b"1"
            i += 1


@app.route("/")
@requires_auth
def main_page():
    deadlines = fetch_deadlines()
    dashboard = build_dashboard(deadlines)
    fetch_submit_status(dashboard)
    
    return render_template("tasks.html",
       base_repo_url=GITLAB_URL+"/prime/shad-cpp/blob/master",
       tasks=dashboard)


@app.route("/login")
def login():
    oauth_state = uuid.uuid4().hex
    session["oauth_state"] = oauth_state
    
    return redirect(GITLAB_URL + "/oauth/authorize?" + urllib.parse.urlencode({
        "client_id": GITLAB_CLIENT_ID,
        "redirect_uri": GITLAB_REDIRECT_URI,
        "response_type": "code",
        "state": oauth_state,
    }))

    
@app.route("/login_finish")
def login_finish():
    code = request.args["code"]
    state = request.args["state"]

    if "oauth_state" not in session or state != session["oauth_state"]:
        abort(500)

    auth_rsp = requests.post(GITLAB_URL + "/oauth/token", data={
        "client_id": GITLAB_CLIENT_ID,
        "client_secret": GITLAB_CLIENT_SECRET,
        "redirect_uri": GITLAB_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code
    })

    auth_rsp.raise_for_status()
    gitlab_token = auth_rsp.json()["access_token"]

    user_rsp = requests.get(GITLAB_URL + "/api/v4/user", auth=GitlabOAuth(gitlab_token))
    user_rsp.raise_for_status()
    user = user_rsp.json()

    session["gitlab"] = {
        "token": gitlab_token,
        "username": user["username"],
        "id": user["id"],
        "is_admin": user.get("is_admin", False),
    }
    session.permanent = True

    return redirect(url_for("main_page"))


@app.route("/logout")
def logout():
    del session["gitlab"]
    return redirect(url_for("main_page"))


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        return render_template("signin.html")

    if request.form["secret"] != SHAD_REGISTRATION_SECRET:
        return render_template("signin.html", error_message="Invalid secret code")

    try:
        register_new_user(
            request.form["username"],
            request.form["firstname"],
            request.form["lastname"],
            request.form["email"],
            request.form["password"])
    except gitlab.GitlabError as ex:
        logger.error("User registration failed: {}".format(ex.error_message))
        return render_template("signin.html", error_message=ex.error_message)

    return redirect(url_for("login"))


def decode_flag(flag):
    msg, sig = flag[5:-1].rsplit(':', 1)
    challenge, date = msg.split(":", 1)

    print(sig, hmac.new(CRASHME_KEY.encode("utf8"), msg=msg.encode("utf8")).hexdigest())
    if sig != hmac.new(CRASHME_KEY.encode("utf8"), msg=msg.encode("utf8")).hexdigest():
        raise ValueError("invalid signature")

    return challenge, date


@app.route("/submit", methods=["GET", "POST"])
@requires_auth
def submit():
    if request.method == "GET":
        return render_template("submit.html")

    flag = request.form["flag"]

    try:
        challenge, date = decode_flag(flag)
    except ValueError as ex:
        return render_template("submit.html", error_message=ex.args[0])

    user_id = int(session["gitlab"]["id"])
    user = gitlab_api.users.get(user_id)
    login = user.username
    repo_url = GITLAB_URL + "/" + GITLAB_GROUP + "/" + login

    sheet = gdoc.get_sheet()
    task_score = get_task_score(challenge, gdoc.is_deadline_extended_for_login(sheet, login))
    gdoc.put_score_in_gdoc(sheet, challenge, login, task_score, user.name, repo_url)
    
    pipe = redis.pipeline()
    pipe.hset("result:{}:{}".format(login, challenge), "ok", "1")
    pipe.hset("result:{}:{}".format(login, challenge), "flag", flag)
    pipe.execute()

    return redirect(url_for("main_page"))
    
# ================================================================================


def get_task_score(task, deadline_extended=False):
    deadlines = fetch_deadlines()

    deadline=None
    start_time=None
    task_score=None
    for group in deadlines:
        for score, task_name in group["tasks"]:
            if task_name == task:
                start_time = TZ_MOSCOW.localize(datetime.datetime.strptime(
                    group["start"], TIME_PATTERN))
                deadline = TZ_MOSCOW.localize(datetime.datetime.strptime(
                    group["deadline"], TIME_PATTERN))
                task_score = score

    if deadline is None:
        abort(404)

    if datetime.datetime.now(TZ_MOSCOW) < start_time:
        abort(403)

    if deadline_extended:
        deadline += datetime.timedelta(weeks=1)
        
    if datetime.datetime.now(TZ_MOSCOW) > deadline:
        task_score = int(0.3 * task_score)

    return task_score


@app.route("/api/report", methods=["POST"])
def report():
    token = request.form["token"]
    if token != TESTER_TOKEN:
        abort(403)

    deadlines = fetch_deadlines()
    task = request.form["task"]

    user_id = int(request.form["user_id"])
    user = gitlab_api.users.get(user_id)
    login = user.username
    repo_url = GITLAB_URL + "/" + GITLAB_GROUP + "/" + login

    sheet = gdoc.get_sheet()
    task_score = get_task_score(task, gdoc.is_deadline_extended_for_login(sheet, login))
    gdoc.put_score_in_gdoc(sheet, task, login, task_score, user.name, repo_url)

    # Also save to status to redis.
    pipe = redis.pipeline()
    pipe.hset("result:{}:{}".format(login, task), "ok", "1")
    pipe.execute()
    
    return ""

# ================================================================================

def register_new_user(username, firstname, lastname, email, password):
    course_group = None
    for group in gitlab_api.groups.search(GITLAB_GROUP):
        if group.name == GITLAB_GROUP:
            course_group = group
            break
    else:
        raise ValueError("Gitlab group {} not found".format(GITLAB_GROUP))
    
    logger.info("Creating user: {}".format({
        "username": username,
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
    }))
    
    new_user = gitlab_api.users.create({
        "email": email,
        "username": username,
        "name": firstname + " " + lastname,
        "external": True,
        "password": password,
        "confirm": False,
    })
    logger.info("Gitlab user created {}".format(new_user))

    project = gitlab_api.projects.create({
        "name": username,
        "namespace_id": course_group.id,
        "builds_enabled": True,
    })
    logger.info("Git project created {}".format(project))

    member = gitlab_api.project_members.create({
        "user_id": new_user.id,
        "project_id": project.id,
        "access_level": gitlab.MASTER_ACCESS,
    })
    logger.info("Access to project granted {}".format(member))

# ================================================================================

if __name__ == "__main__":    
    app.run()
