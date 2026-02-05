from fastapi import FastAPI, Request
import requests
import os
import json

try:
    from project import chain
except ImportError:
    chain = None

app = FastAPI()

# Railway Variables - Double check these names in Railway!
WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"

def send_wassenger_message(phone, text):
    print(f"--- ATTEMPTING TO SEND ---")
    if not WASSENGER_TOKEN:
        print("CRITICAL: WASSENGER_TOKEN is NULL in Railway Variables!")
        return
    
    payload = {
        "phone": str(phone).replace("+", "").strip(),
        "message": str(text)
    }
    headers = {
        "Content-Type": "application/json",
        "Token": WASSENGER_TOKEN.strip()
    }

    try:
        r = requests.post(WASSENGER_URL, json=payload, headers=headers)
        print(f"WASSENGER STATUS: {r.status_code}")
        print(f"WASSENGER RESPONSE: {r.text}")
    except Exception as e:
        print(f"NETWORK ERROR: {e}")

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        raw_body = await request.body()
        data = json.loads(raw_body.decode("utf-8"))
        
        # Double decode if needed
        if isinstance(data, str):
            data = json.loads(data)

        if data.get('event') == 'message:in:new':
            inner = data.get('data', {})
            phone = inner.get('phone')
            # Safely get text
            body = inner.get('body', {})
            user_query = body.get('text') if isinstance(body, dict) else None

            if phone and user_query:
                print(f"DEBUG: Message from {phone}: {user_query}")
                
                # AI Reply Logic
                if any(word in user_query.lower() for word in ['hi', 'hello', 'salam']):
                    reply = "Hello! Server is online. Testing response."
                elif chain:
                    reply = chain.invoke(user_query)
                else:
                    reply = "AI Chain not loaded but server is alive."
                
                # DIRECT SEND (No background task for testing)
                send_wassenger_message(phone, reply)
                
            return {"status": "ok"}
        
        return {"status": "ignored"}
    except Exception as e:
        print(f"WEBHOOK ERROR: {e}")
        return {"status": "error"}

@app.get("/")
def home():
    return {"status": "running", "token_exists": bool(WASSENGER_TOKEN)}