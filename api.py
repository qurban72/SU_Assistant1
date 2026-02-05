from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
import json
import traceback

# Project.py se chain import karna
try:
    from project import chain
except ImportError:
    print("CRITICAL ERROR: project.py not found or chain not defined!")

app = FastAPI()

# Railway Variables
WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"
SECRET_TOKEN = "SU_SECRET_2026"

# --- Helper Functions ---

def send_wassenger_message(phone, text):
    """Safe function to send messages back to WhatsApp."""
    if not phone or not text:
        return
    payload = {"phone": phone, "message": str(text)}
    headers = {"Content-Type": "application/json", "Token": WASSENGER_TOKEN}
    try:
        r = requests.post(WASSENGER_URL, json=payload, headers=headers)
        print(f"DEBUG: Sent to {phone}, Status Code: {r.status_code}")
    except Exception as e:
        print(f"ERROR: Failed to send message: {e}")

def process_whatsapp_ai(phone, query):
    """Background task to handle AI logic."""
    try:
        # Simple Greeting Check
        clean_query = str(query).lower().strip()
        if any(word == clean_query for word in ['hi', 'hello', 'salam', 'aoa', 'hey']):
            reply = "Hello! I am your SU Assistant. How can I help you with University of Sindh matters today?"
        else:
            print(f"DEBUG: Invoking AI for query: {query[:30]}...")
            reply = chain.invoke(query)
        
        send_wassenger_message(phone, reply)
    except Exception as e:
        print(f"AI ERROR: {e}")
        send_wassenger_message(phone, "I'm sorry, I'm having trouble processing your request right now.")

# --- API Endpoints ---

@app.get("/")
def home():
    return {"status": "online", "message": "SU Assistant Server is Running"}

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        # 1. Raw Body Capture
        body_bytes = await request.body()
        if not body_bytes:
            return {"status": "empty_body"}
        
        body_str = body_bytes.decode("utf-8")
        
        # 2. Hardcore Recursive JSON Parsing
        # Yeh tab tak chalega jab tak data aik 'dict' (dictionary) na ban jaye
        data = body_str
        for _ in range(3):
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    break
            else:
                break

        # 3. TYPE CHECK: Agar abhi bhi Dictionary nahi hai, toh return kar jao
        if not isinstance(data, dict):
            print(f"DEBUG: Data is {type(data)}, not a dict. Value: {data}")
            return {"status": "error_invalid_format"}

        # 4. SAFELY EXTRACT EVENT (Using type-safe .get)
        event_type = data.get('event')
        print(f"DEBUG: Event received: {event_type}")

        if event_type == 'message:in:new':
            # Data block nikaalein aur check karein ke woh bhi dict hai
            inner_data = data.get('data')