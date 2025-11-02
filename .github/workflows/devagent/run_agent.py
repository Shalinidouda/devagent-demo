# # This is a basic workflow to help you get started with Actions

# name: CI

# # Controls when the workflow will run
# on:
#   # Triggers the workflow on push or pull request events but only for the "main" branch
#   push:
#     branches: [ "main" ]
#   pull_request:
#     branches: [ "main" ]

#   # Allows you to run this workflow manually from the Actions tab
#   workflow_dispatch:

# # A workflow run is made up of one or more jobs that can run sequentially or in parallel
# jobs:
#   # This workflow contains a single job called "build"
#   build:
#     # The type of runner that the job will run on
#     runs-on: ubuntu-latest

#     # Steps represent a sequence of tasks that will be executed as part of the job
#     steps:
#       # Checks-out your repository under $GITHUB_WORKSPACE, so your job can access it
#       - uses: actions/checkout@v4

#       # Runs a single command using the runners shell
#       - name: Run a one-line script
#         run: echo Hello, world!

#       # Runs a set of commands using the runners shell
#       - name: Run a multi-line script
#         run: |
#           echo Add other actions to build,
#           echo test, and deploy your project.
# devagent/run_agent.py
import os
import subprocess
from pathlib import Path
from github import Github

def run(cmd):
    print("> " + cmd)
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(res.stdout)
    if res.returncode != 0:
        print("ERR:", res.stderr)
    return res

# 1) Find python files to process (exclude devagent folder)
py_files = [str(p) for p in Path(".").rglob("*.py") if "devagent" not in str(p)]

def add_module_docstring(file_path):
    p = Path(file_path)
    text = p.read_text()
    # very simple check: if file starts with triple-quote in first 5 lines, skip
    first_lines = "\n".join(text.splitlines()[:5])
    if '"""' in first_lines or "'''" in first_lines:
        print(f"Docstring already exists in {file_path}")
        return False
    # Create a simple docstring using file name and functions names
    module_name = p.stem
    # get function names (very naive)
    func_names = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("def "):
            name = line.split("def ")[1].split("(")[0]
            func_names.append(name)
    func_list = ", ".join(func_names) if func_names else "no functions"
    doc = f'"""{module_name}.py - contains {func_list}"""\n\n'
    p.write_text(doc + text)
    print(f"Added docstring to {file_path}")
    return True

changed = False
for f in py_files:
    if add_module_docstring(f):
        changed = True

# Create tests folder and a very small test (optional)
tests_dir = Path("generated_tests")
tests_dir.mkdir(exist_ok=True)
if Path("example.py").exists():
    tf = tests_dir / "test_example.py"
    if not tf.exists():
        tf.write_text(
            "from example import add\n\ndef test_add():\n    assert add(2,3) == 5\n"
        )
        changed = True

# If nothing changed, exit
if not changed:
    print("No changes made by DevAgent.")
    exit(0)

# Git operations: create branch, commit, push, PR
run("git config user.email 'devagent@example.com'")
run("git config user.name 'DevAgent Bot'")

branch_name = "devagent/auto-docs"
# create branch from main
run(f"git checkout -b {branch_name} || git checkout {branch_name}")
run("git add .")
run("git commit -m 'DevAgent: add docstrings and tests' || echo 'nothing to commit'")
run(f"git push -u origin {branch_name} --force")

# Create PR via GitHub API if token is present
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if GITHUB_TOKEN:
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    if not repo_name:
        print("GITHUB_REPOSITORY not set in env; cannot create PR via API.")
    else:
        gh = Github(GITHUB_TOKEN)
        repo = gh.get_repo(repo_name)
        pr = repo.create_pull(
            title="DevAgent suggestions: docstrings & tests",
            body="Automated suggestions: docstrings added and basic unit tests generated.",
            head=branch_name,
            base=repo.default_branch,
        )
        print("PR created:", pr.html_url)
else:
    print("No GITHUB_TOKEN found; PR not created via API. Branch pushed.")

