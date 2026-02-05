# %%
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import os

# load local environment variables
load_dotenv()

# Hugging Face API token from .env
HF_TOKE = os.getenv("HUGGINGFACE_KEY")
g_toke = os.getenv("GOOGLE_API_KEY")

# %%

# 1. model for chat
llm = HuggingFaceEndpoint(
    # Llama 3.1 use karein behtar results ke liye
    repo_id="meta-llama/Llama-3.1-8B-Instruct", 
    task="text-generation",
    max_new_tokens=512,
    repetition_penalty=1.1, # Ye bot ko bar bar ek hi baat karne se rokta hai
    return_full_text=False,
    huggingfacehub_api_token=HF_TOKE,
)
model = ChatHuggingFace(llm=llm)

# %%

# 2. Vectorstore Setup
embeddings = GoogleGenerativeAIEmbeddings(
    model="text-embedding-004",
    google_api_key=g_toke
)
vectorstore = FAISS.load_local(
    "faiss_index", 
    embeddings, 
    allow_dangerous_deserialization=True
)

# %%

retriever = vectorstore.as_retriever(
    search_type="mmr", 
    search_kwargs={"k": 8, "fetch_k": 25} 
)

# %%

prompt = ChatPromptTemplate.from_template("""
You are the Official SU Assistant for the University of Sindh. Your goal is to provide accurate, polite, and human-like assistance to students.

### OPERATIONAL RULES:
1. **Greetings:** If the user greets you (e.g., "Hi", "Hello", "Hey", "Assalam o Alaikum"), respond with a warm, professional greeting and ask how you can assist them today. 
2. **University Focus:** You only answer questions related to the University of Sindh. If the user asks about unrelated topics (e.g., general knowledge, celebrities, sports), politely inform them: "I can only assist with queries related to the University of Sindh."
3. **Information Gaps:** If the question is about the university but you cannot find the answer in the provided context, respond exactly: "I apologize, but I am currently in a training phase and do not have enough data to answer this specific question yet."
4. **No Robotic Language:** NEVER start your response with "Based on the provided context," "According to the documents," or "The context states." Answer the question directly as if you already know the information.
5. **Clarity Check:** If a question has more than 2-3 significant typing mistakes or is completely unreadable, say: "Your question contains several typing errors. Please correct them so I can understand and help you better."

Context:
{context}

User Question:
{question}

Assistant's Direct Response:
""")

# %%

# 4. chain
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

# %%
# 5. Execution
# Example usage:
# answer = chain.invoke("What is the syllabus for IT department?")
# print(answer)
