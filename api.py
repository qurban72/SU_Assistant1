from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
from project import chain  # Aapka RAG chain

app = FastAPI()

# Railway Variables
WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"

def send_wassenger_message(phone, text):
    payload = {
        "phone": phone,
        "message": text
    }
    headers = {
        "Content-Type": "application/json",
        "Token": WASSENGER_TOKEN
    }
    response = requests.post(WASSENGER_URL, json=payload, headers=headers)
    return response.status_code

def process_whatsapp_ai(phone, user_query):
    # RAG Chain se jawab lena
    ai_response = chain.invoke(user_query)
    # WhatsApp par bhejna
    send_wassenger_message(phone, ai_response)

# --- ENDPOINT 1: WHATSAPP WEBHOOK ---
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    # Check if it's an incoming message
    if data.get('event') == 'message:in:new':
        phone = data['data']['phone']
        msg_obj = data['data'].get('body', {})
        
        # Check if message is TEXT or MEDIA
        user_query = msg_obj.get('text')
        
        if not user_query:
            # Agar text nahi hai (matlab image, audio, file hai)
            warning_msg = "I apologize, but currently I can only process text messages. Please type your question."
            send_wassenger_message(phone, warning_msg)
            return {"status": "non_text_ignored"}

        # Agar text hai toh AI process kare background mein
        background_tasks.add_task(process_whatsapp_ai, phone, user_query)
        
    return {"status": "ok"}

# --- ENDPOINT 2: FOR STREAMLIT APP ---
@app.post("/ask")
async def ask_ai(request: Request):
    # Streamlit se sirf text aayega
    data = await request.json()
    user_query = data.get("question")
    
    if not user_query:
        return {"error": "No question provided"}
    
    # RAG se jawab le kar direct wapas bhej dena
    ai_response = chain.invoke(user_query)
    return {"answer": ai_response}

@app.get("/")
def home():
    return {"message": "SU Assistant Server is Running!"}