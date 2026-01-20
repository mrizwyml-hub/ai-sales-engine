import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from openai import OpenAI

# -------------------- APP --------------------
app = FastAPI(title="AI Travel WhatsApp Bot")

# OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# WhatsApp webhook verify token (must match Meta UI)
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

# -------------------- MEMORY STORE --------------------
conversation_memory = {}

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

Return ONLY valid JSON:
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

def generate_ai_reply(context: dict) -> str:
    prompt = f"""
You are a professional travel agent.

Conversation context:
{json.dumps(context, indent=2)}

Reply politely and ask for missing information if needed.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text.strip()

# -------------------- ROUTES --------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "WhatsApp AI running"}

# ✅ Meta webhook verification (GET)
@app.get("/webhook/whatsapp")
async def verify_whatsapp_webhook(request: Request):
    params = dict(request.query_params)

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    # Meta expects plain text challenge back
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")

# ✅ Meta webhook events (POST)
@app.post("/webhook/whatsapp")
async def receive_whatsapp_webhook(request: Request):
    payload = await request.json()

    # For now, return OK so Meta sees 200
    # (Later we parse message payload & reply)
    return {"status": "received", "payload": payload}

# Your testing endpoint (kept)
@app.post("/webhook/test")
def webhook_test(data: WebhookRequest):
    if data.contact not in conversation_memory:
        conversation_memory[data.contact] = {
            "intent": "travel",
            "destination": None,
            "travel_date": None,
            "passengers": None
        }

    memory = conversation_memory[data.contact]

    if not is_low_information(data.text):
        ai_data = extract_travel_details(data.text)
        for key in ["destination", "travel_date", "passengers"]:
            if ai_data.get(key):
                memory[key] = ai_data[key]

    ai_reply = generate_ai_reply(memory)
    completed = all(memory.values())

    return {
        "status": "ok",
        "contact": data.contact,
        "memory": memory,
        "stage": "Quote Ready" if completed else "Collecting Details",
        "ai_reply": ai_reply
    }

@app.post("/webhook/reset/{contact}")
def reset_lead(contact: str):
    conversation_memory.pop(contact, None)
    return {"status": "reset", "contact": contact, "message": "Conversation memory cleared"}
