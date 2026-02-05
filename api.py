from fastapi import FastAPI, BackgroundTasks, Request
import requests
import os
import traceback
from project import chain # Aapka RAG chain

app = FastAPI()

# Railway Variables mein WASSENGER_TOKEN add kar dena
WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")

def send_ai_reply(user_phone, user_msg):
    try:
        print(f"DEBUG: Processing message for {user_phone}...")
        
        # 1. AI se answer mangwao (RAG Chain)
        ans = chain.invoke(user_msg)
        print(f"DEBUG: AI Response generated: {ans[:50]}...")

        # 2. Wassenger API ke zariye reply bhejo
        url = "https://api.wassenger.com/v1/messages"
        headers = {
            "Token": WASSENGER_TOKEN,
            "Content-Type": "application/json"
        }
        payload = {
            "phone": user_phone, # Wassenger ko sirf number chahiye (+92...)
            "message": ans
        }
        
        response = requests.post(url, json=payload, headers=headers)
        print(f"DEBUG: Wassenger Response: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Background Task Error: {str(e)}")
        traceback.print_exc()

@app.get('/')
def home():
    return "SU Assistant (Wassenger) is Online"

@app.post('/whatsapp')
async def whatsapp_reply(request: Request, background_tasks: BackgroundTasks):
    # Wassenger JSON bhejta hai
    data = await request.json()
    
    # Check karein ke ye naya message event hai
    if data.get('event') == 'message:in:new':
        user_msg = data['data']['body']
        user_phone = data['data']['fromNumber'] # Direct number milta hai (+92...)
        
        # Background task shuru karo
        background_tasks.add_task(send_ai_reply, user_phone, user_msg)
    
    return {"status": "accepted"}

if __name__ == "__main__":
    import uvicorn
    # Railway ke liye port handling
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)