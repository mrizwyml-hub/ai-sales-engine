import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# -------------------- APP INIT --------------------
app = FastAPI(title="AI Travel Webhook")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------- MODELS --------------------
class WebhookRequest(BaseModel):
    contact: str
    text: str

# -------------------- HELPERS --------------------
def is_low_information(text: str) -> bool:
    text = text.strip()
    return len(text) < 5 or text.isdigit()

def extract_travel_details(message: str) -> dict:
    prompt = f"""
Extract travel details from the message below.

Message:
"{message}"

Return ONLY valid JSON in this format:
{{
  "intent": "travel",
  "destination": "",
  "travel_date": "",
  "passengers": ""
}}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    try:
        return json.loads(response.output_text)
    except Exception:
        raise HTTPException(status_code=500, detail="AI parsing failed")

def generate_ai_reply(destination: str, passengers: str) -> str:
    prompt = f"""
You are a professional travel agent.

Customer wants to travel to {destination}
Passengers: {passengers}

Write a short, polite reply.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text.strip()

# -------------------- ROUTES --------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "AI Travel Webhook is running"}

@app.post("/webhook/test")
def webhook_test(data: WebhookRequest):

    # 🚫 STOP AI GUESSING
    if is_low_information(data.text):
        return {
            "status": "need_more_info",
            "stage": "Awaiting Details",
            "message": "Could you please tell me your destination and travel date?"
        }

    # ✅ AI extraction
    ai_data = extract_travel_details(data.text)

    # ✅ AI reply
    ai_reply = generate_ai_reply(
        ai_data.get("destination", "your destination"),
        ai_data.get("passengers", "your group")
    )

    return {
        "status": "ok",
        "lead_id": hash(data.contact) % 100000,
        "intent": ai_data.get("intent"),
        "destination": ai_data.get("destination"),
        "travel_date": ai_data.get("travel_date"),
        "passengers": ai_data.get("passengers"),
        "stage": "Quote Ready",
        "ai_reply": ai_reply
    }

@app.post("/webhook/reset/{contact}")
def reset_lead(contact: str):
    return {
        "status": "reset",
        "contact": contact,
        "message": "Lead reset successfully"
    }
