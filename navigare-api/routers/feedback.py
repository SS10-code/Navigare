import os
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
import resend as resend_module

router = APIRouter()

class FeedbackRequest(BaseModel):
    email: str
    message: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email address")
        return v

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) < 5:
            raise ValueError("Message must be at least 5 characters")
        return v

@router.post("/feedback")
async def post_feedback(data: FeedbackRequest):
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print(f"[FEEDBACK] From: {data.email} | Message: {data.message}")
        return {"status": "logged", "message": "Feedback received (Resend not configured)"}

    try:
        resend_module.api_key = api_key
        resend_module.Emails.send({
            "from": "Navigare Feedback <onboarding@resend.dev>",
            "to": "sahej4202@gmail.com",
            "subject": f"New Feedback from {data.email}",
            "text": f"From: {data.email}\n\n{data.message}",
            "reply_to": data.email,
        })
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
