from sqlalchemy import Column, Integer, String
from app.database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    contact = Column(String, unique=True, index=True)
    channel = Column(String)

    intent = Column(String, nullable=True)
    stage = Column(String, nullable=True)

    destination = Column(String, nullable=True)
    travel_date = Column(String, nullable=True)
    passengers = Column(String, nullable=True)
