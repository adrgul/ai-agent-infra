import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from graph import build_graph
from models import Task

# Load environment variables
load_dotenv()

app = FastAPI(title="MeetingAI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build the graph once at startup
app.state.graph = build_graph()

class ProcessingResponse(BaseModel):
    summary: str
    short_summary: str
    notes: list[str]
    tasks: list[dict]


@app.get("/")
async def root():
    return {"message": "MeetingAI API is running"}

import re
import io
from docx import Document

def parse_srt(content: str) -> str:
    """Parses SRT subtitle content into plain text."""
    lines = content.splitlines()
    text = []
    for line in lines:
        if re.match(r'^\d+$', line.strip()):
            continue
        if re.match(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$', line.strip()):
            continue
        if not line.strip():
            continue
        text.append(line.strip())
    return " ".join(text)

def parse_docx(content_bytes: bytes) -> str:
    """Extracts text from a DOCX file."""
    doc = Document(io.BytesIO(content_bytes))
    return "\n".join([p.text for p in doc.paragraphs])

@app.get("/meetings")
async def get_meetings():
    """List all saved meetings."""
    from rag import list_meetings
    return list_meetings()

@app.get("/search")
async def search_meetings(q: str):
    """Search meetings by semantic content."""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    from rag import query_similar_meetings
    return query_similar_meetings(q)

@app.post("/process", response_model=ProcessingResponse)
async def process_transcript(file: UploadFile = File(...)):
    """
    Upload a transcript file (txt, md, srt, docx) and process it.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")
        
    filename = file.filename.lower()
    content_bytes = await file.read()
    transcript = ""

    try:
        if filename.endswith(".txt") or filename.endswith(".md"):
            transcript = content_bytes.decode("utf-8")
        elif filename.endswith(".srt"):
            raw_content = content_bytes.decode("utf-8")
            transcript = parse_srt(raw_content)
        elif filename.endswith(".docx"):
            transcript = parse_docx(content_bytes)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Supported: .txt, .md, .srt, .docx")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    if not transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript is empty")

    import hashlib
    file_hash = hashlib.sha256(content_bytes).hexdigest()
    
    from rag import get_meeting_by_hash
    existing_meeting = get_meeting_by_hash(file_hash)
    if existing_meeting:
        raise HTTPException(status_code=409, detail="File already processed")

    if not os.getenv("OPENAI_API_KEY"):
         raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    # Invoke the graph
    initial_state = {
        "transcript": transcript,
        "notes": [],
        "tasks": [],
        "summary": ""
    }
    
    try:
        result = app.state.graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing transcript: {str(e)}")

    # Format output
    tasks = [t.model_dump() if isinstance(t, Task) else t for t in result.get("tasks", [])]
    summary = result.get("summary", "")
    short_summary = result.get("short_summary", "")
    notes = result.get("notes", [])

    meeting_date = result.get("meeting_date")
    
    if not meeting_date:
        meeting_date = datetime.now().strftime("%Y-%m-%d")

    # Save to RAG
    # separate thread or background task would be better in production
    try:
        from rag import add_meeting_context
        add_meeting_context(
            transcript=transcript,
            summary=summary,
            notes=notes,
            tasks=tasks,
            short_summary=short_summary,
            meeting_date=meeting_date,
            file_hash=file_hash
        )
    except Exception as e:
        print(f"Error saving to RAG: {e}")

    return {
        "summary": summary,
        "short_summary": short_summary,
        "notes": notes,
        "tasks": tasks,

    }
