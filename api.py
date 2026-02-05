from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
import json
import traceback

try:
    from project import chain
except ImportError:
    print("CRITICAL: project.py missing!")
    chain = None

app = FastAPI()

WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"

def send_wassenger_message(phone, text):
    print(f"--- SENDING TO WASSENGER ---")
    if not WASSENGER_TOKEN:
        print("ERROR: Token missing in Railway!")
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

def process_whatsapp_ai(phone, query):
    try:
        print(f"DEBUG: Processing query for {phone}")
        clean_query = str(query).lower().strip()
        
        # Greeting Check
        if any(word == clean_query for word in ['hi', 'hello', 'salam', 'aoa']):
            reply = "Hello! I am your SU Assistant. Server is live and working!"
        else:
            if chain:
                reply = chain.invoke(query)
            else:
                reply = "AI System is currently offline."
        
        send_wassenger_message(phone, reply)
    except Exception as e:
        print(f"AI ERROR: {e}")

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        # 1. Raw body uthayein
        raw_body = await request.body()
        body_str = raw_body.decode("utf-8")
        
        if not body_str:
            return {"status": "empty"}

        # 2. Recursive Decoding (Jab tak dict na ban jaye)
        data = body_str
        for i in range(3):
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    break
        
        # 3. Final Type Check
        if not isinstance(data, dict):
            print(f"FAILED: Data is {type(data)} after decoding. Value: {data}")
            return {"status": "error_not_json"}

        # 4. Safely get event
        event_type = data.get('event')
        print(f"DEBUG: Event: {event_type}")

        if event_type == 'message:in:new':
            inner = data.get('data', {})
            phone = inner.get('phone')
            body = inner.get('body', {})
            user_query = body.get('text') if isinstance(body, dict) else None

            if phone and user_query:
                print(f"SUCCESS: Message from {phone}")
                background_tasks.add_task(process_whatsapp_ai, phone, user_query)
                return {"status": "ok"}
            elif phone:
                # Agar sirf picture/media hai
                background_tasks.add_task(send_wassenger_message, phone, "I only understand text messages.")
        
        return {"status": "ignored"}

    except Exception as e:
        print(f"WEBHOOK CRASH: {e}")
        return {"status": "error"}

@app.get("/")
def home():
    return {"status": "running"}