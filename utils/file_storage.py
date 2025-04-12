import json
import os

PROJECTS_FILE = "projects.json"

def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return {}
    with open(PROJECTS_FILE, "r") as f:
        return json.load(f)



def save_projects(projects_data):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects_data, f, indent=4)
