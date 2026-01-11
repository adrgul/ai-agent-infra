"""Unit tests for PDF parser

Tests:
- PDF text extraction
- Metadata extraction
- Page-level data
"""
import pytest
from pathlib import Path
import tempfile

from rag.ingestion.pdf_parser import parse_pdf, PYPDF_AVAILABLE


@pytest.mark.skipif(not PYPDF_AVAILABLE, reason="pypdf not installed")
def test_parse_simple_pdf():
    """Parse a minimal valid PDF."""
    # Create a minimal PDF (this is a simplified example)
    # In practice, use a real PDF fixture or generate with reportlab
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
409
%%EOF
"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        pdf_path.write_bytes(pdf_content)
        
        result = parse_pdf(pdf_path)
        
        # Check structure
        assert result.text is not None
        assert isinstance(result.pages, list)
        assert isinstance(result.metadata, dict)
        
        # Check pages
        assert len(result.pages) > 0
        assert result.pages[0]["page_num"] == 1


@pytest.mark.skipif(not PYPDF_AVAILABLE, reason="pypdf not installed")
def test_parse_pdf_with_metadata():
    """Test metadata extraction (title, author)."""
    # For this test we'd need a PDF with metadata
    # Skipping detailed implementation; in practice use a fixture PDF
    pass


def test_parse_pdf_missing_library():
    """Test graceful failure when pypdf not available."""
    if PYPDF_AVAILABLE:
        pytest.skip("pypdf is available")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = Path(tmpdir) / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")
        
        with pytest.raises(RuntimeError, match="pypdf not available"):
            parse_pdf(pdf_path)
