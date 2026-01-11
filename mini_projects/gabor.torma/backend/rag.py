import os
import chromadb
from chromadb.utils import embedding_functions
import json
from typing import List, Dict, Any

# Ensure directory exists
DB_DIR = "./chroma_db"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Initialize Chroma Client
# using persistent client to save data to disk
client = chromadb.PersistentClient(path=DB_DIR)

# Initialize OpenAI Embedding Function
# Using the default one provided by chromadb utils which uses text-embedding-ada-002 by default if openai is installed
# or we can specify it explicitly.
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)

# Get or create collection
collection = client.get_or_create_collection(
    name="meeting_context",
    embedding_function=openai_ef
)


def add_meeting_context(transcript: str, summary: str, notes: List[str], tasks: List[Dict], meeting_id: str | None = None, short_summary: str = "", meeting_date: str = "2024-01-01", file_hash: str = ""):
    """
    Adds meeting context to the vector database.
    We'll embed the summary and notes as they are the most dense information.
    """
    import uuid
    if not meeting_id:
        meeting_id = str(uuid.uuid4())

    # Create a composite text for embedding
    # We want to retrieve based on what happened in the meeting.
    # Summary + Notes is a good representation.
    
    notes_str = "\n".join([f"- {note}" for note in notes])
    tasks_str = "\n".join([f"- {t.get('title', '')}" for t in tasks])
    
    document_text = f"Summary:\n{summary}\n\nNotes:\n{notes_str}\n\nTasks:\n{tasks_str}"
    
    # Metadata to store structured info
    metadata = {
        "summary": summary,
        "short_summary": short_summary,
        "date": meeting_date,
        "type": "meeting",
        "file_hash": file_hash,
        "notes_json": json.dumps(notes),
        "tasks_json": json.dumps(tasks)
    }

    collection.add(
        documents=[document_text],
        metadatas=[metadata],
        ids=[meeting_id]
    )
    
    print(f"Added meeting {meeting_id} to RAG database with hash {file_hash}.")

    print(f"Added meeting {meeting_id} to RAG database.")

def list_meetings() -> List[Dict[str, Any]]:
    """
    Lists all stored meetings with metadata.
    """
    if collection.count() == 0:
        return []

    # Get all items (limit to a reasonable number if huge, but here all is fine)
    results = collection.get()
    
    meetings = []
    if results['ids']:
        for i in range(len(results['ids'])):
            meetings.append({
                "id": results['ids'][i],
                "metadata": _parse_metadata_json(results['metadatas'][i] if results['metadatas'] else {}),
                "content": results['documents'][i] if results['documents'] else None
            })
    return meetings

def query_similar_meetings(query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieves similar past meetings. Returns structured data.
    """
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    # results structure is a bit complex: {'ids': [['id1']], 'distances': [[0.1]], 'metadatas': [[{...}]], 'documents': [['text']]}
    output = []
    if results['ids']:
        ids = results['ids'][0]
        docs = results['documents'][0]
        metas = results['metadatas'][0] if results['metadatas'] else [{}] * len(ids)
        dists = results['distances'][0] if results['distances'] else [0.0] * len(ids)
        
        for i in range(len(ids)):
            # Filter results that are too far away (irrelevant)
            # Threshold of 1.0 roughly corresponds to cosine similarity of 0.5 (assuming L2 dist)
            if dists[i] < 0.8:
                output.append({
                    "id": ids[i],
                    "content": docs[i],
                    "metadata": _parse_metadata_json(metas[i]),
                    "distance": dists[i]
                })
    
    return output

def get_meeting_by_hash(file_hash: str) -> Dict[str, Any] | None:
    """
    Checks if a meeting with the given file hash already exists.
    """
    if not file_hash:
        return None
        
    results = collection.get(
        where={"file_hash": file_hash}
    )
    
    if results['ids']:
        # Return the first match
        return {
            "id": results['ids'][0],
            "metadata": results['metadatas'][0] if results['metadatas'] else {},
            "document": results['documents'][0] if results['documents'] else ""
        }
    return None

def _parse_metadata_json(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to parse JSON strings in metadata back to objects."""
    new_metadata = metadata.copy()
    if 'notes_json' in new_metadata:
        try:
            new_metadata['notes'] = json.loads(new_metadata['notes_json'])
        except:
            new_metadata['notes'] = []
    if 'tasks_json' in new_metadata:
        try:
            new_metadata['tasks'] = json.loads(new_metadata['tasks_json'])
        except:
            new_metadata['tasks'] = []
    return new_metadata
