"""
Tests for document parsers
"""

import pytest
from pathlib import Path

from meetingai.parsers import TextParser, MarkdownParser, SRTParser


@pytest.fixture
def text_parser():
    return TextParser()


@pytest.fixture
def markdown_parser():
    return MarkdownParser()


@pytest.fixture
def srt_parser():
    return SRTParser()


def test_text_parser_can_parse(text_parser):
    """Test text parser file type detection"""
    assert text_parser.can_parse("document.txt")
    assert not text_parser.can_parse("document.md")
    assert not text_parser.can_parse("document.docx")


def test_markdown_parser_can_parse(markdown_parser):
    """Test markdown parser file type detection"""
    assert markdown_parser.can_parse("document.md")
    assert markdown_parser.can_parse("document.markdown")
    assert not markdown_parser.can_parse("document.txt")


def test_srt_parser_can_parse(srt_parser):
    """Test SRT parser file type detection"""
    assert srt_parser.can_parse("subtitles.srt")
    assert not srt_parser.can_parse("document.txt")


def test_text_parser_parse(sample_text_file, text_parser):
    """Test text parser document parsing"""
    document = text_parser.parse(sample_text_file)

    assert document.page_content is not None
    assert len(document.page_content) > 0
    assert "Meeting:" in document.page_content
    assert document.metadata["parser"] == "TextParser"
    assert document.metadata["content_type"] == "text/plain"


def test_markdown_parser_parse(temp_dir, markdown_parser):
    """Test markdown parser document parsing"""
    # Create sample markdown file
    md_content = """# Meeting Notes

## Attendees
- John
- Peter
- Maria

## Discussion
We discussed the Q4 priorities.

## Action Items
- [ ] UI mockup review - Maria
- [ ] Backend setup - Peter
"""

    md_file = temp_dir / "meeting.md"
    md_file.write_text(md_content)

    document = markdown_parser.parse(str(md_file))

    assert document.page_content is not None
    assert "Meeting Notes" in document.page_content
    assert document.metadata["parser"] == "MarkdownParser"
    assert document.metadata["title"] == "Meeting Notes"
    assert "UI mockup review" in document.page_content


def test_srt_parser_parse(temp_dir, srt_parser):
    """Test SRT parser document parsing"""
    # Create sample SRT file
    srt_content = """1
00:00:01,000 --> 00:00:05,000
John: Welcome to the meeting.

2
00:00:05,000 --> 00:00:10,000
Peter: Let's discuss the priorities.

3
00:00:10,000 --> 00:00:15,000
Maria: I can handle the UI work.
"""

    srt_file = temp_dir / "meeting.srt"
    srt_file.write_text(srt_content)

    document = srt_parser.parse(str(srt_file))

    assert document.page_content is not None
    assert "Welcome to the meeting" in document.page_content
    assert document.metadata["parser"] == "SRTParser"
    assert document.metadata["segment_count"] == 3
    assert document.metadata["total_duration_seconds"] == 15.0


def test_parser_metadata(text_parser, sample_text_file):
    """Test parser metadata extraction"""
    metadata = text_parser.extract_metadata(sample_text_file)

    assert "file_path" in metadata
    assert "file_name" in metadata
    assert "file_size" in metadata
    assert metadata["extension"] == ".txt"
    assert metadata["parser"] == "TextParser"


def test_parser_invalid_file(text_parser):
    """Test parser error handling for invalid files"""
    with pytest.raises(FileNotFoundError):
        text_parser.parse("nonexistent.txt")


def test_parser_clean_text(text_parser):
    """Test text cleaning functionality"""
    dirty_text = "  Text with   extra   spaces  \n\n  and newlines  \t  "
    clean_text = text_parser._clean_text(dirty_text)

    assert clean_text == "Text with extra spaces and newlines"
    assert "  " not in clean_text  # No double spaces
    assert clean_text.strip() == clean_text  # No leading/trailing whitespace