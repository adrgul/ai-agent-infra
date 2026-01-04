You are GitHub Copilot. Generate a COMPLETE working full-stack application: Python FastAPI backend + React TypeScript frontend.

Goal
Build a Hungarian UI “RAG agent” app with categories:

User uploads documents and assigns them to a category (e.g., AI, HR).

Backend chunks the document (token-based with tiktoken), creates embeddings (OpenAI), indexes into a persistent local Chroma vector DB.

User chats with an AI agent; the agent answers ONLY using retrieved chunks (RAG).

The agent uses LangGraph to orchestrate a pipeline:

Decide category (LLM router)

Retrieve from that category’s vector index

Generate answer with citations

Persist conversation history to JSON files on disk (every message).

Keep a user profile JSON on disk (never deleted).

Provide “Reset context” button: clears session conversation history only (NOT the user profile, NOT the vector DB, NOT uploads).

Must-have constraints

Dockerized with docker-compose (backend + frontend).

Backend: Python 3.11+, FastAPI, LangGraph, OpenAI SDK.

OpenAI API key from env var OPENAI_API_KEY.

Embeddings: text-embedding-3-small.

Chat model: default gpt-4o-mini.

Use Chat Completions API for generation and routing decisions.

Vector DB: ChromaDB persistent on disk.

Chunking: token-based with tiktoken. Defaults: chunk_size_tokens=900, overlap_tokens=150.

Retrieval: top_k=5.

Deduplication: remove near-duplicate chunks in context.

Answers in Hungarian.

RAG rule: “Only use provided context; if not in context, say you cannot find it in the uploaded documents.”

Provide citations: include chunk_id and short quoted snippet per cited chunk.

Categories: functional requirements

On upload the user MUST provide a category name.

Frontend must offer:

Dropdown of existing categories (for that user)

Option to type a NEW category

If user has already created categories before, the UI should “offer which category to upload into or create a new one”.

For each user chat question:

Send the user’s question + list of existing categories to the LLM to decide which category to search.

If LLM decides a category that does NOT exist (or decides none), respond:
“Nincs ilyen kategóriájú dokumentum feltöltve, nem tudok a feltöltött dokumentumok alapján válaszolni.”

Example behavior:

Existing category: AI with AI.md

Q: “Miért fontos a RAG?” → LLM routes to category “AI” → retrieve there → answer.

Q: “Milyen munkabiztonsági előírásaink vannak?” → LLM tries “Munkabiztonság/HR” → if category not uploaded → return the “no such category” message.

Document handling

Implement .md ingestion end-to-end now.

Prepare for .pdf and .docx ingestion later:

Create a DocumentTextExtractor interface with implementations:

MarkdownExtractor (implemented)

PdfExtractor (stub / clear NotImplemented error)

DocxExtractor (stub / clear NotImplemented error)

Later OCR can be added as a tool; do not implement OCR now.

Indexing strategy (category-based)

Indexing is per category (not per document):

Each category corresponds to one Chroma collection, e.g. cat_{user_id}_{slug(category)}.

When a document is uploaded into category C:

chunk it

embed chunks

add chunks to that category collection

store metadata per chunk: upload_id, category, source_file, chunk_index, start_char, end_char, optional section_title

Deletion:

Deleting an uploaded document must remove:

the stored upload file

derived artifacts folder

and all vectors from the category collection that belong to that upload_id (delete by ids or by where-filter if supported; store chunk ids for reliable deletion).

Persistence & filesystem layout (must follow)

data/users/{user_id}.json

data/sessions/{session_id}.json

data/uploads/{user_id}/{category}/{upload_id}__{original_filename}

data/derived/{user_id}/{category}/{upload_id}/chunks.json

chroma persistence folder: data/chroma_db (mounted volume)

Never delete user profile.

Reset only clears session messages list.

User Profile model (extend)

user_id: string

language: string default “hu”

categories: list[string] (or derived from uploads; but store it explicitly for fast UI)

optional preferences

Conversation history JSON (persist everything)
Each message:

role: "user" | "assistant" | "system" | "tool"

content: string

timestamp: ISO string

metadata: optional (tool_name, category_routed, upload_id, chunk_ids, etc.)

Backend API (FastAPI)

POST /api/chat
Request: { user_id: string, session_id: string, message: string }
Behavior:

Reset context special command or reset flag:

Load/create profile (do not delete).

Reset session JSON messages to [].

Return: “Kontextus törölve, tiszta lappal megyünk tovább.”

Normal:

Load profile + existing categories

Append user message to session JSON immediately.

If no categories exist: respond that no documents are uploaded yet (Hungarian).

Run LangGraph pipeline:
Node 1: category_decide (LLM router)

Input: user question + list of available categories

Output STRICT JSON: {"category": "<one of available categories>" | null, "reason": "..."}

Must choose ONLY from the provided category list; if none matches, return null.
Conditional:

If category is null → finalize with “no such category” message.

Else → Node 2 retrieve_node:

embed question

query category collection top_k=5

dedupe near-duplicate chunks

Node 3 generate_node:

Chat Completions with strict system prompt:

Only answer using provided context chunks

If not present, say you cannot find it

Provide citations [chunk:<id>] and quote short snippet(s)

Persist tool/system messages and assistant answer to session JSON.
Response: {
final_answer: string,
tools_used: [{name, description}],
memory_snapshot: { routed_category?: string|null, available_categories: string[] },
rag_debug?: { retrieved: [{chunk_id, distance, snippet, metadata}] }
}

POST /api/files/upload
multipart/form-data:

file: UploadFile

user_id: string

category: string

Optional per-document parameters:

chunk_size_tokens: int

overlap_tokens: int

embedding_batch_size: int

show_progress: bool
Behavior:

Normalize category (trim; keep original display name in metadata; also create slug for paths/collection names).

Ensure category exists in profile.categories (add if new).

Save upload under data/uploads/{user_id}/{category}/{upload_id}__{filename}

Extract text (Markdown implemented; PDF/DOCX stub)

Chunk with tiktoken using params/defaults

Create embeddings in batches

Chroma persistent client at data/chroma_db

Create/load category collection cat_{user_id}_{slug(category)}

Add chunks (ids should be stable and unique, e.g. f"{upload_id}:{chunk_index}")

Save chunks.json under data/derived/{user_id}/{category}/{upload_id}/chunks.json
Return: { upload_id, filename, category, size, created_at, params }

GET /api/categories?user_id=...
Return profile categories list.

GET /api/files?user_id=...
Return list of uploaded documents with:

upload_id, filename, category, created_at, params

DELETE /api/files/{upload_id}?user_id=...&category=...
Delete:

upload file

derived folder

vectors in category collection for that upload_id (delete by chunk ids)
If category becomes empty, keep it (do not auto-delete category unless explicitly requested; simplest: keep category list).

GET /api/session/{session_id}
Return session messages.

GET /api/profile/{user_id}
Return stored profile JSON.

PUT /api/profile/{user_id}
Partial update; must not allow deletion.

GET /api/history/search?q=...
Search across all session JSON files for q; return hits.

Frontend (React + TypeScript, Vite)
Hungarian UI everywhere.

Top-left / left panel: Upload section

Category dropdown (existing categories from /api/categories)

Option to create new category (input)

File picker + Upload

List of uploaded docs with category label

Trash icon to delete doc

Center: ChatGPT-like chat.

Bottom: input + send.

Reset context button.

Optional debug: show routed category + retrieved chunks.

Dockerization

docker-compose with:

backend (8000)

frontend (3000)

Mount ./data:/app/data (backend).

CORS configured.

SOLID-ish clean architecture (backend)

domain interfaces:

EmbeddingService

VectorStore

Chunker

DocumentTextExtractor

CategoryRouter (LLM-based)

RAGAnswerer

application services:

UploadService (extract→chunk→embed→index)

ChatService (LangGraph orchestration)

infrastructure:

OpenAIEmbeddingService

ChromaVectorStore

TiktokenChunker

MarkdownExtractor (+ stubs for PDF/DOCX)

OpenAICategoryRouter (Chat Completions → strict JSON)

repositories:

UserProfileRepository (JSON file)

SessionRepository (JSON file)

UploadRepository (filesystem)

Atomic JSON writes (temp + rename) and robust error handling.

Documentation
README must explain:

Categories and LLM routing

Upload and indexing process

LangGraph nodes: category_decide → retrieve → generate

Persistence layout

Reset semantics

How to run locally and with Docker

Now generate the full working project: backend + frontend + Dockerfiles + docker-compose + README.