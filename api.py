from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
import json
import traceback

# Project.py se chain import karna
try:
    from project import chain
except ImportError:
    print("CRITICAL: project.py not found!")
    chain = None

app = FastAPI()

# Railway Variables
WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"

def send_wassenger_message(phone, text):
    """Messages bhejne ka function."""
    if not WASSENGER_TOKEN:
        print("ERROR: WASSENGER_TOKEN missing!")
        return
    
    # Phone number se '+' aur extra spaces khatam karna
    clean_phone = str(phone).replace("+", "").strip()
    
    payload = {
        "phone": clean_phone,
        "message": str(text)
    }
    headers = {
        "Content-Type": "application/json",
        "Token": WASSENGER_TOKEN.strip()
    }

    try:
        r = requests.post(WASSENGER_URL, json=payload, headers=headers)
        print(f"WASSENGER_API_STATUS: {r.status_code}")
        print(f"WASSENGER_API_RESPONSE: {r.text}")
    except Exception as e:
        print(f"NETWORK ERROR: {e}")

def process_ai_logic(phone, user_query):
    """Background mein AI process karne ke liye."""
    try:
        # Simple Greeting Check
        query_lower = user_query.lower().strip()
        if any(greet == query_lower for greet in ['hi', 'hello', 'salam', 'aoa']):
            reply = "Hello! I am your SU Assistant. How can I help you today?"
        elif chain:
            print(f"DEBUG: Calling AI for: {user_query}")
            reply = chain.invoke(user_query)
        else:
            reply = "AI system is currently initializing. Please try again in a moment."
        
        send_wassenger_message(phone, reply)
    except Exception as e:
        print(f"AI_LOGIC_ERROR: {e}")

@app.get("/")
def home():
    return {"status": "online"}

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        # 1. Raw Payload Capture
        raw_body = await request.body()
        body_str = raw_body.decode("utf-8")
        data = json.loads(body_str)

        # Double check if it's a string
        if isinstance(data, str):
            data = json.loads(data)

        # 2. Key Extraction based on your logs
        event = data.get("event")
        print(f"EVENT_TYPE: {event}")

        if event == "message:in:new":
            message_data = data.get("data", {})
            
            # Aapke payload ke mutabiq sahi paths:
            phone = message_data.get("fromNumber") # e.g. +923408346162
            user_query = message_data.get("body")   # e.g. Halahal
            
            print(f"FROM: {phone} | MESSAGE: {user_query}")

            if phone and user_query:
                # 3. Background mein AI ko bhejein taake server fast respond kare
                background_tasks.add_task(process_ai_logic, phone, user_query)
                return {"status": "processing"}

        return {"status": "ignored"}

    except Exception as e:
        print(f"WEBHOOK_CRASH: {traceback.format_exc()}")
        return {"status": "error"}