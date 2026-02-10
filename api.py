from fastapi import FastAPI, Request, BackgroundTasks
import requests
import os
import json
import traceback


from project import rag_chain


app = FastAPI()

WASSENGER_TOKEN = os.getenv("WASSENGER_TOKEN")
WASSENGER_URL = "https://api.wassenger.com/v1/messages"
SECRET_TOKEN = "SU_SECRET_2026" 


def send_wassenger_message(phone, text):
    """WhatsApp par message bhejne ka function."""
    if not WASSENGER_TOKEN:
        print("ERROR: WASSENGER_TOKEN missing!")
        return
    
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
    except Exception as e:
        print(f"NETWORK_ERROR: {e}")

def process_ai_logic(phone, user_query):
    global rag_chain
    """AI se jawab nikalne ka background process."""
    try:
        query_lower = user_query.lower().strip()
        # Greetings handle karna
        if any(greet == query_lower for greet in ['hi', 'hello', 'salam', 'aoa', 'hey']):
            reply = "Hello! I am your SU Assistant. How can I help you with University of Sindh matters today?"
        elif rag_chain:
            print(f"DEBUG: Calling AI for: {user_query}")
            reply = rag_chain.invoke(user_query)
        else:
            reply = "I'm sorry, my AI brain is offline. Please try later."
        
        send_wassenger_message(phone, reply)
    except Exception as e:
        print(f"AI_LOGIC_ERROR: {e}")
        send_wassenger_message(phone, "I encountered an error processing your query.")

# --- API Endpoints ---

@app.get("/")
def home():
    return {"status": "online", "system": "SU Assistant"}

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        raw_body = await request.body()
        data = json.loads(raw_body.decode("utf-8"))
        
        if isinstance(data, str):
            data = json.loads(data)

        event = data.get("event")
        if event == "message:in:new":
            message_data = data.get("data", {})
            phone = message_data.get("fromNumber")
            
            # Check if it's text or media
            msg_type = message_data.get("type") # 'text', 'image', 'document' etc.
            user_query = message_data.get("body")

            if phone:
                if msg_type == "text" and user_query:
                    print(f"TEXT_MSG from {phone}: {user_query}")
                    background_tasks.add_task(process_ai_logic, phone, user_query)
                else:
                    # Agar image/audio/video hai toh ye reply jaye
                    print(f"MEDIA_DETECTED from {phone}: Type {msg_type}")
                    error_msg = "Currently, I can only process text-based questions. Please type your query."
                    background_tasks.add_task(send_wassenger_message, phone, error_msg)
            
            return {"status": "ok"}

        return {"status": "ignored"}

    except Exception as e:
        print(f"WEBHOOK_CRASH: {traceback.format_exc()}")
        return {"status": "error"}

@app.post("/ask")
async def ask_ai(request: Request):
    """Endpoint for Streamlit or other external apps."""
    # Security check
    incoming_token = request.headers.get("X-Secret-Token")
    if incoming_token != SECRET_TOKEN:
        return {"error": "Unauthorized access"}

    try:
        req_data = await request.json()
        user_question = req_data.get("question")
        
        if not user_question:
            return {"error": "No question provided"}

        if rag_chain:
            answer = rag_chain.invoke(user_question)
            return {"answer": answer}
        else:
            return {"error": "AI Chain not initialized"}
            
    except Exception as e:
        return {"error": str(e)}