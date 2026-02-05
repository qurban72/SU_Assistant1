from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
import sys
import json

# project.py se chain import karne ki koshish
try:
    from project import chain
except ImportError:
    print("ERROR: project.py file nahi mili ya chain missing hai!")
    sys.exit(1)

app = FastAPI()

# --- Settings ---
WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"
SECRET_TOKEN = "SU_SECRET_2026"

def is_greeting(text):
    greetings = {'hi', 'hello', 'hey', 'salam', 'aoa'}
    words = text.lower().strip().split()
    if not words: return False
    return words[0] in greetings or any(g in text.lower() for g in ['assalam', 'hello'])

def send_wassenger_message(phone, text):
    print(f"DEBUG: Sending to {phone}")
    payload = {"phone": phone, "message": str(text)}
    headers = {"Content-Type": "application/json", "Token": WASSENGER_TOKEN}
    try:
        res = requests.post(WASSENGER_URL, json=payload, headers=headers)
        print(f"DEBUG: Wassenger Status: {res.status_code}")
        return res.status_code
    except Exception as e:
        print(f"ERROR: Send failed: {e}")
        return 500

def process_whatsapp_ai(phone, user_query):
    try:
        if is_greeting(user_query) and len(user_query.split()) < 4:
            reply = "Hello! I am your SU Assistant. How can I help you today?"
        else:
            print("DEBUG: Calling AI...")
            reply = chain.invoke(user_query)
        
        send_wassenger_message(phone, reply)
    except Exception as e:
        print(f"AI ERROR: {e}")
        send_wassenger_message(phone, "I'm sorry, I'm having trouble with my AI brain right now.")

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        # 1. Raw body ko pakarna
        raw_body = await request.body()
        data = raw_body.decode("utf-8")

        # 2. STR ERROR FIX: Jab tak data dictionary (dict) na ban jaye, loads karte raho
        for _ in range(3):
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    break
            else:
                break

        # Check agar abhi bhi string hai toh error handle karein
        if isinstance(data, str):
            print("DEBUG: Data is still a string after decoding!")
            return {"status": "error"}

        print(f"DEBUG: Received Event: {data.get('event')}")

        if data.get('event') == 'message:in:new':
            inner = data.get('data', {})
            phone = inner.get('phone')
            user_query = inner.get('body', {}).get('text')

            if not phone: return {"status": "no_phone"}

            # Agar image bhej di hai (text missing hai)
            if not user_query:
                print("DEBUG: Media detected, sending warning.")
                background_tasks.add_task(send_wassenger_message, phone, "I can only handle text at the moment. Please type your question.")
                return {"status": "ok"}

            # Sab theek hai toh AI process karein
            background_tasks.add_task(process_whatsapp_ai, phone, user_query)
            return {"status": "ok"}

        return {"status": "ignored"}

    except Exception as e:
        print(f"CRASH ERROR: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
def home():
    return {"status": "online"}