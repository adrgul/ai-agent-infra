"""Document processing service."""

import logging
from typing import Literal
from PyPDF2 import PdfReader
from io import BytesIO
import chardet

from database.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document upload and processing."""
    
    def __init__(self):
        self.repository = DocumentRepository()
    
    async def upload_document(
        self,
        filename: str,
        content: bytes,
        file_type: str,
        tenant_id: int,
        user_id: int,
        visibility: Literal["private", "tenant"]
    ) -> int:
        """
        Process uploaded document and store in database.
        
        Args:
            filename: Original filename
            content: File content as bytes
            file_type: File extension (.pdf, .txt, .md)
            tenant_id: Tenant identifier
            user_id: User identifier
            visibility: Document visibility level
        
        Returns:
            document_id: ID of created document
        
        Raises:
            ValueError: If file content cannot be extracted
        """
        logger.info(f"Processing document: {filename} ({file_type})")
        
        # Extract text content based on file type
        text_content = self._extract_content(content, file_type)
        
        if not text_content or not text_content.strip():
            raise ValueError("Document is empty or could not be read")
        
        # Store in database (sync call)
        document_id = self.repository.insert_document(
            tenant_id=tenant_id,
            user_id=user_id,
            visibility=visibility,
            source="upload",
            title=filename,
            content=text_content
        )
        
        logger.info(f"Document stored: id={document_id}, length={len(text_content)} chars")
        
        return document_id
    
    def _extract_content(self, content: bytes, file_type: str) -> str:
        """
        Extract text content from file bytes.
        
        Args:
            content: File content as bytes
            file_type: File extension
        
        Returns:
            Extracted text content
        
        Raises:
            ValueError: If extraction fails
        """
        try:
            if file_type == ".pdf":
                return self._extract_pdf(content)
            elif file_type in [".txt", ".md"]:
                return self._extract_text(content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Content extraction error ({file_type}): {e}")
            raise ValueError(f"Failed to extract content from {file_type} file")
    
    def _extract_pdf(self, content: bytes) -> str:
        """Extract text from PDF bytes."""
        pdf_file = BytesIO(content)
        reader = PdfReader(pdf_file)
        
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        return "\n".join(text_parts)
    
    def _extract_text(self, content: bytes) -> str:
        """Extract text from TXT/MD bytes using automatic encoding detection."""
        # Use chardet to detect the actual encoding
        detection = chardet.detect(content)
        detected_encoding = detection.get('encoding')
        confidence = detection.get('confidence', 0)
        
        logger.info(f"Detected encoding: {detected_encoding} (confidence: {confidence:.2f})")
        
        # Try detected encoding first if confidence is high enough
        if detected_encoding and confidence > 0.7:
            try:
                decoded = content.decode(detected_encoding)
                logger.info(f"Successfully decoded with {detected_encoding}")
                return decoded
            except (UnicodeDecodeError, LookupError) as e:
                logger.warning(f"Failed to decode with detected encoding {detected_encoding}: {e}")
        
        # Fallback: try common encodings
        encodings = ["utf-8", "cp1250", "cp1252", "latin-1", "iso-8859-2"]
        
        for encoding in encodings:
            try:
                decoded = content.decode(encoding)
                logger.info(f"Successfully decoded with fallback encoding: {encoding}")
                return decoded
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Last resort: utf-8 with error replacement
        logger.warning("All encodings failed, using UTF-8 with error replacement")
        return content.decode("utf-8", errors="replace")
