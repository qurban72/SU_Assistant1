
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os


load_dotenv()


HF_TOKE = os.getenv("HUGGINGFACE_KEY")
g_toke = os.getenv("GOOGLE_API_KEY")

llm = HuggingFaceEndpoint(
    repo_id="stepfun-ai/Step-3.5-Flash", # Example of a highly compatible model
    task="text-generation",
    max_new_tokens=512,
    temperature=0.5,
    huggingfacehub_api_token=HF_TOKE
)
model = ChatHuggingFace(llm = llm)

embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=HF_TOKE
)

vectorstore = FAISS.load_local(
    "faiss_index", 
    embeddings, 
    allow_dangerous_deserialization=True
)

retriever = vectorstore.as_retriever(
    search_type="mmr", 
    search_kwargs={"k": 4, "fetch_k": 20} 
)


prompt = ChatPromptTemplate.from_template("""
You are the Official SU Assistant for the University of Sindh. Your goal is to provide accurate, polite, and human-like assistance to students.

IDENTITY RULES:
- If the user asks who created you, who is your developer, or about your origin: 
  Always respond: "I am an AI Assistant created by Mr.QK (final  year student of 'Saylani Mass IT Training' and 3rd year  student of  university of sindh  )  ."
- If asked about your name, you are "SU-ASSISTANT".
### OPERATIONAL RULES:
1. **Greetings:** If the user greets you (e.g., "Hi", "Hello", "Hey", "Assalam o Alaikum"), respond with a warm, professional greeting and ask how you can assist them today. 
2. **University Focus:** You only answer questions related to the University of Sindh. If the user asks about unrelated topics (e.g., general knowledge, celebrities, sports,maths,code etc.), politely inform them: "I can only assist with queries related to the University of Sindh."
3. **Information Gaps:** If the question is about the university but you cannot find the answer in the provided context, respond exactly: "I apologize, but I am currently in a training phase and trained on limited data to answer this specific question yet."
4. **No Robotic Language:** NEVER start your response with "Based on the provided context," "According to the documents," or "The context states." Answer the question directly as if you already know the information.

Context:
{context}

User Question:
{question}

Assistant's Direct Response:
""")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

rag_chain = chain