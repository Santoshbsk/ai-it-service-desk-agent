from rag import load_documents, embeddings
from langchain_chroma import Chroma

from config import CHROMA_PATH, COLLECTION_NAME


documents = load_documents()

vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_PATH
)

print(f"Indexed {len(documents)} documents successfully.")