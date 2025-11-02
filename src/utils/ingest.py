import chromadb
import re
import hashlib
from langchain_chroma import Chroma
from utils.llm import EmbeddingModel
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PaginatedPipelineOptions
from docling.document_converter import DocumentConverter, WordFormatOption
from dotenv import load_dotenv
from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PaginatedPipelineOptions
from docling.document_converter import DocumentConverter, WordFormatOption

load_dotenv()

def get_file_hash(file_path: Path) -> str:
    """
    Generate an MD5 hash of a file's contents.
    
    Args:
        file_path (Path): The path to the file.
        
    Returns:
        str: The MD5 hash of the file.
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def convert_docx_to_markdown(doc_path: Path) -> str:
    """
    Convert a DOCX document to a normalized markdown string suitable for
    structured chunking (For example, Bug or Feedback reports).

    Args:
        doc_path (Path): Path to the DOCX file.

    Returns:
        str: Clean, markdown-formatted content.
    """
    print(f"Converting DOCX to Markdown: {doc_path}")

    pipeline_options = PaginatedPipelineOptions()
    converter = DocumentConverter(
        format_options={
            InputFormat.DOCX: WordFormatOption(pipeline_options=pipeline_options)
        }
    )

    result = converter.convert(doc_path)
    document = result.document
    raw_markdown = document.export_to_markdown()

    # Remove text styles in docx files (in this case, bold)
    raw_markdown = re.sub(r'\*\*(.*?)\*\*', r'\1', raw_markdown)

    # Convert "Bug #1" or "Feedback #1" into proper Markdown headers
    markdown_text = re.sub(r'(?<!#)(\bBug\s+#\d+)', r'# \1', raw_markdown)
    markdown_text = re.sub(r'(?<!#)(\bFeedback\s+#\d+)', r'# \1', markdown_text)

    print(f"Finished converting {doc_path.name}")
    return markdown_text


def split_markdown(markdown_text: str, file_name: str, file_hash: str):
    """
    Split markdown into chunks and add file name to metadata.
    
    Args:
        markdown_text (str): The markdown content to split.
        file_name (str): The name of the source file.
        
    Returns:
        List[Document]: A list of document chunks with metadata.
    """
    print("Splitting markdown into chunks...")
    headers_to_split_on = [
        ("#", "Header 1"),
    ]
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
    splits = splitter.split_text(markdown_text)
    
    # Add the file name to the metadata of each chunk
    for doc in splits:
        doc.metadata["file_name"] = file_name
        doc.metadata["file_hash"] = file_hash

    return splits

def ingest_to_chroma(markdown_chunks, collection_name: str, embedding_model, file_hash: str):
    """
    Ingests document chunks into a local Chroma collection only if the file hash has changed.

    Args:
        markdown_chunks (List[Document]): The document chunks to ingest.
        collection_name (str): The name of the Chroma collection.
        embedding_model (EmbeddingFunction): The embedding model to use.
        persist_directory (str): Directory to persist the local Chroma database.
        file_hash (str): The hash of the source file.
    """
    
    # Initialize local Chroma client
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    # Check for an existing collection and the presence of the current file hash
    try:
        if collection_name in [c.name for c in chroma_client.list_collections()]:
            collection = chroma_client.get_collection(name=collection_name)
            # Use the where clause to find if any document has the current hash
            results = collection.get(where={"file_hash": file_hash})
            if results["ids"]:
                print(f"Collection '{collection_name}' already contains content with this hash. Skipping ingestion.")
                return
    except Exception as e:
        print(f"An error occurred while checking the collection: {e}")

    print(f"Creating or updating collection '{collection_name}'...")
    Chroma.from_documents(
        documents=markdown_chunks,
        embedding=embedding_model,
        collection_name=collection_name,
        client=chroma_client
    )

    print(f"Successfully ingested data into collection '{collection_name}'.")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent
    # Path to the DOCX file
    docx_path = base_dir / "data"
    docx_files = list(docx_path.glob("*.docx"))

    if not docx_files:
        raise FileNotFoundError(f"No DOCX files found in {docx_path}")
    
    for docx_path in docx_files:
        print(f"Processing file: {docx_path}")
        file_hash = get_file_hash(docx_path)
    
        # Convert DOCX to markdown
        markdown_content = convert_docx_to_markdown(docx_path)

        ingest_to_chroma(
            markdown_chunks=split_markdown(markdown_content, docx_path.name, file_hash),
            collection_name="bug_and_feedback_reports",
            embedding_model=EmbeddingModel().get_embedding_model(),
            file_hash=file_hash
        )
   
    print("Document ingested successfully.")
