"""
Document Processing Workflow (LangGraph)

Full automated pipeline: upload → extract → chunk → embed → Qdrant

WHY LangGraph:
- Eliminates manual 3-step process (upload → chunk → embed)
- Error handling at each step with state tracking
- Automatic retry logic
- Clear visibility into processing stages
- Easier debugging (state inspection)

Workflow:
START → validate_file → extract_content → store_document 
      → chunk_document → generate_embeddings → upsert_to_qdrant 
      → verify_completion → END
"""

import logging
from typing import TypedDict, List, Optional, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from io import BytesIO

from services.document_service import DocumentService
from services.chunking_service import ChunkingService
from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from database.document_chunk_repository import DocumentChunkRepository

logger = logging.getLogger(__name__)


# ===== STATE DEFINITION =====

class DocumentProcessingState(TypedDict, total=False):
    """State for document processing workflow."""
    # Input (required)
    filename: str
    content_bytes: bytes
    file_type: str  # .pdf, .txt, .md
    tenant_id: int
    user_id: int
    visibility: Literal["private", "tenant"]
    
    # Intermediate
    extracted_text: Optional[str]
    document_id: Optional[int]
    chunk_ids: List[int]
    embedding_count: int
    qdrant_point_ids: List[str]
    
    # Temporary (workflow internal)
    _embedded_chunks: List[Dict[str, Any]]
    _original_chunks: List[Dict[str, Any]]
    
    # Output
    status: str  # "success" | "failed"
    error: Optional[str]
    processing_summary: Dict[str, Any]


# ===== WORKFLOW CLASS =====

class DocumentProcessingWorkflow:
    """
    LangGraph-based document processing workflow.
    
    Automates entire document upload pipeline:
    1. File validation
    2. Content extraction (PDF/TXT/MD)
    3. Database storage
    4. Text chunking
    5. Embedding generation
    6. Qdrant upload
    7. Verification
    
    Benefits over manual process:
    - Single API call instead of 3 separate calls
    - Automatic error recovery
    - State tracking for debugging
    - Consistent processing pipeline
    """
    
    def __init__(self):
        self.doc_service = DocumentService()
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()
        self.qdrant_service = QdrantService()
        self.chunk_repo = DocumentChunkRepository()
        
        self.graph = self._build_graph()
        logger.info("DocumentProcessingWorkflow initialized")
    
    def _build_graph(self) -> Any:
        """Build the LangGraph workflow."""
        workflow = StateGraph(DocumentProcessingState)
        
        # Add nodes
        workflow.add_node("validate_file", self._validate_file_node)
        workflow.add_node("extract_content", self._extract_content_node)
        workflow.add_node("store_document", self._store_document_node)
        workflow.add_node("chunk_document", self._chunk_document_node)
        workflow.add_node("generate_embeddings", self._generate_embeddings_node)
        workflow.add_node("upsert_to_qdrant", self._upsert_qdrant_node)
        workflow.add_node("verify_completion", self._verify_completion_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Define edges (sequential pipeline)
        workflow.set_entry_point("validate_file")
        
        # Main success path
        workflow.add_conditional_edges(
            "validate_file",
            self._check_validation,
            {
                "continue": "extract_content",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "extract_content",
            self._check_extraction,
            {
                "continue": "store_document",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "store_document",
            self._check_storage,
            {
                "continue": "chunk_document",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "chunk_document",
            self._check_chunking,
            {
                "continue": "generate_embeddings",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_embeddings",
            self._check_embeddings,
            {
                "continue": "upsert_to_qdrant",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "upsert_to_qdrant",
            self._check_qdrant,
            {
                "continue": "verify_completion",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("verify_completion", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    # ===== NODE IMPLEMENTATIONS =====
    
    def _validate_file_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """
        Node 1: Validate file parameters.
        
        Checks:
        - filename not empty
        - content_bytes not empty
        - file_type in allowed list
        - file size within limits
        """
        logger.info(f"[NODE: validate_file] Validating {state['filename']}")
        
        try:
            # Check filename
            if not state.get("filename") or not state["filename"].strip():
                return {"error": "Filename is empty", "status": "failed"}
            
            # Check content
            if not state.get("content_bytes") or len(state["content_bytes"]) == 0:
                return {"error": "File content is empty", "status": "failed"}
            
            # Check file type
            allowed_types = {".pdf", ".txt", ".md"}
            if state["file_type"] not in allowed_types:
                return {"error": f"Invalid file type: {state['file_type']}", "status": "failed"}
            
            # Check file size (10MB max)
            max_size = 10 * 1024 * 1024
            if len(state["content_bytes"]) > max_size:
                return {"error": f"File too large: {len(state['content_bytes'])} bytes (max: {max_size})", "status": "failed"}
            
            logger.info(f"[NODE: validate_file] ✅ Validation passed")
            return {}  # No changes, validation passed
            
        except Exception as e:
            logger.error(f"[NODE: validate_file] ❌ Error: {e}", exc_info=True)
            return {"error": f"Validation error: {str(e)}", "status": "failed"}
    
    def _extract_content_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """
        Node 2: Extract text content from file bytes.
        
        Supports:
        - PDF (PyPDF2)
        - TXT (UTF-8 detection)
        - MD (UTF-8)
        """
        logger.info(f"[NODE: extract_content] Extracting from {state['file_type']}")
        
        try:
            extracted = self.doc_service._extract_content(
                state["content_bytes"],
                state["file_type"]
            )
            
            if not extracted or not extracted.strip():
                return {"error": "Extracted content is empty", "status": "failed"}
            
            logger.info(f"[NODE: extract_content] ✅ Extracted {len(extracted)} chars")
            return {"extracted_text": extracted}
            
        except Exception as e:
            logger.error(f"[NODE: extract_content] ❌ Error: {e}", exc_info=True)
            return {"error": f"Content extraction failed: {str(e)}", "status": "failed"}
    
    def _store_document_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """
        Node 3: Store document in PostgreSQL documents table.
        """
        logger.info(f"[NODE: store_document] Storing {state['filename']}")
        
        try:
            doc_id = self.doc_service.repository.insert_document(
                tenant_id=state["tenant_id"],
                user_id=state["user_id"],
                visibility=state["visibility"],
                source="upload",
                title=state["filename"],
                content=state["extracted_text"]
            )
            
            logger.info(f"[NODE: store_document] ✅ Document stored: id={doc_id}")
            return {"document_id": doc_id}
            
        except Exception as e:
            logger.error(f"[NODE: store_document] ❌ Error: {e}", exc_info=True)
            return {"error": f"Database storage failed: {str(e)}", "status": "failed"}
    
    def _chunk_document_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """
        Node 4: Split document into chunks using LangChain splitter.
        """
        logger.info(f"[NODE: chunk_document] Chunking document_id={state['document_id']}")
        
        try:
            chunk_ids = self.chunking_service.chunk_document(
                document_id=state["document_id"],
                tenant_id=state["tenant_id"],
                content=state["extracted_text"],
                source_title=state["filename"]
            )
            
            logger.info(f"[NODE: chunk_document] ✅ Created {len(chunk_ids)} chunks")
            return {"chunk_ids": chunk_ids}
            
        except Exception as e:
            logger.error(f"[NODE: chunk_document] ❌ Error: {e}", exc_info=True)
            return {"error": f"Chunking failed: {str(e)}", "status": "failed"}
    
    def _generate_embeddings_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """
        Node 5: Generate embeddings for all chunks.
        """
        logger.info(f"[NODE: generate_embeddings] Processing {len(state['chunk_ids'])} chunks")
        
        try:
            # Fetch chunks
            chunks = self.chunk_repo.get_chunks_not_embedded(
                document_id=state["document_id"]
            )
            
            if not chunks:
                state["error"] = "No chunks found to embed"
                state["status"] = "failed"
                return state
            
            # Generate embeddings
            embedded_chunks = self.embedding_service.generate_embeddings_for_chunks(chunks)
            
            logger.info(f"[NODE: generate_embeddings] ✅ Generated {len(embedded_chunks)} embeddings")
            
            # Store for next node
            return {
                "embedding_count": len(embedded_chunks),
                "_embedded_chunks": embedded_chunks,
                "_original_chunks": chunks
            }
            
        except Exception as e:
            logger.error(f"[NODE: generate_embeddings] ❌ Error: {e}", exc_info=True)
            return {"error": f"Embedding generation failed: {str(e)}", "status": "failed"}
    
    def _upsert_qdrant_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """
        Node 6: Upload embeddings to Qdrant with batching.
        """
        logger.info(f"[NODE: upsert_to_qdrant] Uploading {state['embedding_count']} vectors")
        
        try:
            embedded_chunks = state.get("_embedded_chunks", [])
            original_chunks = state.get("_original_chunks", [])
            
            # Prepare Qdrant data
            qdrant_data = []
            for embedded_chunk in embedded_chunks:
                original = next(
                    (c for c in original_chunks if c["id"] == embedded_chunk["chunk_id"]),
                    None
                )
                
                if original:
                    qdrant_data.append({
                        "chunk_id": embedded_chunk["chunk_id"],
                        "embedding": embedded_chunk["embedding"],
                        "tenant_id": original["tenant_id"],
                        "document_id": original["document_id"],
                        "user_id": state.get("user_id"),  # Document owner
                        "visibility": state.get("visibility", "tenant"),  # Access control
                        "content": original["content"]
                    })
            
            # Upsert to Qdrant (with automatic batching to avoid payload size limits)
            qdrant_results = self.qdrant_service.upsert_document_chunks(
                qdrant_data,
                batch_size=self.qdrant_service.upload_batch_size
            )
            
            # Update PostgreSQL with point IDs
            self.chunk_repo.update_chunks_embedding_batch(qdrant_results)
            
            logger.info(f"[NODE: upsert_to_qdrant] ✅ Uploaded {len(qdrant_results)} vectors")
            return {"qdrant_point_ids": [r["qdrant_point_id"] for r in qdrant_results]}
            
        except Exception as e:
            logger.error(f"[NODE: upsert_to_qdrant] ❌ Error: {e}", exc_info=True)
            return {"error": f"Qdrant upload failed: {str(e)}", "status": "failed"}
    
    def _verify_completion_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """
        Node 7: Verify all steps completed successfully.
        """
        logger.info(f"[NODE: verify_completion] Verifying document_id={state['document_id']}")
        
        try:
            processing_summary = {
                "document_id": state["document_id"],
                "filename": state["filename"],
                "content_length": len(state["extracted_text"]),
                "chunk_count": len(state["chunk_ids"]),
                "embedding_count": state["embedding_count"],
                "qdrant_vectors": len(state["qdrant_point_ids"])
            }
            
            logger.info(f"[NODE: verify_completion] ✅ Processing complete")
            return {"status": "success", "processing_summary": processing_summary}
            
        except Exception as e:
            logger.error(f"[NODE: verify_completion] ❌ Error: {e}", exc_info=True)
            return {"error": f"Verification failed: {str(e)}", "status": "failed"}
    
    def _handle_error_node(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """
        Error handler node.
        """
        logger.error(f"[NODE: handle_error] Pipeline failed: {state.get('error', 'Unknown error')}")
        
        processing_summary = {
            "error": state.get("error", "Unknown error"),
            "document_id": state.get("document_id"),
            "filename": state.get("filename"),
            "completed_steps": []
        }
        
        # Track which steps completed
        if state.get("extracted_text"):
            processing_summary["completed_steps"].append("extraction")
        if state.get("document_id"):
            processing_summary["completed_steps"].append("storage")
        if state.get("chunk_ids"):
            processing_summary["completed_steps"].append("chunking")
        if state.get("embedding_count"):
            processing_summary["completed_steps"].append("embedding")
        
        return {"status": "failed", "processing_summary": processing_summary}
    
    # ===== ROUTING FUNCTIONS =====
    
    def _check_validation(self, state: DocumentProcessingState) -> str:
        """Check if validation passed."""
        if state.get("error"):
            return "error"
        return "continue"
    
    def _check_extraction(self, state: DocumentProcessingState) -> str:
        """Check if content extraction succeeded."""
        if state.get("error") or not state.get("extracted_text"):
            return "error"
        return "continue"
    
    def _check_storage(self, state: DocumentProcessingState) -> str:
        """Check if document storage succeeded."""
        if state.get("error") or not state.get("document_id"):
            return "error"
        return "continue"
    
    def _check_chunking(self, state: DocumentProcessingState) -> str:
        """Check if chunking succeeded."""
        if state.get("error") or not state.get("chunk_ids"):
            return "error"
        return "continue"
    
    def _check_embeddings(self, state: DocumentProcessingState) -> str:
        """Check if embedding generation succeeded."""
        if state.get("error") or state.get("embedding_count", 0) == 0:
            return "error"
        return "continue"
    
    def _check_qdrant(self, state: DocumentProcessingState) -> str:
        """Check if Qdrant upload succeeded."""
        if state.get("error") or not state.get("qdrant_point_ids"):
            return "error"
        return "continue"
    
    # ===== EXECUTION =====
    
    async def process_document(
        self,
        filename: str,
        content: bytes,
        file_type: str,
        tenant_id: int,
        user_id: int,
        visibility: Literal["private", "tenant"]
    ) -> Dict[str, Any]:
        """
        Execute the full document processing workflow.
        
        Args:
            filename: Original filename
            content: File bytes
            file_type: .pdf, .txt, .md
            tenant_id: Tenant ID
            user_id: User ID
            visibility: Document visibility level
        
        Returns:
            {
                "status": "success" | "failed",
                "document_id": int,
                "summary": {...}
            }
        
        Raises:
            Exception: If workflow execution fails
        """
        initial_state = DocumentProcessingState(
            filename=filename,
            content_bytes=content,
            file_type=file_type,
            tenant_id=tenant_id,
            user_id=user_id,
            visibility=visibility,
            extracted_text=None,
            document_id=None,
            chunk_ids=[],
            embedding_count=0,
            qdrant_point_ids=[],
            status="processing",
            error=None,
            processing_summary={}
        )
        
        logger.info(f"[WORKFLOW] Starting document processing: {filename}")
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            logger.info(f"[WORKFLOW] Processing complete: status={final_state['status']}")
            
            return {
                "status": final_state["status"],
                "document_id": final_state.get("document_id"),
                "error": final_state.get("error"),
                "summary": final_state.get("processing_summary", {})
            }
            
        except Exception as e:
            logger.error(f"[WORKFLOW] Fatal error: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": f"Workflow execution failed: {str(e)}",
                "summary": {}
            }
