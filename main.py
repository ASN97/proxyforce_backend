# main.py

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional
import random,openai
import uvicorn
from typing import Dict

app = FastAPI(title="ProxyForce Chat Backend", version="1.0")

# Allow all origins for development (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
###########################################################################
# MODELS
###############################################################################

# Models for Project-related endpoints
class Milestone(BaseModel):
    id: int
    name: str
    deadline: datetime
    status: str  # "completed", "in-progress", "not-started"
    progress: int  # percentage

class TeamMember(BaseModel):
    id: int
    name: str
    role: str
    avatar: Optional[str] = None
    tasks: int = 0
    completed: int = 0

class Project(BaseModel):
    id: int
    name: str
    description: str
    startDate: datetime
    deadline: datetime
    progress: int  # percentage complete
    budget: float
    budgetUsed: float
    milestones: List[Milestone] = []
    tasks: List[dict] = []       # will hold task dictionary objects
    teamMembers: List[TeamMember] = []
    stakeholders: List[dict] = []  # e.g., {"name": "Stakeholder Name", ...}

# Model for task creation/request
class TaskCreate(BaseModel):
    name: str
    assignee: str
    deadline: datetime
    priority: str  # "low", "medium", "high"
    description: Optional[str] = None

class Task(TaskCreate):
    id: int
    status: str  # "not-started", "in-progress", "completed"

# Models for Chat
class ChatMessage(BaseModel):
    id: str
    content: str
    sender: str  # "user" or "ai"
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str

# Models for Email
class EmailTemplate(BaseModel):
    recipient: str  # "all" or a specific stakeholder name
    subject: str
    content: str
    includeTimeline: bool = True
    includeTaskSummary: bool = True

# Models for Timeline
class TimelineData(BaseModel):
    milestones: List[Milestone]
    insights: Optional[List[dict]] = None  # e.g., [{"type": "warning", "message": "Delay risk detected."}]

# Models for Risk Analysis
class RiskReport(BaseModel):
    report: str
    risks: List[dict]  # Each risk: {"description": str, "impact": str, "probability": int, "mitigation": str, "contingency": str}
    completionProbability: int


###############################################################################
# SAMPLE DATA STORE (in-memory)
###############################################################################

# This is a fake data store. In production, you would use a database.
PROJECTS = {
    1: Project(
        id=1,
        name="ProxyForce Alpha",
        description="A project for creating dynamic AI teams.",
        startDate=datetime.now() - timedelta(days=30),
        deadline=datetime.now() + timedelta(days=60),
        progress=45,
        budget=100000,
        budgetUsed=45000,
        milestones=[
            Milestone(id=1, name="Design Complete", deadline=datetime.now() - timedelta(days=10), status="completed", progress=100),
            Milestone(id=2, name="Prototype", deadline=datetime.now() + timedelta(days=10), status="in-progress", progress=50),
            Milestone(id=3, name="Final Release", deadline=datetime.now() + timedelta(days=60), status="not-started", progress=0),
        ],
        tasks=[],
        teamMembers=[
            TeamMember(id=1, name="Alice Smith", role="Developer", avatar="https://randomuser.me/api/portraits/women/1.jpg", tasks=5, completed=3),
            TeamMember(id=2, name="Bob Johnson", role="Designer", avatar="https://randomuser.me/api/portraits/men/2.jpg", tasks=4, completed=4),
        ],
        stakeholders=[{"name": "CEO"}, {"name": "CTO"}],
    )
}

# Sample chat messages per project id
PROJECT_CHATS = {
    1: [
        ChatMessage(id="1", content="Welcome to the project chat!", sender="ai", timestamp=datetime.now() - timedelta(minutes=10)),
    ]
}

# Global task ID counter
TASK_ID_COUNTER = 1

###############################################################################
# API ENDPOINTS
###############################################################################


import json
import os

PROJECTS_FILE = "projects.json"

def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return {"projects": {}}
    with open(PROJECTS_FILE, "r") as f:
        return json.load(f)

def save_projects(data):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(data, f, indent=2)
# Get all projects (frontend format)

@app.get("/api/projects")
async def get_projects():
    data = load_projects()
    return [
        {
            "id": pid,
            "name": p["name"],
            "description": p["description"],
            "status": p.get("status", "Not Started"),
            "deadline": p["deadline"],
            "progress": p.get("progress", 0),
            "teamSize": len(p.get("team_members", []))
        }
        for pid, p in data.get("projects", {}).items()
    ]

# Get full data of one project
@app.get("/api/projects/{project_id:str}")
async def get_project_details(project_id: str):
    data = load_projects()
    project = data["projects"].get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# Create a new project
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class TeamMember(BaseModel):
    name: str
    email: str
    skills: str
    hoursPerWeek: str
    hourlyWage: str

class Stakeholder(BaseModel):
    name: str
    email: str
    role: str

class AdditionalInfo(BaseModel):
    objectives: Optional[str] = None
    successCriteria: Optional[str] = None

class ProjectCreateRequest(BaseModel):
    name: str
    description: str
    startDate: str
    deadline: str
    budget: str
    budgetUsed: str
    currentStage: str
    team_members: List[TeamMember]
    stakeholders: List[Stakeholder]
    techStack: str
    buffer: str
    additional_info: Optional[AdditionalInfo] = None

@app.post("/api/projects")
async def create_project(payload: ProjectCreateRequest):
    data = load_projects()
    new_id = f"p{len(data['projects']) + 1}"
    data["projects"][new_id] = payload.dict()
    save_projects(data)
    return {"message": "Project created", "id": new_id}



    
# PROJECTS ENDPOINTS
@app.get("/api/projects/{project_id}", response_model=Project)
async def get_project(project_id: int):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# TASKS ENDPOINTS
@app.post("/api/projects/{project_id}/tasks", response_model=Task)
async def create_task(project_id: int, task: TaskCreate):
    global TASK_ID_COUNTER
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    new_task = Task(
        id=TASK_ID_COUNTER,
        name=task.name,
        assignee=task.assignee,
        deadline=task.deadline,
        priority=task.priority,
        description=task.description,
        status="not-started",
    )
    TASK_ID_COUNTER += 1
    # Append to the project tasks
    project.tasks.append(new_task.dict())
    return new_task

# CHAT ENDPOINTS
@app.get("/api/projects/{project_id}/chat", response_model=List[ChatMessage])
async def get_chat_messages(project_id: str):
    messages = PROJECT_CHATS.get(project_id, [])
    return messages

@app.post("/api/projects/{project_id}/chat", response_model=ChatMessage)
async def send_chat_message(project_id: int, chat: ChatRequest):
    # Add the user's chat message to our fake chat
    new_message = ChatMessage(
        id=str(datetime.now().timestamp()),
        content=chat.message,
        sender="user",
        timestamp=datetime.now(),
    )
    PROJECT_CHATS.setdefault(project_id, []).append(new_message)
    
    # Simulate an AI response by echoing back with additional text
    ai_response = ChatMessage(
        id=str(datetime.now().timestamp() + random.randint(1, 1000)),
        content=f"AI Response: {chat.message[::-1]}",
        sender="ai",
        timestamp=datetime.now(),
    )
    PROJECT_CHATS[project_id].append(ai_response)
    return ai_response

# TIMELINE ENDPOINTS
@app.get("/api/projects/{project_id}/timeline", response_model=TimelineData)
async def get_project_timeline(project_id: int):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # For this demo, we simply return the project's milestones and a dummy insight
    timeline_data = TimelineData(
        milestones=project.milestones,
        insights=[{"type": "info", "message": "Ensure all milestones are on schedule."}]
    )
    return timeline_data

@app.post("/api/projects/{project_id}/timeline/weekly-plan")
async def generate_weekly_plan(project_id: int):
    # Simulate generating weekly assignments from timeline data
    assignments = [
        {"member": tm.name, "role": tm.role, "tasks": [f"Task {i+1}" for i in range(random.randint(1, 3))]}
        for tm in PROJECTS.get(project_id).teamMembers
    ]
    return {"message": "Weekly plan generated.", "assignments": assignments}

# RISK ENDPOINTS
@app.post("/api/projects/{project_id}/risk", response_model=RiskReport)
async def generate_risk_report(project_id: int):
    # Simulate risk report generation
    risks = [
        {
            "description": "Potential delay in design phase",
            "impact": "high",
            "probability": 70,
            "mitigation": "Increase design team hours",
            "contingency": "Outsource design review",
        },
        {
            "description": "Budget overrun risk",
            "impact": "medium",
            "probability": 40,
            "mitigation": "Regular cost reviews",
            "contingency": "Reallocate funds from marketing",
        },
    ]
    report_text = "Risk Analysis Report:\n" + "\n".join([f"{i+1}. {r['description']} ({r['impact']} Impact, {r['probability']}% probability)" for i, r in enumerate(risks)])
    completion_probability = random.randint(60, 90)
    return RiskReport(report=report_text, risks=risks, completionProbability=completion_probability)

# EMAIL ENDPOINTS
@app.post("/api/projects/{project_id}/email/generate", response_model=EmailTemplate)
async def generate_email_template(project_id: int, template: EmailTemplate):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # Create a dummy email based on project data
    content = f"Status Update for {project.name}:\n\nProgress: {project.progress}% complete.\nUpcoming Milestones:\n"
    for milestone in project.milestones:
        if milestone.status != "completed":
            content += f"- {milestone.name}: due {milestone.deadline.strftime('%b %d')}\n"
    # Optionally add task summaries
    if template.includeTaskSummary:
        content += "\nTask Summary:\n"
        for task in project.tasks:
            content += f"- {task.get('name')} (Status: {task.get('status')})\n"
    return EmailTemplate(
        recipient=template.recipient,
        subject=template.subject or f"{project.name} - Status Update",
        content=content,
        includeTimeline=template.includeTimeline,
        includeTaskSummary=template.includeTaskSummary
    )

# @app.post("/api/projects/{project_id}/email/send")
# async def send_email(project_id: int, template: EmailTemplate):
#     # In a real application, you would integrate with an email service (SMTP, SendGrid, etc.)
#     # Here, we simulate sending the email.
#     print(f"Sending email for project {project_id}:")
#     print(f"Recipient: {template.recipient}")
#     print(f"Subject: {template.subject}")
#     print(f"Content:\n{template.content}")
#     return {"message": "Email sent successfully."}


role_themes = {
    "pm": {
        "title": "Project Manager",
        "gradient": "from-blue-500 to-blue-700"
    },
    "sales": {
        "title": "Sales Executive",
        "gradient": "from-red-500 to-red-700"
    },
    "marketing": {
        "title": "Marketing Lead",
        "gradient": "from-green-500 to-green-700"
    }
}
@app.get("/api/roles/{role}/theme")
async def get_role_theme(role: str):
    if role not in role_themes:
        raise HTTPException(status_code=404, detail="Role not found")
    return role_themes[role]


@app.get("/api/tiers/{tier}")
async def get_tier_info(tier: str):
    tier_info = {
        "1": {"years": "2 Years", "title": "Tier 1"},
        "2": {"years": "5 Years", "title": "Tier 2"},
        "3": {"years": "10+ Years", "title": "Tier 3"}
    }
    if tier not in tier_info:
        raise HTTPException(status_code=404, detail="Tier not found")
    return tier_info[tier]



@app.get("/api/project-stages")
async def get_project_stages():
    """
    Returns a list of project stages.
    """
    return project_stages


###############################################################################
# Run the Application
###############################################################################


###############################################################################
# Pydantic Models
###############################################################################

class AiAssistantResponse(BaseModel):
    name: str
    title: str
    experience: int
    avatar: str
    greeting: str

class ThemeResponse(BaseModel):
    primary: str
    light: str
    border: str
    hover: str

class ChatRequest(BaseModel):
    message: str
    role: str
    tier: str

class ChatResponse(BaseModel):
    message: str

###############################################################################
# Dummy Data for AI Assistant and Theme
###############################################################################

# Dummy assistant data keyed by role
assistant_data: Dict[str, Dict[str, str or int]] = {
    "project-manager": {
        "name": "Ava",
        "title": "Project Manager",
        "experience": 8,
        "avatar": "https://randomuser.me/api/portraits/women/68.jpg",
        "greeting": "Hello, I'm Ava, your project manager AI. How can I assist you today?"
    },
    "sales": {
        "name": "Max",
        "title": "Sales Executive",
        "experience": 5,
        "avatar": "https://randomuser.me/api/portraits/men/75.jpg",
        "greeting": "Hi, I'm Max, your sales AI. What sales insights can I provide today?"
    },
    "marketing": {
        "name": "Lara",
        "title": "Marketing Analyst",
        "experience": 7,
        "avatar": "https://randomuser.me/api/portraits/women/42.jpg",
        "greeting": "Hey, I'm Lara, your marketing AI. Let's analyze some trends!"
    }
}

# Dummy theme data keyed by role (use lower-case keys for consistency)
theme_data: Dict[str, Dict[str, str]] = {
    "project-manager": {
        "primary": "bg-blue-500",
        "light": "bg-blue-100",
        "border": "border border-blue-300",
        "hover": "hover:bg-blue-600"
    },
    "sales": {
        "primary": "bg-red-500",
        "light": "bg-red-100",
        "border": "border border-red-300",
        "hover": "hover:bg-red-600"
    },
    "marketing": {
        "primary": "bg-green-500",
        "light": "bg-green-100",
        "border": "border border-green-300",
        "hover": "hover:bg-green-600"
    }
}



@app.get("/api/theme/{role}", response_model=ThemeResponse)
async def get_theme(role: str):
    """
    Returns theme configuration for the given role.
    """
    key = role.lower()
    theme = theme_data.get(key)
    if not theme:
        # Default to project-manager theme if role is unknown.
        theme = theme_data["project-manager"]
    return ThemeResponse(**theme)

@app.post("/api/chat", response_model=ChatResponse)
async def send_chat_message(chat: ChatRequest):
    """
    Accepts a user's message and returns an AI-generated response.
    This demo endpoint simply echoes back the reversed user message.
    """
    user_message = chat.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # For demonstration, simulate "processing" by reversing the text.
    ai_reply = f"I heard you say: {user_message[::-1]}"
    
    # Alternatively, you could use more advanced logic here.
    return ChatResponse(message=ai_reply)

###############################################################################
# Run the Application
###############################################################################
###############################################################################
# MODELS FOR PROJECT, TASK, CHAT, TIMELINE, EMAIL, RISK
###############################################################################

class Milestone(BaseModel):
    id: int
    name: str
    deadline: datetime
    status: str  # "completed", "in-progress", "not-started"
    progress: int  # percentage

class TeamMember(BaseModel):
    id: int
    name: str
    role: str
    avatar: Optional[str] = None
    tasks: int = 0
    completed: int = 0

class Project(BaseModel):
    id: int
    name: str
    description: str
    startDate: datetime
    deadline: datetime
    progress: int  # percentage complete
    budget: float
    budgetUsed: float
    milestones: List[Milestone] = []
    tasks: List[dict] = []  # List of task dictionary objects
    teamMembers: List[TeamMember] = []
    stakeholders: List[dict] = []  # e.g. {"name": "Stakeholder Name", ...}

class TaskCreate(BaseModel):
    name: str
    assignee: str
    deadline: datetime
    priority: str  # "low", "medium", "high"
    description: Optional[str] = None

class Task(TaskCreate):
    id: int
    status: str  # "not-started", "in-progress", "completed"

class ChatMessage(BaseModel):
    id: str
    content: str
    sender: str  # "user" or "ai"
    timestamp: datetime

class ChatRequest(BaseModel):
    message: str

class EmailTemplate(BaseModel):
    recipient: str  # "all" or a specific stakeholder name
    subject: str
    content: str
    includeTimeline: bool = True
    includeTaskSummary: bool = True

class TimelineData(BaseModel):
    milestones: List[Milestone]
    insights: Optional[List[dict]] = None  # e.g. [{"type": "warning", "message": "Delay risk detected."}]

class RiskReport(BaseModel):
    report: str
    risks: List[dict]  # Each risk: {"description": str, "impact": str, "probability": int, "mitigation": str, "contingency": str}
    completionProbability: int

###############################################################################
# MODELS FOR NEW PROJECT CREATION (used in NewProjectPage)
###############################################################################

class ProjectCreateRequest(BaseModel):
    name: str
    description: str
    startDate: datetime
    deadline: datetime
    budget: float
    budgetUsed: float = 0.0
    currentStage: str
    teamMembers: List[Dict[str, str]]
    stakeholders: List[Dict[str, str]]
    techStack: str
    buffer: Optional[str] = None

class ProjectCreated(ProjectCreateRequest):
    id: int
    createdAt: datetime

###############################################################################
# MODELS FOR AI ASSISTANT (ChatPage standalone)
###############################################################################

class AiAssistantResponse(BaseModel):
    name: str
    title: str
    experience: int
    avatar: str
    greeting: str

class ThemeResponse(BaseModel):
    primary: str
    light: str
    border: str
    hover: str

class ChatResponse(BaseModel):
    message: str

###############################################################################
# IN-MEMORY DATA STORES
###############################################################################

# Projects data store (simulate a database)
PROJECTS: Dict[int, Project] = {
    1: Project(
        id=1,
        name="ProxyForce Alpha",
        description="A project for creating dynamic AI teams.",
        startDate=datetime.now() - timedelta(days=30),
        deadline=datetime.now() + timedelta(days=60),
        progress=45,
        budget=100000,
        budgetUsed=45000,
        milestones=[
            Milestone(id=1, name="Design Complete", deadline=datetime.now() - timedelta(days=10), status="completed", progress=100),
            Milestone(id=2, name="Prototype", deadline=datetime.now() + timedelta(days=10), status="in-progress", progress=50),
            Milestone(id=3, name="Final Release", deadline=datetime.now() + timedelta(days=60), status="not-started", progress=0),
        ],
        tasks=[],
        teamMembers=[
            TeamMember(id=1, name="Alice Smith", role="Developer", avatar="https://randomuser.me/api/portraits/women/1.jpg", tasks=5, completed=3),
            TeamMember(id=2, name="Bob Johnson", role="Designer", avatar="https://randomuser.me/api/portraits/men/2.jpg", tasks=4, completed=4),
        ],
        stakeholders=[{"name": "CEO"}, {"name": "CTO"}],
    )
}
project_id_counter = 2  # Next available project id

# Sample chat messages per project id
PROJECT_CHATS: Dict[int, List[ChatMessage]] = {
    1: [
        ChatMessage(id="1", content="Welcome to the project chat!", sender="ai", timestamp=datetime.now() - timedelta(minutes=10)),
    ]
}

# Global task ID counter
TASK_ID_COUNTER = 1

###############################################################################
# STATIC DATA FOR NEW PROJECT PAGE (Role Themes, Tier Titles, Project Stages)
###############################################################################

role_themes_data = {
    "pm": {
        "title": "Project Manager",
        "color": "#3B82F6",
        "gradient": "from-blue-900 to-blue-700",
        "glow": "bg-blue-600",
    },
    "sales": {
        "title": "Sales Executive",
        "color": "#EF4444",
        "gradient": "from-red-900 to-red-700",
        "glow": "bg-red-600",
    },
    "marketing": {
        "title": "Marketing Analyst",
        "color": "#22C55E",
        "gradient": "from-green-900 to-green-700",
        "glow": "bg-green-600",
    },
}

tier_titles = {
    "1": "Apprentice",
    "2": "Adept",
    "3": "Master",
}

project_stages_data = [
    {"value": "initial", "label": "Initial Planning"},
    {"value": "development", "label": "Development"},
    {"value": "testing", "label": "Testing"},
    {"value": "deployment", "label": "Deployment"},
    {"value": "maintenance", "label": "Maintenance"},
]

###############################################################################
# DUMMY DATA FOR AI ASSISTANT AND THEME (For ChatPage)
###############################################################################

assistant_data: Dict[str, Dict[str, str or int]] = {
    "project-manager": {
        "name": "Ava",
        "title": "Project Manager",
        "experience": 8,
        "avatar": "https://randomuser.me/api/portraits/women/68.jpg",
        "greeting": "Hello, I'm Ava, your project manager AI. How can I assist you today?"
    },
    "sales": {
        "name": "Max",
        "title": "Sales Executive",
        "experience": 5,
        "avatar": "https://randomuser.me/api/portraits/men/75.jpg",
        "greeting": "Hi, I'm Max, your sales AI. What sales insights can I provide today?"
    },
    "marketing": {
        "name": "Lara",
        "title": "Marketing Analyst",
        "experience": 7,
        "avatar": "https://randomuser.me/api/portraits/women/42.jpg",
        "greeting": "Hey, I'm Lara, your marketing AI. Let's analyze some trends!"
    }
}

theme_data = {
    "project-manager": {
        "primary": "bg-blue-500",
        "light": "bg-blue-100",
        "border": "border border-blue-300",
        "hover": "hover:bg-blue-600",
        # Optionally include an avatar field if needed:
        "avatar": "https://randomuser.me/api/portraits/women/68.jpg",
        "name": "Ava"
    },
    "sales": {
        "primary": "bg-red-500",
        "light": "bg-red-100",
        "border": "border border-red-300",
        "hover": "hover:bg-red-600",
        "avatar": "https://randomuser.me/api/portraits/men/75.jpg",
        "name": "Max"
    },
    "marketing": {
        "primary": "bg-green-500",
        "light": "bg-green-100",
        "border": "border border-green-300",
        "hover": "hover:bg-green-600",
        "avatar": "https://randomuser.me/api/portraits/women/42.jpg",
        "name": "Lara"
    }
}

###############################################################################
# API ENDPOINTS
###############################################################################

# -------------------------
# Projects Endpoints
# -------------------------
@app.get("/api/projects/{project_id}", response_model=Project)
async def get_project(project_id: int):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# -------------------------
# Tasks Endpoints
# -------------------------
@app.post("/api/projects/{project_id}/tasks", response_model=Task)
async def create_task(project_id: int, task: TaskCreate):
    global TASK_ID_COUNTER
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    new_task = Task(
        id=TASK_ID_COUNTER,
        name=task.name,
        assignee=task.assignee,
        deadline=task.deadline,
        priority=task.priority,
        description=task.description,
        status="not-started",
    )
    TASK_ID_COUNTER += 1
    project.tasks.append(new_task.dict())
    return new_task

# -------------------------
# Chat Endpoints (Project Chat)
# -------------------------
@app.get("/api/projects/{project_id}/chat", response_model=List[ChatMessage])
async def get_chat_messages(project_id: int):
    messages = PROJECT_CHATS.get(project_id, [])
    return messages


# async def send_chat_message(project_id: int, chat: ChatRequest):
#     new_message = ChatMessage(
#         id=str(datetime.now().timestamp()),
#         content=chat.message,
#         sender="user",
#         timestamp=datetime.now(),
#     )
#     PROJECT_CHATS.setdefault(project_id, []).append(new_message)
    
#     ai_response = ChatMessage(
#         id=str(datetime.now().timestamp() + random.randint(1, 1000)),
#         content=f"AI Response: {chat.message[::-1]}",
#         sender="ai",
#         timestamp=datetime.now(),
#     )
#     PROJECT_CHATS[project_id].append(ai_response)
#     return ai_response
@app.post("/api/projects/{project_id}/chat", response_model=ChatMessage)
async def send_chat_message(project_id: int, chat: ChatRequest,role):
    # Load project details
    with open("projects.json", "r") as f:
        data = json.load(f)
    #project = data["projects"].get(req.projectId)
    project = data.get(chat.projectId)

    
    if not project:
        return {"response": "Project not found."}

    # Build dynamic system context
    system_prompt = f"""
You are acting as an expert {role} helping a team on this project:

Project Name: {project['project_name']}
Description: {project['description']}
Deadline: {project['deadline']}
Budget: ${project['budget']}

Team Members:
{chr(10).join([f"- {tm['name']} ({', '.join(tm.get('PFRoles', []))})" for tm in project.get('team_members', [])])}

Respond to the user’s prompt accordingly.
"""

    # Call OpenAI GPT
   # openai.api_key = "YOUR_API_KEY"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": req.prompt}
        ],
        temperature=0.7
    )

    reply = response.choices[0].message.content.strip()
    return {"response": reply}
# -------------------------
# Timeline Endpoints
# -------------------------
@app.get("/api/projects/{project_id}/timeline", response_model=TimelineData)
async def get_project_timeline(project_id: int):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    timeline_data = TimelineData(
        milestones=project.milestones,
        insights=[{"type": "info", "message": "Ensure all milestones are on schedule."}]
    )
    return timeline_data

@app.post("/api/projects/{project_id}/timeline/weekly-plan")
async def generate_weekly_plan(project_id: int):
    assignments = [
        {"member": tm.name, "role": tm.role, "tasks": [f"Task {i+1}" for i in range(random.randint(1, 3))]}
        for tm in PROJECTS.get(project_id).teamMembers
    ]
    return {"message": "Weekly plan generated.", "assignments": assignments}

# -------------------------
# Risk Endpoints
# -------------------------
@app.post("/api/projects/{project_id}/risk", response_model=RiskReport)
async def generate_risk_report(project_id: int):
    risks = [
        {
            "description": "Potential delay in design phase",
            "impact": "high",
            "probability": 70,
            "mitigation": "Increase design team hours",
            "contingency": "Outsource design review",
        },
        {
            "description": "Budget overrun risk",
            "impact": "medium",
            "probability": 40,
            "mitigation": "Regular cost reviews",
            "contingency": "Reallocate funds from marketing",
        },
    ]
    report_text = "Risk Analysis Report:\n" + "\n".join([f"{i+1}. {r['description']} ({r['impact']} Impact, {r['probability']}% probability)" for i, r in enumerate(risks)])
    completion_probability = random.randint(60, 90)
    return RiskReport(report=report_text, risks=risks, completionProbability=completion_probability)

# -------------------------
# Email Endpoints
# -------------------------
@app.post("/api/projects/{project_id}/email/generate", response_model=EmailTemplate)
async def generate_email_template(project_id: int, template: EmailTemplate):
    project = PROJECTS.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    content = f"Status Update for {project.name}:\n\nProgress: {project.progress}% complete.\nUpcoming Milestones:\n"
    for milestone in project.milestones:
        if milestone.status != "completed":
            content += f"- {milestone.name}: due {milestone.deadline.strftime('%b %d')}\n"
    if template.includeTaskSummary:
        content += "\nTask Summary:\n"
        for task in project.tasks:
            content += f"- {task.get('name')} (Status: {task.get('status')})\n"
    return EmailTemplate(
        recipient=template.recipient,
        subject=template.subject or f"{project.name} - Status Update",
        content=content,
        includeTimeline=template.includeTimeline,
        includeTaskSummary=template.includeTaskSummary
    )

@app.post("/api/projects/{project_id}/email/send")
async def send_email(project_id: int, template: EmailTemplate):
    print(f"Sending email for project {project_id}:")
    print(f"Recipient: {template.recipient}")
    print(f"Subject: {template.subject}")
    print(f"Content:\n{template.content}")
    return {"message": "Email sent successfully."}

# -------------------------
# Endpoints for AI Assistant (ChatPage) and Theme
# -------------------------
@app.get("/api/ai-assistant", response_model=AiAssistantResponse)
async def get_ai_assistant(
    role: str = Query("project-manager"),
    tier: str = Query("1")
):
    key = role.lower()
    assistant = assistant_data.get(key, assistant_data["project-manager"])
    return AiAssistantResponse(**assistant)

@app.get("/api/theme/{role}", response_model=ThemeResponse)
async def get_theme(role: str):
    key = role.lower()
    theme = theme_data.get(key)
    if not theme:
        theme = theme_data["project-manager"]
    return ThemeResponse(**theme)

###############################################################################
# RUN THE APPLICATION
###############################################################################

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
