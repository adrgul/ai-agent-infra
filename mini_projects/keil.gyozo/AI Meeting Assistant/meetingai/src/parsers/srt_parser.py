"""
SRT subtitle file parser
"""

import logging
import re
from pathlib import Path

from langchain.schema import Document

from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class SRTParser(BaseParser):
    """Parser for SRT subtitle files"""

    def __init__(self):
        super().__init__()
        self.supported_extensions = ["srt"]

    def parse(self, file_path: str) -> Document:
        """
        Parse an SRT subtitle file

        Args:
            file_path: Path to the .srt file

        Returns:
            LangChain Document object
        """
        try:
            path = Path(file_path)

            # Read file content
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Parse SRT content
            segments = self._parse_srt(content)

            # Extract text content
            text_segments = [segment['text'] for segment in segments]
            full_text = ' '.join(text_segments)

            # Clean the text
            cleaned_content = self._clean_text(full_text)

            # Extract timing information
            total_duration = self._calculate_duration(segments)

            # Extract metadata
            metadata = self.extract_metadata(file_path)
            metadata.update({
                "parser": "SRTParser",
                "content_type": "text/srt",
                "segment_count": len(segments),
                "total_duration_seconds": total_duration,
                "word_count": len(cleaned_content.split()),
                "segments": segments,  # Include timing information
            })

            logger.info(f"Successfully parsed SRT file: {file_path}")

            return Document(
                page_content=cleaned_content,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to parse SRT file {file_path}: {str(e)}")
            raise RuntimeError(f"SRT parsing failed: {str(e)}")

    def _parse_srt(self, content: str) -> list:
        """
        Parse SRT content into segments

        Args:
            content: SRT file content

        Returns:
            List of segment dictionaries
        """
        segments = []
        blocks = re.split(r'\n\s*\n', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # Extract sequence number
                seq_match = re.match(r'^\d+$', lines[0].strip())
                if seq_match:
                    # Extract timing
                    timing_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                    if timing_match:
                        start_time = timing_match.group(1)
                        end_time = timing_match.group(2)

                        # Extract text (remaining lines)
                        text_lines = lines[2:]
                        text = ' '.join(text_lines).strip()

                        if text:
                            segments.append({
                                'sequence': int(seq_match.group()),
                                'start_time': start_time,
                                'end_time': end_time,
                                'text': text
                            })

        return segments

    def _calculate_duration(self, segments: list) -> float:
        """
        Calculate total duration from segments

        Args:
            segments: List of segments

        Returns:
            Total duration in seconds
        """
        if not segments:
            return 0.0

        def time_to_seconds(time_str: str) -> float:
            """Convert SRT time format to seconds"""
            hours, minutes, seconds = time_str.replace(',', '.').split(':')
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)

        last_segment = segments[-1]
        end_time = time_to_seconds(last_segment['end_time'])

        return end_time