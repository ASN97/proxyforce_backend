from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
import json
import os

import openai
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


# Load environment variables
load_dotenv()\

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

# Constants
PROJECTS_FILE = "projects.json"

# ------------------------- Models -------------------------

class ChatRequest(BaseModel):
    message: str
    role: str
    tier: str

class ChatMessage(BaseModel):
    id: str
    content: str
    sender: str
    timestamp: datetime

class TaskModel(BaseModel):
    name: str
    assignee: str
    deadline: str
    priority: str
    description: str = ""
    status: str = "not-started"

# ------------------------- Helpers -------------------------

def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return {"projects": {}}
    with open(PROJECTS_FILE, "r") as f:
        return json.load(f)

def save_projects(data):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_project_context(project_id: str) -> str:
    data = load_projects()
    project = data.get("projects", {}).get(project_id)
    if not project:
        return "Project details not found."

    context = f"""You are a Project Manager AI with 3 years of experience.
You are managing the following project:

Project ID: {project_id}
Name: {project.get("name", "N/A")}
Description: {project.get("description", "N/A")}
Status: {project.get("status", "N/A")}
Progress: {project.get("progress", "N/A")}%
Deadline: {project.get("deadline", "N/A")}
Budget: ${project.get("budget", "N/A")} (Used: ${project.get("budgetUsed", "N/A")})
Tech Stack: {project.get("techStack", "N/A")}
Current Stage: {project.get("currentStage", "N/A")}
Buffer: {project.get("buffer", "N/A")} days

Team Members:
"""
    for tm in project.get("team_members", []):
        context += f"- {tm['name']} ({tm['email']})\n"

    context += "\nStakeholders:\n"
    for sh in project.get("stakeholders", []):
        context += f"- {sh['name']} ({sh['email']}, {sh['role']})\n"

    info = project.get("additional_info", {})
    context += f"\nObjectives: {info.get('objectives', 'N/A')}\nSuccess Criteria: {info.get('successCriteria', 'N/A')}\n"
    context += "Answer all queries as a professional Project Manager with full awareness of the above project details."
    return context

# ------------------------- Routes -------------------------

@app.get("/api/projects")
def get_all_projects():
    data = load_projects()
    return [
        {
            "id": pid,
            "name": p.get("name"),
            "description": p.get("description"),
            "status": p.get("status", "Not Started"),
            "deadline": p.get("deadline"),
            "progress": p.get("progress", 0),
            "teamSize": len(p.get("team_members", []))
        }
        for pid, p in data.get("projects", {}).items()
    ]

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    data = load_projects()
    project = data.get("projects", {}).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.get("/api/roles/{role}/theme")
def get_role_theme(role: str):
    role_themes = {
        "pm": {"title": "Project Manager", "gradient": "from-blue-500 to-blue-700"},
        "sales": {"title": "Sales Executive", "gradient": "from-red-500 to-red-700"},
        "marketing": {"title": "Marketing Lead", "gradient": "from-green-500 to-green-700"}
    }
    theme = role_themes.get(role)
    if not theme:
        raise HTTPException(status_code=404, detail="Role not found")
    return theme

@app.get("/api/tiers/{tier}")
def get_tier_info(tier: str):
    tier_info = {
        "1": {"years": "2 Years", "title": "Tier 1"},
        "2": {"years": "5 Years", "title": "Tier 2"},
        "3": {"years": "10+ Years", "title": "Tier 3"}
    }
    info = tier_info.get(tier)
    if not info:
        raise HTTPException(status_code=404, detail="Tier not found")
    return info

@app.post("/api/projects/{project_id}/chat", response_model=ChatMessage)
async def send_chat_message(project_id: str, chat: ChatRequest = Body(...)):
    try:
        system_prompt = get_project_context(project_id)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chat.message}
            ],
            temperature=0.7
        )
        reply_text = response.choices[0].message.content.strip()
    except Exception as e:
        reply_text = f"⚠️ OpenAI error: {str(e)}"

    return ChatMessage(
        id=str(datetime.now().timestamp()),
        content=reply_text,
        sender="ai",
        timestamp=datetime.now()
    )

# ------------------------- Run (optional if using `uvicorn`) -------------------------

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
