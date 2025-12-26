import os
import time
from typing import List, Dict, Any, Type, Optional
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, Range
import uuid

from domain.interfaces import ILLMClient, IVectorDBClient

class GeminiClient(ILLMClient):
    def __init__(self, model_name: str = "gemini-3-flash-preview", temperature: float = 0):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("ERROR: GOOGLE_API_KEY not found in environment")
        else:
            print(f"DEBUG: Initializing GeminiClient with key length {len(api_key)}")
        
        # Override model if set in env
        env_model = os.getenv("LLM_MODEL")
        if env_model:
            model_name = env_model
            print(f"DEBUG: Using model: {model_name}")
        else:
            print(f"DEBUG: Using default model: {model_name}")

        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=api_key)

    async def generate(self, prompt: str) -> str:
        response = await self.llm.ainvoke(prompt)
        return response.content

    async def generate_structured(self, prompt: str, response_model: Type[Any]) -> Any:
        try:
            structured_llm = self.llm.with_structured_output(response_model)
            return await structured_llm.ainvoke(prompt)
        except Exception as e:
            print(f"ERROR in Gemini generate_structured: {e}")
            raise e

class QdrantVectorDB(IVectorDBClient):
    def __init__(self, path: str = "./qdrant_db", collection_name: str = "medical_kb"):
        qdrant_url = os.getenv("QDRANT_URL")
        # Production ready: Support both local and URL-based instance
        if qdrant_url:
            print(f"DEBUG: Connecting to Qdrant at {qdrant_url}")
            self.client = QdrantClient(url=qdrant_url)
        else:
            print(f"DEBUG: Using local Qdrant at {path}")
            self.client = QdrantClient(path=path)
        
        self.collection_name = collection_name
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
             print("ERROR: GOOGLE_API_KEY for Embeddings not found")
        
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        # Ensure collection exists
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            print(f"DEBUG: Creating collection {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

    async def search(self, query: str, limit: int = 3, tenant_id: str = None) -> List[Dict[str, Any]]:
        try:
            print(f"DEBUG: Embedding query: {query}")
            query_vector = self.embeddings.embed_query(query)
            
            # Build filters
            must_filters = []
            
            # 1. Tenant ID Filter (ACL/ABAC)
            if tenant_id:
                must_filters.append(
                    FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))
                )
                
            # 2. Validity Filter (Time-based validity)
            current_time = time.time()
            # Valid if: (valid_from IS NULL OR valid_from <= now) AND (valid_until IS NULL OR valid_until >= now)
            # Simplification: We ensure valid_from/until are always set or handle defaults.
            # Using Range filters.
            
            # Actually, to simulate "valid documents only", we check if `valid_until` > now.
            # Assuming payload stores timestamps.
            must_filters.append(
                FieldCondition(key="valid_until", range=Range(gte=current_time))
            )
            
            query_filter = Filter(must=must_filters) if must_filters else None

            print(f"DEBUG: Performing search with filter: {query_filter}")
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=limit
            )
            hits = results.points
            
            return [{"text": hit.payload.get("text", ""), "source": hit.payload.get("source", ""), "score": hit.score} for hit in hits]
        except Exception as e:
            print(f"ERROR in search: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def upsert(self, text: str, metadata: Dict[str, Any]):
        """
        Upsert a single chunk of text.
        Metadata should include:
        - tenant_id: str
        - valid_from: float (timestamp)
        - valid_until: float (timestamp)
        - source: str
        """
        # Ensure default metadata
        meta = metadata.copy()
        if "id" not in meta:
            meta["id"] = str(uuid.uuid4())
        
        # Embed
        vector = self.embeddings.embed_query(text)
        
        point = PointStruct(
            id=meta["id"],
            vector=vector,
            payload={"text": text, **meta}
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    async def ingest_document(self, file_path: str, tenant_id: str = "default", valid_days: int = 365):
        """
        Ingests a document (PDF or Text), chunks it, and indexes it.
        """
        print(f"DEBUG: Ingesting file: {file_path}")
        text_content = ""
        
        if file_path.lower().endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text_content += page.extract_text() + "\n"
            except ImportError:
                print("ERROR: pypdf not installed. Cannot process PDF.")
                return 0
            except Exception as e:
                print(f"ERROR reading PDF {file_path}: {e}")
                return 0
        else:
            # Assume text
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
            except Exception as e:
                print(f"ERROR reading file {file_path}: {e}")
                return 0

        # Chunking
        chunks = self.text_splitter.split_text(text_content)
        print(f"DEBUG: Created {len(chunks)} chunks from {file_path}")
        
        current_time = time.time()
        valid_until = current_time + (valid_days * 24 * 3600)
        
        source_name = os.path.basename(file_path)
        
        count = 0
        for i, chunk in enumerate(chunks):
            meta = {
                "source": source_name,
                "chunk_index": i,
                "tenant_id": tenant_id,
                "valid_from": current_time,
                "valid_until": valid_until,
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{source_name}_{i}_{tenant_id}")) # Deterministic ID
            }
            await self.upsert(chunk, meta)
            count += 1
            
        return count
