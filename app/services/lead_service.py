from sqlalchemy.orm import Session
from app.models.lead import Lead

def get_or_create_lead(db: Session, contact: str, channel: str):
    lead = db.query(Lead).filter(Lead.contact == contact).first()
    if lead:
        return lead

    lead = Lead(
        contact=contact,
        channel=channel,
        stage="New Lead"
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead
