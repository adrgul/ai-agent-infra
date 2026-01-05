"""
Unit tests for Qdrant RAG client deduplication and overlap boost features.
Tests the _deduplicate_citations and _apply_it_overlap_boost functions.
"""
import pytest
from domain.models import Citation
from infrastructure.qdrant_rag_client import _deduplicate_citations, _apply_it_overlap_boost


class TestDeduplicateCitations:
    """Test suite for content deduplication logic."""
    
    def test_deduplicate_removes_exact_duplicates(self):
        """Should keep only highest-scoring citation for exact duplicates."""
        citations = [
            Citation(
                doc_id="doc1#chunk0",
                title="Aurora Digital Arculati Kézikönyv",
                score=0.95,
                content="Elsődleges szín: Éjkék (#0B1C2D)\nMásodlagos szín: Aurora türkiz (#1FA6A3)"
            ),
            Citation(
                doc_id="doc2#chunk0",
                title="Aurora Digital Arculati Kézikönyv",
                score=0.92,
                content="Elsődleges szín: Éjkék (#0B1C2D)\nMásodlagos szín: Aurora türkiz (#1FA6A3)"
            ),
        ]
        
        result = _deduplicate_citations(citations)
        
        assert len(result) == 1
        assert result[0].doc_id == "doc1#chunk0"  # Higher score kept
        assert result[0].score == 0.95
    
    def test_deduplicate_keeps_different_content(self):
        """Should keep citations with different content."""
        citations = [
            Citation(
                doc_id="doc1#chunk0",
                title="Aurora Digital Arculati Kézikönyv",
                score=0.95,
                content="Elsődleges szín: Éjkék (#0B1C2D)"
            ),
            Citation(
                doc_id="doc2#chunk0",
                title="Aurora Digital Arculati Kézikönyv",
                score=0.92,
                content="Tipográfia: Inter font család használata kötelező"
            ),
        ]
        
        result = _deduplicate_citations(citations)
        
        assert len(result) == 2
    
    def test_deduplicate_handles_empty_list(self):
        """Should handle empty citation list."""
        citations = []
        
        result = _deduplicate_citations(citations)
        
        assert len(result) == 0
    
    def test_deduplicate_handles_single_citation(self):
        """Should pass through single citation unchanged."""
        citations = [
            Citation(
                doc_id="doc1#chunk0",
                title="Test Document",
                score=0.95,
                content="Some content here"
            )
        ]
        
        result = _deduplicate_citations(citations)
        
        assert len(result) == 1
        assert result[0] == citations[0]
    
    def test_deduplicate_pdf_docx_formats(self):
        """Should remove PDF/DOCX duplicates of same content."""
        citations = [
            Citation(
                doc_id="doc1.pdf#chunk0",
                title="Aurora_Digital_Arculati_Kezikonyv_HU.pdf",
                score=0.95,
                content="Színpaletta: Elsődleges szín Éjkék, másodlagos Aurora türkiz, kiegészítő világosszürke"
            ),
            Citation(
                doc_id="doc2.docx#chunk0",
                title="Aurora_Digital_Arculati_Kezikonyv_HU.docx",
                score=0.93,
                content="Színpaletta: Elsődleges szín Éjkék, másodlagos Aurora türkiz, kiegészítő világosszürke"
            ),
        ]
        
        result = _deduplicate_citations(citations)
        
        assert len(result) == 1
        assert result[0].score == 0.95  # PDF kept (higher score)
    
    def test_deduplicate_different_titles_same_content(self):
        """Should treat different titles as different even with same content."""
        citations = [
            Citation(
                doc_id="doc1#chunk0",
                title="Document A",
                score=0.95,
                content="Same content here"
            ),
            Citation(
                doc_id="doc2#chunk0",
                title="Document B",
                score=0.93,
                content="Same content here"
            ),
        ]
        
        result = _deduplicate_citations(citations)
        
        # Different titles = different signatures = both kept
        assert len(result) == 2
    
    def test_deduplicate_content_preview_length(self):
        """Should use first 80 chars for signature matching."""
        citations = [
            Citation(
                doc_id="doc1#chunk0",
                title="Test Doc",
                score=0.95,
                content="A" * 80 + "different ending X"
            ),
            Citation(
                doc_id="doc2#chunk0",
                title="Test Doc",
                score=0.93,
                content="A" * 80 + "different ending Y"
            ),
        ]
        
        result = _deduplicate_citations(citations)
        
        # First 80 chars are same → should deduplicate
        assert len(result) == 1
        assert result[0].score == 0.95
    
    def test_deduplicate_preserves_metadata(self):
        """Should preserve all citation metadata fields."""
        citations = [
            Citation(
                doc_id="doc1#chunk0",
                title="IT Policy",
                score=0.95,
                content="VPN troubleshooting steps",
                url="https://confluence.example.com",
                section_id="IT-KB-234"
            ),
        ]
        
        result = _deduplicate_citations(citations)
        
        assert result[0].url == "https://confluence.example.com"
        assert result[0].section_id == "IT-KB-234"
    
    def test_deduplicate_multiple_duplicates(self):
        """Should handle multiple sets of duplicates."""
        citations = [
            # Set 1: 3 duplicates
            Citation(doc_id="d1", title="Doc A", score=0.95, content="Content A"),
            Citation(doc_id="d2", title="Doc A", score=0.90, content="Content A"),
            Citation(doc_id="d3", title="Doc A", score=0.85, content="Content A"),
            # Set 2: 2 duplicates
            Citation(doc_id="d4", title="Doc B", score=0.80, content="Content B"),
            Citation(doc_id="d5", title="Doc B", score=0.75, content="Content B"),
            # Unique
            Citation(doc_id="d6", title="Doc C", score=0.70, content="Content C"),
        ]
        
        result = _deduplicate_citations(citations)
        
        assert len(result) == 3  # One from each set + unique
        assert result[0].doc_id == "d1"  # Highest score from set 1
        assert result[1].doc_id == "d4"  # Highest score from set 2
        assert result[2].doc_id == "d6"  # Unique


class TestApplyITOverlapBoost:
    """Test suite for IT domain lexical overlap boosting."""
    
    def test_overlap_boost_increases_score_on_match(self):
        """Should boost score when query tokens match content."""
        citations = [
            Citation(
                doc_id="doc1",
                title="VPN Troubleshooting",
                score=0.80,
                content="VPN kliens nem fut vagy lefagyott. VPN szolgáltatás megszakadt."
            )
        ]
        
        result = _apply_it_overlap_boost(citations, "VPN nem működik")
        
        # "VPN" token matches → should boost
        assert result[0].score > 0.80
    
    def test_overlap_boost_max_20_percent(self):
        """Should cap boost at 20% maximum."""
        citations = [
            Citation(
                doc_id="doc1",
                title="VPN Guide",
                score=1.0,
                content="VPN VPN VPN VPN VPN VPN"
            )
        ]
        
        result = _apply_it_overlap_boost(citations, "VPN VPN VPN")
        
        # Max boost is 1.2x
        assert result[0].score <= 1.2
    
    def test_overlap_boost_ignores_short_tokens(self):
        """Should ignore tokens shorter than 3 characters."""
        citations = [
            Citation(
                doc_id="doc1",
                title="IT Policy",
                score=0.80,
                content="IT support"
            )
        ]
        
        result = _apply_it_overlap_boost(citations, "IT és VPN")
        
        # "IT" and "és" are < 3 chars → ignored, only "VPN" counts
        # No "VPN" in content → no boost
        assert result[0].score == 0.80
    
    def test_overlap_boost_case_insensitive(self):
        """Should match tokens case-insensitively."""
        citations = [
            Citation(
                doc_id="doc1",
                title="VPN Guide",
                score=0.80,
                content="vpn configuration steps"
            )
        ]
        
        result = _apply_it_overlap_boost(citations, "VPN CONFIG")
        
        # "vpn" matches "VPN", "config" matches "configuration"
        assert result[0].score > 0.80
    
    def test_overlap_boost_handles_hungarian_chars(self):
        """Should handle Hungarian special characters."""
        citations = [
            Citation(
                doc_id="doc1",
                title="Hálózati kapcsolat",
                score=0.80,
                content="Hálózati kapcsolat megszüntetése szükséges vírusvédelem esetén"
            )
        ]
        
        result = _apply_it_overlap_boost(citations, "hálózati vírusvédelem")
        
        # Both tokens match → should boost
        assert result[0].score > 0.80
    
    def test_overlap_boost_reranks_citations(self):
        """Should re-sort citations by boosted score."""
        citations = [
            Citation(
                doc_id="doc1",
                title="Email Setup",
                score=0.90,
                content="Email configuration steps for Outlook"
            ),
            Citation(
                doc_id="doc2",
                title="VPN Setup",
                score=0.85,
                content="VPN client installation and troubleshooting for remote access"
            ),
        ]
        
        result = _apply_it_overlap_boost(citations, "VPN troubleshooting")
        
        # doc2 should jump to first after boost (has matching tokens)
        assert result[0].doc_id == "doc2"
    
    def test_overlap_boost_empty_query(self):
        """Should handle empty query gracefully."""
        citations = [
            Citation(doc_id="doc1", title="Test", score=0.80, content="Content")
        ]
        
        result = _apply_it_overlap_boost(citations, "")
        
        # No tokens → no boost
        assert result[0].score == 0.80
    
    def test_overlap_boost_empty_citations(self):
        """Should handle empty citation list."""
        citations = []
        
        result = _apply_it_overlap_boost(citations, "VPN setup")
        
        assert len(result) == 0
    
    def test_overlap_boost_no_matches(self):
        """Should not boost when no tokens match."""
        citations = [
            Citation(
                doc_id="doc1",
                title="Printer Setup",
                score=0.80,
                content="Printer driver installation guide"
            )
        ]
        
        result = _apply_it_overlap_boost(citations, "VPN network")
        
        # No matches → no boost
        assert result[0].score == 0.80
    
    def test_overlap_boost_partial_match(self):
        """Should boost proportionally to match ratio."""
        citations = [
            Citation(
                doc_id="doc1",
                title="IT Guide",
                score=0.80,
                content="VPN setup and configuration"
            )
        ]
        
        # Query has 3 tokens (>= 3 chars): "VPN", "setup", "printer"
        # Content matches 2 out of 3 → overlap_ratio = 2/3 = 0.6667
        # boost factor = 1 + min(0.2, 0.6667 * 0.4) = 1 + min(0.2, 0.2667) = 1.2 (max boost)
        result = _apply_it_overlap_boost(citations, "VPN setup printer")
        
        # Should apply max boost (20%)
        assert result[0].score > 0.80
        assert result[0].score == 0.96  # 0.80 * 1.2 = 0.96 (max boost reached)
    
    def test_overlap_boost_title_and_content(self):
        """Should match tokens in both title and content."""
        citations = [
            Citation(
                doc_id="doc1",
                title="VPN Troubleshooting Guide",
                score=0.80,
                content="Steps to diagnose network issues"
            )
        ]
        
        result = _apply_it_overlap_boost(citations, "VPN network troubleshooting")
        
        # All 3 tokens match (VPN in title, network in content, troubleshooting in title)
        assert result[0].score > 0.80


class TestDeduplicationAndBoostIntegration:
    """Integration tests for deduplication + overlap boost pipeline."""
    
    def test_deduplicate_then_boost_workflow(self):
        """Should deduplicate first, then apply boost."""
        citations = [
            # Duplicates
            Citation(doc_id="d1.pdf", title="VPN Guide", score=0.90, content="VPN setup steps"),
            Citation(doc_id="d2.docx", title="VPN Guide", score=0.85, content="VPN setup steps"),
            # Unique
            Citation(doc_id="d3", title="Email Guide", score=0.80, content="Email configuration"),
        ]
        
        # Simulate pipeline: deduplicate → boost
        deduped = _deduplicate_citations(citations)
        boosted = _apply_it_overlap_boost(deduped, "VPN setup")
        
        # Should have 2 citations (duplicates removed)
        assert len(boosted) == 2
        # VPN guide should be first (boosted)
        assert boosted[0].title == "VPN Guide"
        assert boosted[0].score > 0.90  # Boosted
