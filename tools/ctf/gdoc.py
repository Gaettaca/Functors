#!/usr/bin/python3

import os
import sys
import json
import re
import yaml

import gspread

from oauth2client.service_account import ServiceAccountCredentials


SPREADSHEET_ID="19JP0b5PoAWZ6bFq5z1EZKKAme2ZXE2KlG1SDxf5aMF4"
SHAD_GDOC_ACCOUNT=os.environ["SHAD_GDOC_ACCOUNT"]


def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds']    
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(
        json.loads(SHAD_GDOC_ACCOUNT), scope)
    
    gs = gspread.authorize(credentials)
    sheet = gs.open_by_key(SPREADSHEET_ID)
    return sheet


def find_task_column(worksheet, task):
    all_tasks = worksheet.range(2, 6, 2, worksheet.col_count)
    for task_column in range(len(all_tasks)):
        if task == all_tasks[task_column].value:
            return task_column + 6

    raise KeyError("Task {} not found in spreadsheet".format(task))


def sync_task_columns(worksheet, tasks):
    if worksheet.col_count < len(tasks) + 6:
        worksheet.resize(cols=6 + len(tasks))
    
    all_tasks = worksheet.range(2, 6, 2, worksheet.col_count)

    added = []
    tasks = list(set(tasks))    
    for task_cell in all_tasks:
        if not tasks:
            break

        if task_cell.value == "":
            task_cell.value = tasks[0]
            tasks.pop(0)
            added.append(task_cell)
        elif task_cell.value in tasks:
            tasks.remove(task_cell.value)

    worksheet.update_cells(all_tasks)

def find_login_row(worksheet, login):
    all_logins = worksheet.range(3, 3, worksheet.row_count, 3)

    # Gitlab converts names to lowercase and replaces '.' with '-'
    login = login.lower().replace('.', '-')
    for login_row in range(len(all_logins)):
        sheet_name = all_logins[login_row].value.lower().replace('.', '-')
        if sheet_name == login:
            return login_row + 3
    
    raise KeyError("Login {} not found in spreadsheet".format(login))

def is_deadline_extended(worksheet, student_row):
    return worksheet.cell(student_row, 4).value == 'z'

def is_deadline_extended_for_login(sheet, login):
    scores = sheet.worksheet("Оценки")
    try:
        student_row = find_login_row(scores, login)
    except KeyError:
        return False
    return is_deadline_extended(scores, student_row)

def add_new_login(worksheet, git, full_name, login):
    if len(full_name) == 0 or re.match("\W", full_name[0], flags=re.UNICODE):
        raise ValueError("Name looks fishy")

    worksheet.append_row(['=HYPERLINK("{}";"git")'.format(git), full_name, login])


def put_score_in_gdoc(sheet, task, login, score, full_name, git):
    scores = sheet.worksheet("Оценки")
    try:
        student_row = find_login_row(scores, login)
    except KeyError:
        add_new_login(scores, git, full_name, login)
        student_row = find_login_row(scores, login)

    task_column = find_task_column(scores, task)

    prev_score = scores.cell(student_row, task_column)
    if prev_score.value == '' or int(prev_score.value) < score:
        prev_score.value = str(score)
        scores.update_cells([prev_score])


if __name__ == "__main__":
    if "sync" in sys.argv:
        sheet = get_sheet()
        scores = sheet.worksheet("Оценки")

        deadlines = yaml.load(open(".deadlines.yml"))
        tasks = []
        for group in deadlines:
            for _, task in group["tasks"]:
                tasks.append(task)
    
        sync_task_columns(scores, tasks)
