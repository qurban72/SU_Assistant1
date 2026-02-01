from fastapi import FastAPI, Form, BackgroundTasks, Response
from twilio.rest import Client
import os
from project import chain

app = FastAPI()

# Twilio Credentials (Railway Variables se uthayega)
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

import traceback

def send_ai_reply(user_phone, user_msg):
    try:
        print(f"DEBUG: Processing message for {user_phone}...")
        
        # 1. Check karein ke 'chain' object initialize hua hai ya nahi
        if 'chain' not in globals():
            print("ERROR: 'chain' object is not defined!")
            return

        # 2. AI se answer mangwao
        ans = chain.invoke(user_msg)
        print(f"DEBUG: AI Response generated: {ans[:50]}...") # Pehle 50 chars print karein

        # 3. Twilio API ke zariye reply bhejo
        # Yaad rahe ke user_phone ka format 'whatsapp:+92...' hona chahiye
        message = client.messages.create(
            from_='whatsapp:+14155238886',
            body=ans,
            to=user_phone
        )
        print(f"DEBUG: Message sent successfully! SID: {message.sid}")

    except Exception as e:
        print(f"Background Task Error: {str(e)}")
        # Ye line pura error ka rasta (Line number) dikhayegi
        traceback.print_exc()
@app.get('/')
def home():
    return "SU Assistant is Online"

@app.post('/whatsapp')
async def whatsapp_reply(
    background_tasks: BackgroundTasks,
    Body: str = Form(...),
    From: str = Form(...)
):
    # Foran background task shuru karo
    background_tasks.add_task(send_ai_reply, From, Body)
    
    # Twilio ko foran 200 OK bhej do (Taakay timeout na ho)
    return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")