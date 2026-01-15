import os
import json
import requests
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# -------------------- APP --------------------
app = FastAPI(title="AI Travel WhatsApp Bot")

# -------------------- ENV --------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------- MEMORY --------------------
conversation_memory = {}

# -------------------- HELPERS --------------------
def is_low_information(text: str) -> bool:
    return len(text.strip()) < 5 or text.strip().isdigit()

def extract_travel_details(message: str) -> dict:
    prompt = f"""
Extract travel details from the message.

Message:
"{message}"

Return JSON only:
{{
  "destination": "",
  "travel_date": "",
  "passengers": ""
}}
"""
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )
    return json.loads(response.output_text)

def generate_ai_reply(memory: dict) -> str:
    prompt = f"""
You are a professional travel agent.

Conversation memory:
{json.dumps(memory, indent=2)}

Reply politely and ask for missing info.
"""
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )
    return response.output_text.strip()

def send_whatsapp_message(to: str, message: str):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    r = requests.post(url, headers=headers, json=payload)
    if r.status_code != 200:
        print("WhatsApp send error:", r.text)

# -------------------- ROUTES --------------------

@app.get("/")
def root():
    return {"status": "ok", "message": "WhatsApp AI running"}

# 🔐 Webhook verification
@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return int(params.get("hub.challenge"))

    raise HTTPException(status_code=403, detail="Verification failed")

# 📩 Incoming WhatsApp messages
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    payload = await request.json()

    try:
        message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
        contact = message["from"]
        text = message["text"]["body"]
    except Exception:
        return {"status": "ignored"}

    # Init memory
    if contact not in conversation_memory:
        conversation_memory[contact] = {
            "destination": None,
            "travel_date": None,
            "passengers": None
        }

    memory = conversation_memory[contact]

    if not is_low_information(text):
        extracted = extract_travel_details(text)
        for k in memory:
            if extracted.get(k):
                memory[k] = extracted[k]

    reply = generate_ai_reply(memory)

    # 🔥 SEND MESSAGE BACK TO WHATSAPP
    send_whatsapp_message(contact, reply)

    return {"status": "sent"}
