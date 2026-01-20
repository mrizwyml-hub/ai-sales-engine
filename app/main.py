import os
import json
from fastapi import FastAPI, Request, HTTPException
from openai import OpenAI

# -------------------- CONFIG --------------------
VERIFY_TOKEN = "my_verify_token_123"  # MUST match Meta dashboard

# -------------------- APP --------------------
app = FastAPI(title="AI Travel WhatsApp Bot")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------- ROOT --------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "WhatsApp AI running"}

# -------------------- WEBHOOK VERIFICATION (GET) --------------------
@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)  # ⚠️ MUST return challenge ONLY

    raise HTTPException(status_code=403, detail="Verification failed")

# -------------------- WEBHOOK RECEIVER (POST) --------------------
@app.post("/webhook/whatsapp")
async def receive_whatsapp_message(request: Request):
    payload = await request.json()

    # For now just log & acknowledge
    print(json.dumps(payload, indent=2))

    return {"status": "received"}
