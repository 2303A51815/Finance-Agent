import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def build_rag_chain(df):
    docs = []
    for _, row in df.iterrows():
        text = (
            f"On {row['date']}, "
            f"spent ₹{row['amount']} on {row['description']} "
            f"(category: {row['category']})"
        )
        docs.append(Document(page_content=text))

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(docs, embeddings)
    retriever = vectorstore.as_retriever()

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

    prompt = ChatPromptTemplate.from_template("""
You are a smart and friendly AI finance assistant 💰.

Rules:
- Give short, clear answers
- Be conversational
- Add relevant emojis
- Give small insights if possible
- DO NOT return JSON

Transactions:
{context}

Question: {question}
""")

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain


def ask(chain, question: str):
    return chain.invoke(question)