from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
import json

try:
    from project import chain
except ImportError:
    print("CRITICAL: project.py not found!")

app = FastAPI()

WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"

def send_wassenger_message(phone, text):
    payload = {"phone": phone, "message": str(text)}
    headers = {"Content-Type": "application/json", "Token": WASSENGER_TOKEN}
    try:
        r = requests.post(WASSENGER_URL, json=payload, headers=headers)
        print(f"DEBUG: Sent to {phone}, Status: {r.status_code}")
    except Exception as e:
        print(f"ERROR: Sending failed: {e}")

def process_whatsapp_ai(phone, query):
    try:
        # Greeting check
        if any(word in query.lower() for word in ['hi', 'hello', 'salam', 'aoa']):
            reply = "Hello! I am your SU Assistant. How can I help you today?"
        else:
            reply = chain.invoke(query)
        send_wassenger_message(phone, reply)
    except Exception as e:
        print(f"AI Error: {e}")

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        # 1. Get raw body
        raw_body = await request.body()
        body_str = raw_body.decode("utf-8")
        
        # 2. Hardcore JSON Parsing
        data = body_str
        for _ in range(5):  # 5 baar koshish karein decode karne ki
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    break
            else:
                break

        # 3. Agar ab bhi string hai, toh manual check karein
        if not isinstance(data, dict):
            print(f"CRITICAL DEBUG: Data is still a string! Value: {data}")
            return {"status": "error", "reason": "data_not_dict"}

        # 4. Ab safely keys nikaalein
        event_type = data.get('event')
        print(f"DEBUG: Event Received: {event_type}")

        if event_type == 'message:in:new':
            # Use .get() everywhere to be 100% safe
            message_data = data.get('data', {})
            phone = message_data.get('phone')
            body_obj = message_data.get('body', {})
            user_query = body_obj.get('text')

            if phone:
                if user_query:
                    background_tasks.add_task(process_whatsapp_ai, phone, user_query)
                else:
                    # Message is media/image
                    background_tasks.add_task(send_wassenger_message, phone, "I can only handle text messages right now.")
            
        return {"status": "ok"}

    except Exception as e:
        # Yahan error print hoga jo aapne logs mein bheja tha
        print(f"CRASH ERROR IN WEBHOOK: {e}")
        return {"status": "error"}

@app.get("/")
def home(): return {"status": "online"}