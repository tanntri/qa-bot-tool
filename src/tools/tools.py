from langchain_core.tools import tool
from utils.vector import VectorStore
from dotenv import load_dotenv
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent

load_dotenv()

vector_store_instance = VectorStore()
retriever = vector_store_instance.get_retriever()

@tool
def retriever_tool(query: str) -> str:
    """Tool to retrieve relevant documents based on a query."""
    docs = retriever.invoke(query)
    return "\n\n".join([doc.page_content for doc in docs])

if __name__ == "__main__":
    sample_query = "Any customer feedback about scrollbar related issues?"
    retrieved_content = retriever_tool.invoke(sample_query)
    print("Retrieved Documents:")
    print(retrieved_content)