import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

app = FastAPI()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

@app.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    params = dict(request.query_params)

    # DEBUG: print everything Meta sends
    print("VERIFY QUERY PARAMS:", params)

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        # DEBUG: print the values
        print("VERIFIED! Returning challenge:", challenge)
        return PlainTextResponse(challenge)

    # DEBUG: print failure info
    print("Verification failed:", {"mode": mode, "token": token, "expected": VERIFY_TOKEN})

    raise HTTPException(status_code=403, detail="Verification failed")
