import os
import sys
import glob
from dotenv import load_dotenv

# Add backend directory to sys.path to allow imports from services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv()

def ingest_docs():
    print("--- Starting Document Ingestion ---")
    
    api_key = os.getenv("PINECONE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or not openai_key:
        print("Error: Missing API Keys")
        return

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=openai_key)
    index_name = "knowledge-router"
    
    # Process HR Docs
    print("\nProcessing HR Documents...")
    process_domain_docs("data/docs/hr_*.md", "hr", embeddings, index_name)

    # Process IT Docs
    print("\nProcessing IT Documents...")
    process_domain_docs("data/docs/it_*.md", "it", embeddings, index_name)
    
    print("\n--- Ingestion Complete ---")

def process_domain_docs(file_pattern, namespace, embeddings, index_name):
    files = glob.glob(file_pattern)
    if not files:
        print(f"No files found for pattern: {file_pattern}")
        return

    all_splits = []
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    for file_path in files:
        print(f"  Loading: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            
        splits = markdown_splitter.split_text(text)
        
        # Add source metadata
        for split in splits:
            split.metadata["source"] = os.path.basename(file_path)
            split.metadata["domain"] = namespace
            
        all_splits.extend(splits)
    
    print(f"  Uploading {len(all_splits)} chunks to namespace '{namespace}'...")
    
    PineconeVectorStore.from_documents(
        documents=all_splits,
        embedding=embeddings,
        index_name=index_name,
        namespace=namespace
    )
    print("  Upload successful.")

if __name__ == "__main__":
    ingest_docs()
