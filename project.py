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
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    task="chat-completion",
    max_new_tokens=512,
    return_full_text=False,
    huggingfacehub_api_token=HF_TOKE,  # safe token usage
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
You are a helpful and polite university assistant.

- Answer the question **directly and concisely** using **only the context provided**.
- **Do NOT** use filler phrases such as "Based on the context," "I’m not sure," or "According to the documents."
- If the answer is not in the context, respond exactly: 
"I’m in development phase and don’t have enough data to answer this question."
If question has more than 2 typing mistakes then say your question has so many typing mistakes please correct it
Or if the question is not understandable then say "I can't understand your question."

Context:
{context}

Question:
{question}

Answer:
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
