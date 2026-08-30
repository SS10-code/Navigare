import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from resend import Resend

router = APIRouter()

class FeedbackRequest(BaseModel):
    email: EmailStr
    message: str

@router.post("/feedback")
async def post_feedback(data: FeedbackRequest):
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        # Fallback to logging if Resend is not configured
        print(f"FEEDBACK from {data.email}: {data.message}")
        return {"status": "logged", "message": "Feedback received (Resend not configured)"}

    try:
        resend = Resend(api_key)
        resend.emails.send({
            "from": "Navigare Feedback <onboarding@resend.dev>",
            "to": "sahej4202@gmail.com",
            "subject": f"New Feedback from {data.email}",
            "text": data.message
        })
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
