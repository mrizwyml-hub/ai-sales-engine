from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

app = FastAPI()

VERIFY_TOKEN = "my_verify_token_123"  # MUST match Meta exactly

@app.get("/")
def root():
    return {"status": "ok", "message": "WhatsApp AI running"}

# ✅ WEBHOOK VERIFICATION (GET)
@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")

# ✅ MESSAGE RECEIVER (POST)
@app.post("/webhook/whatsapp")
async def receive_message(payload: dict):
    print(payload)
    return {"status": "received"}
