# ---------------- GasExportClient ----------------

import httpx
from domain.interfaces import IGasExportClient
from typing import Dict, Any

class GasExportClient(IGasExportClient):
    """
    Gas Exported Quantity client for Transparency.host API.
    Fetches exported gas quantity (kWh) for a given point and date range.
    """
    BASE_URL = "https://transparency.entsog.eu/api/v1"

    async def get_exported_quantity(self, point_label: str, date_from: str, date_to: str) -> Dict[str, Any]:
        try:
            # 1. Get pointKey for the given pointLabel
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(f"{self.BASE_URL}/connectionPoints", params={"extended": 1})
                resp.raise_for_status()
                points = resp.json().get("connectionPoints", [])
                point = next((p for p in points if p.get("label") == point_label), None)
                if not point:
                    return {"success": False, "error": f"No connection point found for label: {point_label}"}
                point_key = point.get("key")
                if not point_key:
                    return {"success": False, "error": f"No pointKey found for label: {point_label}"}

            # 2. Query operationaldatas for the given period and pointKey
            params = {
                "periodFrom": date_from,
                "periodTo": date_to,
                "indicator": "Physical Flow",
                "pointKey": point_key,
                "periodType": "day",
                "directionKey": "exit"
            }
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(f"{self.BASE_URL}/operationaldatas", params=params)
                resp.raise_for_status()
                data = resp.json().get("operationalData", [])
                # Handle if operationalData is a dict (single record)
                if isinstance(data, dict):
                    data = [data]
                elif not isinstance(data, list):
                    logger.error(f"Unexpected operationalData type: {type(data)} - value: {data}")
                    return {"success": False, "error": f"Unexpected operationalData type: {type(data)}"}

            # If only one record, return its fields directly in results
            results = []
            for d in data:
                # Use all relevant fields from the dict
                result = {
                    "date": d.get("gasDay") or d.get("periodFrom") or d.get("periodTo"),
                    "value": d.get("value"),
                    "indicator": d.get("indicator"),
                    "periodType": d.get("periodType"),
                    "unit": d.get("unit"),
                    "operatorLabel": d.get("operatorLabel"),
                    "flowStatus": d.get("flowStatus"),
                    "directionKey": d.get("directionKey"),
                    "pointLabel": d.get("pointLabel"),
                    "pointKey": d.get("pointKey")
                }
                results.append(result)
            try:
                results.sort(key=lambda x: x["date"])
            except Exception:
                pass
            total = sum(float(r["value"]) for r in results if r["value"] is not None)
            return {
                "success": True,
                "results": results,
                "total": total,
                "point_label": point_label,
                "point_key": point_key,
                "period_from": date_from,
                "period_to": date_to,
                "system_message": f"Returned {len(results)} value(s), total: {total:,.0f} kWh from {date_from} to {date_to} according to Transparency.host."
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"GasExportClient HTTP error: {e}")
            return {"success": False, "error": f"Gas export query failed: {e}"}
        except Exception as e:
            logger.error(f"GasExportClient error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def execute(self, **kwargs) -> Dict[str, Any]:
        point_label = kwargs.get("pointLabel") or kwargs.get("point_label")
        date_from = kwargs.get("from") or kwargs.get("periodFrom") or kwargs.get("date_from")
        date_to = kwargs.get("to") or kwargs.get("periodTo") or kwargs.get("date_to")
        if not point_label or not date_from or not date_to:
            return {"success": False, "error": "Missing required parameters: pointLabel, from, to"}
        return await self.get_exported_quantity(point_label, date_from, date_to)
"""
Infrastructure layer - External API client implementations.
Following SOLID: Single Responsibility - each client handles one external service.
Open/Closed Principle - easy to add new tool clients without modifying existing ones.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)



# ---------------- RegulationRAGClient (standalone) ----------------
class RegulationRAGClient:
    """
    Regulation RAG (Retrieval-Augmented Generation) client using LangChain and FAISS.

    This client:
    - Loads and processes PDF documents
    - Creates embeddings using OpenAI embeddings
    - Stores vectors in FAISS for efficient retrieval
    - Uses OpenAI for generating answers based on retrieved context
    """

    def __init__(
        self,
        pdf_path: str,
        openai_api_key: str,
        persist_directory: str = "data/regulation_vectordb",
        chunk_size: int = 100000,
        chunk_overlap: int = 200
    ):
        self.pdf_path = Path(pdf_path)
        self.openai_api_key = openai_api_key
        self.persist_directory = Path(persist_directory)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._vectorstore = None
        self._regulation_info = None
        self._initialized = False

    def _initialize(self):
        """Initialize the RAG pipeline (lazy loading)."""
        if self._initialized:
            return
        logger.info(f"Initializing Regulation RAG pipeline for: {self.pdf_path}")
        try:
            from langchain_community.document_loaders import PyPDFLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain_openai import OpenAIEmbeddings
            from langchain_community.vectorstores import FAISS
            # Create embeddings using OpenAI
            embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            # Check if vectorstore already exists
            faiss_index_path = self.persist_directory / "index.faiss"
            if faiss_index_path.exists():
                logger.info("Loading existing FAISS vector store...")
                self._vectorstore = FAISS.load_local(
                    str(self.persist_directory),
                    embeddings
                )
                self._regulation_info = {
                    "title": self.pdf_path.stem,
                    "path": str(self.pdf_path),
                    "chunks_count": len(self._vectorstore.docstore._dict),
                    "status": "loaded_from_cache"
                }
                logger.info(f"Loaded FAISS vector store")
            else:
                # Load and process PDF
                logger.info(f"Loading PDF: {self.pdf_path}")
                loader = PyPDFLoader(str(self.pdf_path))
                documents = loader.load()
                logger.info(f"Loaded {len(documents)} pages from PDF")
                # Split into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    length_function=len,
                    separators=["\n\n\n"]
                )
                chunks = text_splitter.split_documents(documents)
                # Limit total tokens in all chunks to 300000
                try:
                    import tiktoken
                    enc = tiktoken.get_encoding("cl100k_base")
                    def count_tokens(text):
                        return len(enc.encode(text))
                except ImportError:
                    def count_tokens(text):
                        return len(text)
                total_tokens = 0
                limited_chunks = []
                for chunk in chunks:
                    chunk_text = chunk.page_content if hasattr(chunk, 'page_content') else str(chunk)
                    chunk_tokens = count_tokens(chunk_text)
                    if total_tokens + chunk_tokens > 300000:
                        break
                    limited_chunks.append(chunk)
                    total_tokens += chunk_tokens
                chunks = limited_chunks
                logger.info(f"Token-limited to {total_tokens} tokens in {len(chunks)} chunks")
                # Create persist directory
                self.persist_directory.mkdir(parents=True, exist_ok=True)
                # Create FAISS vector store
                self._vectorstore = FAISS.from_documents(
                    documents=chunks,
                    embedding=embeddings
                )
                # Save to disk
                self._vectorstore.save_local(str(self.persist_directory))
                self._regulation_info = {
                    "title": self.pdf_path.stem,
                    "path": str(self.pdf_path),
                    "pages_count": len(documents),
                    "chunks_count": len(chunks),
                    "status": "newly_indexed"
                }
                logger.info(f"Created FAISS vector store with {len(chunks)} chunks")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Regulation RAG pipeline: {e}", exc_info=True)
            raise

    async def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Query the regulation content using RAG pipeline.

        Args:
            question: The question to answer based on regulation content
            top_k: Number of relevant chunks to retrieve

        Returns:
            Dict with answer, sources, and metadata
        """
        try:
            self._initialize()
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            from langchain_core.runnables import RunnablePassthrough
            logger.info(f"Querying regulation with: {question[:100]}...")
            # Retrieve relevant chunks
            retriever = self._vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": top_k}
            )
            # Get relevant documents
            docs = retriever.invoke(question)
            # Build context from retrieved documents
            context = "\n\n".join([doc.page_content for doc in docs])
            # Create prompt
            prompt = ChatPromptTemplate.from_template(
                """Use the following pieces of context from the regulation to answer the question. 
If you don't know the answer based on the context, say so - don't make up information.
Always try to provide specific details from the text when possible.

Context from the regulation:
{context}

Question: {question}

Answer (provide a detailed response based on the regulation content):"""
            )
            # Create LLM
            llm = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.3,
                openai_api_key=self.openai_api_key
            )
            # Create chain
            chain = prompt | llm | StrOutputParser()
            # Run query
            answer = chain.invoke({"context": context, "question": question})
            # Extract source information
            sources = []
            for doc in docs:
                sources.append({
                    "page": doc.metadata.get("page", "unknown"),
                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
            logger.info(f"Query completed, found {len(sources)} relevant sources")
            return {
                "answer": answer,
                "sources": sources,
                "question": question,
                "regulation_title": self._regulation_info.get("title", "Unknown")
            }
        except Exception as e:
            logger.error(f"Regulation query error: {e}", exc_info=True)
            return {"error": str(e)}

    async def get_regulation_info(self) -> Dict[str, Any]:
        """Get information about the loaded regulation."""
        try:
            self._initialize()
            return self._regulation_info
        except Exception as e:
            logger.error(f"Get regulation info error: {e}")
            return {"error": str(e)}

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute regulation RAG operations."""
        action = kwargs.get("action", "query")
        if action == "query":
            question = kwargs.get("question", "")
            if not question:
                return {"error": "Question is required for query action"}
            top_k = kwargs.get("top_k", 5)
            return await self.query(question, top_k)
        elif action == "info":
            return await self.get_regulation_info()
        else:
            return {"error": f"Unknown action: {action}. Supported: query, info"}
