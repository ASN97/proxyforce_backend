from fastapi import APIRouter, Body
from utils.openai_helper import call_openai  # Assuming this is your GPT wrapper
from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List, Dict
import matplotlib.pyplot as plt
import io,os,uuid
import base64
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from datetime import datetime, timedelta
from utils.file_storage import load_projects, save_projects
from uuid import uuid4
from models.project_models import ProjectCreateRequest


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

@router.post("/create")
async def create_project(project_data: ProjectCreateRequest):
    project_id = str(uuid4())

    # Load existing projects
    projects_db = load_projects()

    # Save new one
    projects_db[project_id] = project_data.dict()
    save_projects(projects_db)

    return {
        "message": "Project created and saved successfully!",
        "project_id": project_id,
        "data": projects_db[project_id]
    }


from fastapi import APIRouter, Body
from models.project_models import ProjectCreateRequest
from utils.openai_helper import call_openai  # your GPT helper
from datetime import datetime


@router.post("/create-timeline")
async def create_timeline(project_data: ProjectCreateRequest):
    startdate = datetime.strptime(project_data.start_date, "%Y-%m-%d").strftime("%B %d, %Y")
    deadline = datetime.strptime(project_data.deadline, "%Y-%m-%d").strftime("%B %d, %Y")
    
    prompt = f"""
    You're an experienced AI project manager.

    Based on the following project information, generate a structured project timeline with phases, durations, and 2-3 key milestones per phase.

    Project: {project_data.project_name}
    Description: {project_data.description}
    Team: {[f"{m.name} ({', '.join(m.skills)})" for m in project_data.team_members]}
    Stakeholders: {', '.join(project_data.stakeholders)}
    Budget: ${project_data.budget} (used: ${project_data.budget_used})
    StartDate: {startdate}
    Deadline: {deadline}
    Tech Stack: {', '.join(project_data.tech_stack)}
    Stage: {project_data.current_stage}

    Format output as:
    {{
      "timeline": [
        {{
          "phase": "Planning",
          "duration_days": 3,
          "milestones": ["Define scope", "Stakeholder approval"]
        }},
        ...
      ],
      "estimated_completion": "Month DD, YYYY"
    }}
    """
    return await call_openai(prompt)







#Generating the gantt chart image from timeline


@router.post("/generate-gantt-chart-image")
async def generate_gantt_chart_image(timeline_data: dict = Body(...)):
    timeline = timeline_data.get("timeline", [])
    start_date = datetime.today()

    fig, ax = plt.subplots(figsize=(10, 5))

    for i, phase in enumerate(timeline):
        phase_name = phase["phase"]
        duration = phase["duration_days"]
        
        # Calculate valid start date
        days_offset = sum(t["duration_days"] for t in timeline[:i])
        start = start_date + timedelta(days=days_offset)

        # Avoid invalid dates
        if start.toordinal() >= 1:
            ax.barh(phase_name, duration, left=start.toordinal(), height=0.4, align='center')
            for j, milestone in enumerate(phase["milestones"]):
                ax.text(start.toordinal() + j, i, f"• {milestone}", va='center', fontsize=8)

    ax.set_xlabel("Date")
    ax.set_ylabel("Project Phases")
    ax.set_title("Gantt Chart")

    # Safe date formatting
    def safe_formatter(x, _):
        try:
            return datetime.fromordinal(int(x)).strftime('%b %d')
        except ValueError:
            return ""

    ax.xaxis.set_major_formatter(plt.FuncFormatter(safe_formatter))
    plt.tight_layout()

    # Save file
    os.makedirs("static", exist_ok=True)
    filename = f"gantt_{uuid.uuid4().hex}.png"
    filepath = os.path.join("static", filename)

    plt.savefig(filepath)
    plt.close()

    return FileResponse(filepath, media_type="image/png", filename="project_gantt_chart.png")

from models.project_models import WeeklyTaskAssignmentRequest

@router.post("/assign-weekly-tasks")
async def assign_weekly_tasks(data: WeeklyTaskAssignmentRequest):
    project = data.project_data
    timeline = data.timeline

    prompt = f"""
    You are an experienced AI project manager.

    Based on the following project data and timeline, break down the upcoming week's work into 6–8 detailed tasks.

    Each task should be:
    - Mapped to one of the current milestones
    - Assigned to a team member based on their skills and weekly working hours
    - Clearly estimated in terms of hours
    - Prioritized according to the phase duration

    Project Info:
    Name: {project.project_name}
    Description: {project.description}
    Team: {[f"{m.name} ({', '.join(m.skills)})" for m in project.team_members]}
    Deadline: {project.deadline}
    Tech Stack: {', '.join(project.tech_stack)}
    Stage: {project.current_stage}
    Budget: ${project.budget} (Used: ${project.budget_used})

    Timeline:
    {[
        f"{t.phase} ({t.duration_days} days): " + ", ".join(t.milestones)
        for t in timeline
    ]}

    Format:
    {{
      "weekly_tasks": [
        {{
          "task": "Design login UI",
          "assigned_to": "Aromal Nair",
          "skills_required": ["UI/UX", "React"],
          "estimated_hours": 6,
          "due_date": "April 19, 2025",
          "status": "Not Started",
          "phase": "Development"
        }},
        ...
      ],
      "notes": "Balanced workload across available members"
    }}
    """

    return await call_openai(prompt)


@router.post("/generate-email-summary")
async def generate_email_summary(payload: dict = Body(...)):
    project_id = payload.get("project_id")

    if not project_id:
        raise HTTPException(status_code=400, detail="Missing project_id")

    projects_db = load_projects()
    project = projects_db.get(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    team_emails = [member["email"] for member in project["team_members"]]
    team_intro = "\n".join([
        f"- {member['name']} ({', '.join(member['skills'])})"
        for member in project["team_members"]
    ])

    prompt = f"""
    You're an AI project manager writing a weekly update email to the team.

    Project: {project['project_name']}
    Description: {project['description']}
    Deadline: {project['deadline']}
    Current stage: {project['current_stage']}
    Budget used: ${project['budget_used']} / ${project['budget']}

    Team:
    {team_intro}

    Write a professional but friendly email with:
    - A quick project status update
    - Appreciation for work so far
    - Key focus areas for the next week
    - A call-to-action for replying with blockers

    End with a positive closing and include recipients:
    {', '.join(team_emails)}
    """

    return await call_openai(prompt)