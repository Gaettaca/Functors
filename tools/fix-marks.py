#!/usr/bin/python3
"""
Usage:
  manage-submits.py (fetch|fix)

Options:
  -h --help
"""
import os
import gitlab
import git
import docopt
import tqdm
import json
import sys
import yaml
import pytz
import datetime

from gdoc import *

GITLAB_ADMIN_TOKEN = os.environ["GITLAB_ADMIN_TOKEN"]
GITLAB_URL = "https://best-cpp-course-ever.ru"

TZ_MOSCOW = pytz.timezone('Europe/Moscow')
TIME_PATTERN = "%d-%m-%Y %H:%M"

gitlab_api = gitlab.Gitlab(GITLAB_URL, GITLAB_ADMIN_TOKEN)

def fetch():
    ok_submits = []
    
    os.makedirs("students", exist_ok=True)
    for project in tqdm.tqdm(gitlab_api.projects.list(all=True)):
        if project.namespace.name != "students":
            continue

        for pipeline in project.pipelines.list(all=True):
            if pipeline.status == 'success':
                ok_submits.append([pipeline.user['username'], pipeline.ref, pipeline.created_at])

    json.dump(ok_submits, open("submits.json", 'w'))

def put_score_in_gdoc(sheet, task, login, score):
    scores = sheet.worksheet("Оценки")
    student_row = find_login_row(scores, login)

    task_column = find_task_column(scores, task)

    prev_score = scores.cell(student_row, task_column)
    if prev_score.value == '' or int(prev_score.value) < score:
        prev_score.value = str(score)
        scores.update_cells([prev_score])

def get_task_score(deadlines, date, task):
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

    if pytz.utc.localize(date) > deadline + datetime.timedelta(weeks=1):
        task_score = int(0.3 * task_score)

    return task_score
        
def fix():
    list_submits = json.load(open("submits.json"))
    sheet_sheet = get_sheet()
    sheet = sheet_sheet.worksheet("Оценки")
    deadlines = yaml.load(open("../.deadlines.yml"))

    ok_submits = {}
    for username, ref, time in list_submits:
        ok_submits.setdefault(username, []).append((ref, time))

    for username, submits in ok_submits.items():
        student_row = find_login_row(sheet, username)
        if is_deadline_extended(sheet, student_row):
            print("Fixing", username)
            for ref, time in submits:
                if not ref.startswith("submits/"):
                    continue

                time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
                task_name = ref.split("/")[1]

                score = get_task_score(deadlines, time, task_name)
                put_score_in_gdoc(sheet_sheet, task_name, username, score)

if __name__ == "__main__":
    args = docopt.docopt(__doc__)

    if args['fetch']:
        fetch()

    if args['fix']:
        fix()
