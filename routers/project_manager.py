from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.openai_helper import generate_response

router = APIRouter()

class Prompt(BaseModel):
    prompt: str

ROLE_PROMPT = """You are an expert AI Project Manager.
You break down goals into tasks, create timelines, give status updates, and identify risks."""

@router.post("/project-manager")
def project_manager_response(data: Prompt):
    try:
        output = generate_response(ROLE_PROMPT, data.prompt)
        return {"response": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
