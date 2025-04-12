from fastapi import APIRouter, Body
from utils.openai_helper import call_openai  # Assuming this is your GPT wrapper
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter(prefix="/project_manager", tags=["Project Manager"])



# --- Step 1: Input Schema ---
class TeamMember(BaseModel):
    name: str
    skills: List[str]
    working_hours_per_week: int

class ProjectInitRequest(BaseModel):
    project_name: str
    description: str
    team_members: List[TeamMember]
    stakeholders: List[str]
    budget: float
    deadline: str  # format: YYYY-MM-DD
    tech_stack: List[str]

# --- Step 2: Project Initialization Endpoint ---
@router.post("/initialize")
async def initialize_project(data: ProjectInitRequest):
    # Store or process project info here
    return {
        "message": "Project initialized successfully!",
        "project_summary": data.dict(),
        "available_features": [
            "Timeline Generator",
            "Gantt Chart Generator",
            "Smart Task Assignment",
            "Email + Calendar Integration",
            "Change History Log",
            "Task Update Interface"
        ]
    }


@router.post("/generate-timeline")
async def generate_timeline(project_data: ProjectInitRequest):
    deadline = datetime.strptime(project_data.deadline, "%Y-%m-%d").strftime("%B %d, %Y")
    
    prompt = f"""
    You're an expert project planner.

    Based on the following project information, create a project timeline with phases, estimated durations, and key milestones.

    - Project Name: {project_data.project_name}
    - Description: {project_data.description}
    - Team Members: {[member.name + ' (' + ', '.join(member.skills) + ')' for member in project_data.team_members]}
    - Deadline: {deadline}
    - Budget: ${project_data.budget}
    - Tech Stack: {', '.join(project_data.tech_stack)}

    Output in this format:
    {{
        "timeline": [
            {{
                "phase": "Planning",
                "duration_days": 3,
                "milestones": ["Define goals", "Select tools"]
            }},
            {{
                "phase": "Development",
                "duration_days": 10,
                "milestones": ["Set up frontend", "Build backend API"]
            }}
        ],
        "estimated_completion": "April 28, 2025"
    }}
    """
    return await call_openai(prompt)















# 1. Auto Task Breakdown
@router.post("/task-breakdown")
async def task_breakdown(project_goal: str = Body(..., embed=True)):
    prompt = f"""
    Break down this project into phases and tasks:
    "{project_goal}"

    Format:
    {{
        "projectTitle": "...",
        "phases": [
            {{
                "phase": "...",
                "tasks": ["...", "..."],
                "duration": "..."
            }}
        ]
    }}
    """
    return await call_openai(prompt)

# 2. Real-Time Status Summary
@router.post("/status-update")
async def status_update(updates: list = Body(...)):
    prompt = f"""
    Based on these updates from team members, give a status summary:
    {updates}

    Include:
    - Tasks completed / pending
    - Delays if any
    - Project health
    - ETA for completion
    """
    return await call_openai(prompt)

# 3. Risk Radar + Suggestions
@router.post("/risk-analysis")
async def risk_analysis(plan_data: dict = Body(...)):
    prompt = f"""
    Analyze this project plan for possible risks:
    {plan_data}

    Return:
    {{
        "detectedRisk": "...",
        "recommendation": "...",
        "riskLevel": "Low/Medium/High"
    }}
    """
    return await call_openai(prompt)
