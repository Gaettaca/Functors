#!/usr/bin/python3
"""
Usage:
  manage-submits.py pull-submits

Options:
  -h --help
"""
import os
import gitlab
import git
import docopt
import tqdm

GITLAB_ADMIN_TOKEN = os.environ["GITLAB_ADMIN_TOKEN"]
GITLAB_URL = "https://best-cpp-course-ever.ru"

gitlab_api = gitlab.Gitlab(GITLAB_URL, GITLAB_ADMIN_TOKEN)

def pull_submits():
    os.makedirs("students", exist_ok=True)
    for project in tqdm.tqdm(gitlab_api.projects.list(all=True)):
        if project.namespace.name != "students":
            continue

        local_path = os.path.join("students", project.name)
        
        if not os.path.exists(local_path):
            git.Git().clone(project.ssh_url_to_repo, local_path)

        repo = git.Repo(local_path)
        repo.remotes.origin.fetch()

        empty = True
        for branch in repo.remotes.origin.refs:
            if "initial" in branch.name:
                empty = False

        if empty:
            continue

        if repo.active_branch.name != "initial":
            git.Git(local_path).checkout("-b", "initial", "origin/initial")

        for branch in repo.remotes.origin.refs:
            if "submits/" not in branch.name:
                continue

            git.Git(local_path).merge("--allow-unrelated-histories", branch.name)

if __name__ == "__main__":
    args = docopt.docopt(__doc__)

    if 'pull-submits' in args:
        pull_submits()
