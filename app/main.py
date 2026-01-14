from fastapi import FastAPI
from app.database import engine, Base
from app.routes.webhook import router as webhook_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(webhook_router)

@app.get("/")
def root():
    return {"status": "AI Sales Assistant running"}
