from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.openai_helper import call_openai
router = APIRouter()

class Prompt(BaseModel):
    prompt: str

ROLE_PROMPT = """You are a creative and strategic AI Marketing Executive.
You can create social media posts, ad campaigns, email content, SEO keywords, and content ideas."""

@router.post("/marketing-executive")
def marketing_response(data: Prompt):
    try:
        output = generate_response(ROLE_PROMPT, data.prompt)
        return {"response": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
