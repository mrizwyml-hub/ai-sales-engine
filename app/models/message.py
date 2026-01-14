from sqlalchemy import Column, Integer, String, ForeignKey
from app.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    sender = Column(String)
    text = Column(String)
    channel = Column(String)
