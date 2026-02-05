from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
import sys

# Try to import chain from project.py
try:
    from project import chain
except ImportError:
    print("ERROR: project.py or 'chain' not found! Make sure project.py is in the same folder.")
    sys.exit(1)

app = FastAPI()

# --- Configuration (Railway Variables) ---
WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"
SECRET_TOKEN = "SU_SECRET_2026"  # Streamlit app headers mein yehi use karein

# --- Helper Functions ---

def is_greeting(text):
    """Checks if the message is a simple greeting."""
    greetings = {'hi', 'hello', 'hey', 'salam', 'assalam', 'aoa', 'how are you'}
    words = text.lower().strip().split()
    if not words:
        return False
    return words[0] in greetings or any(g in text.lower() for g in ['assalam', 'hello'])

def send_wassenger_message(phone, text):
    """Sends a message back to the user via Wassenger."""
    print(f"DEBUG: Attempting to send message to {phone}")
    payload = {
        "phone": phone,
        "message": str(text)
    }
    headers = {
        "Content-Type": "application/json",
        "Token": WASSENGER_TOKEN
    }
    try:
        response = requests.post(WASSENGER_URL, json=payload, headers=headers)
        print(f"DEBUG: Wassenger API Status: {response.status_code} - Response: {response.text}")
        return response.status_code
    except Exception as e:
        print(f"ERROR: Failed to call Wassenger API: {e}")
        return 500

def process_whatsapp_ai(phone, user_query):
    """Background task to handle AI logic and reply."""
    print(f"DEBUG: Processing AI for {phone}. Query: {user_query}")
    try:
        # 1. Greeting Logic
        if is_greeting(user_query) and len(user_query.split()) < 4:
            reply = "Hello! I am your SU Assistant. How can I help you with University of Sindh matters today?"
            print("DEBUG: Greeting detected. Skipping RAG.")
        else:
            # 2. RAG Logic (Gemini/AI)
            print("DEBUG: Calling AI Chain...")
            reply = chain.invoke(user_query)
            print(f"DEBUG: AI Reply Generated: {reply[:50]}...")

        # 3. Send Reply
        send_wassenger_message(phone, reply)
        
    except Exception as e:
        print(f"ERROR in process_whatsapp_ai: {e}")
        send_wassenger_message(phone, "I'm sorry, I'm having trouble processing your request right now. Please try again.")

# --- API Endpoints ---

@app.get("/")
def home():
    return {"status": "online", "message": "SU Assistant is running"}

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        print(f"DEBUG: Webhook received event: {data.get('event')}")

        # Process only NEW incoming messages
        if data.get('event') == 'message:in:new':
            inner_data = data.get('data', {})
            phone = inner_data.get('phone')
            msg_body = inner_data.get('body', {})
            user_query = msg_body.get('text')

            if not phone:
                print("DEBUG: No phone number found in data. Ignoring.")
                return {"status": "error", "message": "No phone"}

            if not user_query:
                print("DEBUG: Non-text message received.")
                send_wassenger_message(phone, "I can currently only understand text messages. Please type your query.")
                return {"status": "non_text_ignored"}

            # Start background task
            background_tasks.add_task(process_whatsapp_ai, phone, user_query)
            return {"status": "ok", "message": "Task queued"}

        return {"status": "ignored", "event": data.get('event')}

    except Exception as e:
        print(f"ERROR: Webhook crash: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/ask")
async def ask_ai(request: Request):
    """Endpoint for Streamlit App."""
    token = request.headers.get("X-Secret-Token")
    if token != SECRET_TOKEN:
        return {"error": "Unauthorized"}

    try:
        data = await request.json()
        user_query = data.get("question", "")
        
        if is_greeting(user_query) and len(user_query.split()) < 4:
            return {"answer": "Hello! I am your SU Assistant. How can I help you today?"}

        response = chain.invoke(user_query)
        return {"answer": response}
    except Exception as e:
        return {"error": str(e)}