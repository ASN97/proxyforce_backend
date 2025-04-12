from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.openai_helper import generate_response

router = APIRouter()

class Prompt(BaseModel):
    prompt: str

ROLE_PROMPT = """You are a top-tier AI Sales Executive.
You help generate leads, write cold outreach emails, and suggest sales strategies for new products or services."""

@router.post("/sales-executive")
def sales_response(data: Prompt):
    try:
        output = generate_response(ROLE_PROMPT, data.prompt)
        return {"response": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
