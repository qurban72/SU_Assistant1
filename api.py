from fastapi import FastAPI, Request
import requests
import os
import json

app = FastAPI()

# Railway Variables
WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"

@app.get("/")
def home():
    return {"status": "online", "token_exists": bool(WASSENGER_TOKEN)}

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    # 1. Print Raw Data (Sub se pehle dekhen data aa kya raha hai)
    raw_body = await request.body()
    body_str = raw_body.decode("utf-8")
    print(f"RAW_PAYLOAD_RECEIVED: {body_str}")

    if not body_str:
        print("EMPTY BODY RECEIVED")
        return {"status": "empty"}

    try:
        # 2. Parse JSON
        data = json.loads(body_str)
        
        # Wassenger event check
        event = data.get("event")
        print(f"EVENT_TYPE: {event}")

        if event == "message:in:new":
            msg_data = data.get("data", {})
            phone = msg_data.get("phone")
            message_text = msg_data.get("body", {}).get("text")
            
            print(f"FROM: {phone} | MESSAGE: {message_text}")

            if phone and message_text:
                # 3. Quick Response Test (Bina AI ke check karen message jata hai?)
                reply = f"I received your message: {message_text}"
                
                print(f"ATTEMPTING_SEND_TO: {phone}")
                
                headers = {
                    "Token": WASSENGER_TOKEN.strip(),
                    "Content-Type": "application/json"
                }
                payload = {
                    "phone": phone,
                    "message": reply
                }
                
                response = requests.post(WASSENGER_URL, json=payload, headers=headers)
                print(f"WASSENGER_API_STATUS: {response.status_code}")
                print(f"WASSENGER_API_RESPONSE: {response.text}")

        return {"status": "success"}

    except Exception as e:
        print(f"MAJOR_ERROR: {str(e)}")
        return {"status": "error", "detail": str(e)}