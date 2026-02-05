from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
from project import chain  # Aapka RAG chain

app = FastAPI()

# Railway Variables
WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"
SECRET_TOKEN = "SU_SECRET_2026"  # Streamlit app ke liye security password

# --- HELPER FUNCTIONS ---

def is_greeting(text):
    """Checks if the user message is a simple greeting."""
    greetings = {'hi', 'hello', 'hey', 'salam', 'assalam', 'aoa', 'how are you'}
    # Sirf pehla word check karein aur clean karein
    clean_text = text.lower().strip()
    return clean_text in greetings or any(word in clean_text for word in ['hello', 'hi', 'salam'])

def send_wassenger_message(phone, text):
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
        return response.status_code
    except Exception as e:
        print(f"Error sending to Wassenger: {e}")
        return 500

def process_whatsapp_ai(phone, user_query):
    try:
        # 1. Check if it's just a greeting (limit to short messages)
        if is_greeting(user_query) and len(user_query.split()) < 4:
            reply = "Hello! I am your SU Assistant. How can I help you with University of Sindh matters today?"
        else:
            # 2. Process with RAG chain
            reply = chain.invoke(user_query)
        
        send_wassenger_message(phone, reply)
    except Exception as e:
        print(f"AI Logic Error: {e}")
        send_wassenger_message(phone, "I apologize, but I am having trouble processing that right now.")

# --- ENDPOINT 1: WHATSAPP WEBHOOK ---

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        
        # Security: Only process incoming new messages
        if data.get('event') != 'message:in:new':
            return {"status": "ignored"}

        # Safety: Use .get() to avoid KeyError 'phone'
        message_data = data.get('data', {})
        phone = message_data.get('phone')
        
        if not phone:
            return {"status": "error", "message": "No phone number found"}

        msg_body = message_data.get('body', {})
        user_query = msg_body.get('text')
        
        # Check if message is TEXT or MEDIA
        if not user_query:
            warning_msg = "Currently, I can only process text messages. Please type your question."
            send_wassenger_message(phone, warning_msg)
            return {"status": "non_text_ignored"}

        # Process in background to prevent timeout
        background_tasks.add_task(process_whatsapp_ai, phone, user_query)
        return {"status": "ok"}

    except Exception as e:
        print(f"Webhook Error: {e}")
        return {"status": "error", "message": str(e)}

# --- ENDPOINT 2: FOR STREAMLIT APP (WITH SECURITY) ---

@app.post("/ask")
async def ask_ai(request: Request):
    # Security Token Check
    incoming_token = request.headers.get("X-Secret-Token")
    if incoming_token != SECRET_TOKEN:
        return {"error": "Unauthorized access"}

    data = await request.json()
    user_query = data.get("question")
    
    if not user_query:
        return {"error": "No question provided"}
    
    # Handle Greetings for Streamlit too
    if is_greeting(user_query) and len(user_query.split()) < 4:
        return {"answer": "Hello! How can I help you today?"}
    
    ai_response = chain.invoke(user_query)
    return {"answer": ai_response}

@app.get("/")
def home():
    return {"message": "SU Assistant Server is Online!"}