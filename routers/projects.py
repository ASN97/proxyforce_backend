from fastapi import APIRouter, Body
from models.project_models import ProjectCreateRequest
from uuid import uuid4
from utils.file_storage import load_projects, save_projects

router = APIRouter(prefix="/projects", tags=["Projects"])

# Load existing projects from file
#projects_db = load_projects()

@router.post("/create")
async def create_project(project_data: ProjectCreateRequest):
    project_id = str(uuid4())
    projects_db[project_id] = project_data.dict()
    save_projects(projects_db)  # Save to file
    return {
        "message": "Project created successfully!",
        "project_id": project_id,
        "data": projects_db[project_id]
    }

@router.get("/all")
async def get_all_projects():
    projects_db = load_projects()
    return {
        "projects": projects_db
    }

@router.get("/{project_id}")
async def get_project_by_id(project_id: str):
    projects_db = load_projects()
    project = projects_db.get(project_id)
    if not project:
        return {"error": "Project not found"}
    return {
        "project_id": project_id,
        "data": project
    }
