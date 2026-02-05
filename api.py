from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
import json
import traceback

try:
    from project import chain
except ImportError:
    print("CRITICAL ERROR: project.py missing!")
    chain = None

app = FastAPI()

# Railway Variables
WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"

def send_wassenger_message(phone, text):
    print(f"--- ATTEMPTING TO SEND MESSAGE ---")
    print(f"Target Phone: {phone}")
    
    # Safety check for token
    if not WASSENGER_TOKEN:
        print("ERROR: WASSENGER_TOKEN is missing in Railway Variables!")
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
        print(f"WASSENGER RESPONSE CODE: {r.status_code}")
        print(f"WASSENGER RESPONSE BODY: {r.text}")
    except Exception as e:
        print(f"NETWORK ERROR DURING SEND: {e}")

def process_whatsapp_ai(phone, query):
    try:
        print(f"DEBUG: Starting AI process for {phone}")
        # AI bypass test for Greetings
        clean_query = str(query).lower().strip()
        if any(word == clean_query for word in ['hi', 'hello', 'salam', 'aoa']):
            reply = "Hello! I am your SU Assistant. Server is working!"
        else:
            if chain:
                print("DEBUG: Calling RAG Chain...")
                reply = chain.invoke(query)
            else:
                reply = "AI Chain not loaded."
        
        send_wassenger_message(phone, reply)
    except Exception as e:
        print(f"AI PROCESSING ERROR: {e}")

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body_bytes = await request.body()
        data = json.loads(body_bytes.decode("utf-8"))

        # Recursive decode if string
        if isinstance(data, str):
            data = json.loads(data)

        if not isinstance(data, dict):
            return {"status": "not_a_dict"}

        event_type = data.get('event')
        if event_type == 'message:in:new':
            inner = data.get('data', {})
            phone = inner.get('phone')
            user_query = inner.get('body', {}).get('text')

            if phone and user_query:
                print(f"DEBUG: New Message from {phone}: {user_query}")
                # Use background task
                background_tasks.add_task(process_whatsapp_ai, phone, user_query)
                return {"status": "ok"}
        
        return {"status": "ignored"}
    except Exception as e:
        print(f"WEBHOOK ERROR: {e}")
        return {"status": "error"}

@app.get("/")
def home():
    return {"status": "running", "token_set": bool(WASSENGER_TOKEN)}