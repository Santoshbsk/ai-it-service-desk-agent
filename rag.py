from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from config import GEMINI_API_KEY,LLM_MODEL
from config import CHROMA_PATH, COLLECTION_NAME


embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GEMINI_API_KEY
)


vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_PATH,
    embedding_function=embeddings
)

reranker_llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0
)

def rerank_documents(query, documents, top_k=3):

    document_text = ""

    for i, doc in enumerate(documents):

        document_text += f"""
DOCUMENT {i}

SOURCE:
{doc.metadata.get("source", "Unknown")}

CONTENT:
{doc.page_content}

--------------------
"""

    prompt = f"""
You are a document relevance ranking system.

User query:

{query}

Below are candidate IT support documents.

{document_text}

Rank the documents according to how useful they are
for answering the user's query.

Return ONLY the document numbers in descending order
of relevance.

Example:

2, 0, 4
"""

    result = reranker_llm.invoke(prompt)

    if isinstance(result.content, list):
        text = "".join(
            block.get("text", "")
            if isinstance(block, dict)
            else str(block)
            for block in result.content
        )
    else:
        text = str(result.content)

    try:

        rankings = [
            int(x.strip())
            for x in text.split(",")
            if x.strip().isdigit()
        ]

        ranked_documents = [
            documents[i]
            for i in rankings
            if i < len(documents)
        ]

        return ranked_documents[:top_k]

    except Exception:

        return documents[:top_k]


def retrieve_context(query, k=5):

    results = vectorstore.similarity_search(
        query,
        k=k
    )

    reranked = rerank_documents(
        query,
        results,
        top_k=3
    )
    return reranked

def generate_rag_answer(query, documents):

    context = "\n\n".join(
        [
            f"Source: {doc.metadata.get('source', 'Unknown')}\n"
            f"{doc.page_content}"
            for doc in documents
        ]
    )

    prompt = f"""
You are an IT Service Desk AI Agent.

User question:
{query}

Knowledge base:
{context}

Answer the question using only the knowledge base.

Rules:

- Do not invent information.
- Do not claim an action was performed.
- Give practical troubleshooting steps.
- If the knowledge base does not contain enough information,
  say so.

Return only the answer.
"""

    result = reranker_llm.invoke(prompt)

    if isinstance(result.content, list):
        text = "".join(
            block.get("text", "")
            if isinstance(block, dict)
            else str(block)
            for block in result.content
        )
    else:
        text = str(result.content)

    return text.strip()