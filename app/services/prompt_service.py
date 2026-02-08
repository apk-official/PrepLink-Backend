import json

from fastapi import HTTPException,status

from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig
from app.core.config import settings
from app.schema.prep_schema import InterviewPrepResponse
from app.utils.prompts import TOS_SYSTEM_PROMPT, INTERVIEW_PREP_PROMPT

client = genai.Client(api_key=settings.GOOGLE_GEMINI_API_KEY)
class PromptService:
    @staticmethod
    def tos_prompt(tos_data:dict):
        if not tos_data.get("pages"):
            return True
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=tos_data,
            config=GenerateContentConfig(
                system_instruction=TOS_SYSTEM_PROMPT,
                temperature=0.0,
                response_mime_type="text/x.enum",
                response_schema={
                    "type":"string",
                    "enum":["True","False"]
                }
            )
        )
        verdict = response.text.strip() =="True"

        return verdict

    @staticmethod
    def create_prep_prompt(prep_data:dict)->InterviewPrepResponse:
        if not prep_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="No data input to generate Interview Prep")
        payload_text = json.dumps(prep_data, ensure_ascii=False)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=payload_text,
            config=GenerateContentConfig(
                thinking_config=types.ThinkingConfig(include_thoughts=False),
                system_instruction=INTERVIEW_PREP_PROMPT,
                temperature=0.2,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=InterviewPrepResponse
            )
        )

        return response.parsed