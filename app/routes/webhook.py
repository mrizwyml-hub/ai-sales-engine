from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.message import Message
from app.models.lead import Lead
from app.services.lead_service import get_or_create_lead
from app.services.ai_service import detect_intent, generate_ai_reply

router = APIRouter()

class WebhookRequest(BaseModel):
    contact: str
    text: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/webhook/test")
def test_webhook(payload: WebhookRequest, db: Session = Depends(get_db)):
    lead = get_or_create_lead(db, payload.contact, "whatsapp")

    # Save customer message
    db.add(Message(
        lead_id=lead.id,
        sender="customer",
        text=payload.text,
        channel="whatsapp"
    ))
    db.commit()

    # FIRST message → detect intent only
    if lead.intent is None:
        lead.intent = detect_intent(payload.text)
        lead.stage = "Qualified"
        db.commit()

    # FOLLOW-UP messages → save answers
    else:
        if lead.intent == "travel":
            if lead.destination is None:
                lead.destination = payload.text
                db.commit()
            elif lead.travel_date is None:
                lead.travel_date = payload.text
                db.commit()
            elif lead.passengers is None:
                lead.passengers = payload.text
                lead.stage = "Quote Ready"
                db.commit()

    ai_text = generate_ai_reply(lead)

    # Save AI message
    db.add(Message(
        lead_id=lead.id,
        sender="ai",
        text=ai_text,
        channel="whatsapp"
    ))
    db.commit()

    return {
        "status": "ok",
        "lead_id": lead.id,
        "intent": lead.intent,
        "destination": lead.destination,
        "travel_date": lead.travel_date,
        "passengers": lead.passengers,
        "stage": lead.stage,
        "ai_reply": ai_text
    }


# 🔁 RESET ENDPOINT (FOR TESTING)
@router.post("/webhook/reset/{contact}")
def reset_lead(contact: str, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.contact == contact).first()
    if not lead:
        return {"status": "not found"}

    lead.intent = None
    lead.stage = "New Lead"
    lead.destination = None
    lead.travel_date = None
    lead.passengers = None
    db.commit()

    return {"status": "reset successful"}
