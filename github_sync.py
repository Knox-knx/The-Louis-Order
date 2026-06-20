import os
from github import Github

def push_json(local_file, github_file):

    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO")

    if not token or not repo_name:
        print("GitHub sync disabled")
        return

    g = Github(token)
    repo = g.get_repo(repo_name)

    with open(local_file, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        file = repo.get_contents(github_file)

        repo.update_file(
            file.path,
            f"Update {github_file}",
            content,
            file.sha
        )

        print(f"Updated {github_file}")

    except Exception:

        repo.create_file(
            github_file,
            f"Create {github_file}",
            content
        )

        print(f"Created {github_file}")