import openai
import os
from dotenv import load_dotenv

load_dotenv()  # loads your .env with OPENAI_API_KEY

openai.api_key = os.getenv("OPENAI_API_KEY")

async def call_openai(prompt: str, model="gpt-4", max_tokens=500):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful project manager assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return {"response": response["choices"][0]["message"]["content"]}
    except Exception as e:
        return {"error": str(e)}
