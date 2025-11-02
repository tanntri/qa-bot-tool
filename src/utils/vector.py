import os
from pathlib import Path
import chromadb
from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever as LangChainVectorStoreRetriever
from dotenv import load_dotenv
from utils.llm import EmbeddingModel

load_dotenv()

class VectorStore:
    """
    Connects to a local Chroma vector store and returns a retriever.
    This class is intended for local development or self-hosted usage.
    """

    def __init__(self):
        # Configuration
        self.collection_name = os.getenv("CHROMA_COLLECTION_NAME", "bug_and_feedback_reports")

        # Optional: directory for persistent Chroma database
        chroma_persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.persist_dir = Path(chroma_persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model
        self.embedding_model = EmbeddingModel().get_embedding_model()

        # Initialize local Chroma client
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db"
        )

        # Load or create collection
        self.vector_store = self._load_vector_store()

    def _load_vector_store(self):
        """
        Load (or create) a local Chroma collection.
        """
        print(f"Loading Chroma collection '{self.collection_name}' from local store at {self.persist_dir}")

        vector_store = Chroma(
            client=self.chroma_client,
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=str(self.persist_dir)
        )
    
        collection_count = vector_store._collection.count()
        print(f"Collection '{self.collection_name}' loaded with {collection_count} documents.")
        return vector_store

    def get_retriever(self) -> LangChainVectorStoreRetriever:
        """
        Return a retriever configured for similarity search.
        """
        return self.vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

if __name__ == "__main__":
    try:
        vs = VectorStore()
        retriever = vs.get_retriever()
        print("Successfully initialized local VectorStore and got retriever.")

        query = "How to fix upload stuck at 99%?"
        docs = retriever.invoke(query)
        print("Query results:", docs)

    except Exception as e:
        print(f"An error occurred: {e}")

