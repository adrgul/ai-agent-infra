#!/usr/bin/env python3
"""
Batch processing script for MeetingAI
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meetingai.workflows.meeting_processor import MeetingProcessor
from meetingai.utils.config import Config
from meetingai.utils.logger import setup_logger

logger = setup_logger()


async def process_batch(input_files: List[str], config: Config) -> None:
    """Process multiple meeting files"""
    processor = MeetingProcessor(config)

    results = []
    for i, input_file in enumerate(input_files, 1):
        try:
            logger.info(f"Processing file {i}/{len(input_files)}: {input_file}")
            result = await processor.process(input_file)
            results.append((input_file, result, None))

        except Exception as e:
            logger.error(f"Failed to process {input_file}: {str(e)}")
            results.append((input_file, None, str(e)))

    # Print summary
    print("\n" + "="*70)
    print("BATCH PROCESSING SUMMARY")
    print("="*70)

    successful = 0
    failed = 0

    for input_file, result, error in results:
        filename = Path(input_file).name
        if error:
            print(f"❌ {filename}: {error}")
            failed += 1
        else:
            print(f"✅ {filename}: {result.summary.meeting_id}")
            successful += 1

    print(f"\nTotal files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(results)*100:.1f}%")


def find_meeting_files(directory: str) -> List[str]:
    """Find all meeting files in directory"""
    path = Path(directory)
    if not path.exists():
        raise ValueError(f"Directory not found: {directory}")

    extensions = ['*.txt', '*.md', '*.docx', '*.srt']
    files = []

    for ext in extensions:
        files.extend(path.glob(ext))

    return [str(f) for f in sorted(files)]


async def main():
    """Main function"""
    try:
        # Load configuration
        config_path = Path("../config.yaml")
        if not config_path.exists():
            logger.error("config.yaml not found. Please copy config.yaml.example to config.yaml")
            return

        config = Config.from_yaml(str(config_path))

        # Get input from command line
        if len(sys.argv) < 2:
            print("Usage:")
            print("  python process_batch.py <input_file1> <input_file2> ...")
            print("  python process_batch.py --dir <directory>")
            return

        input_files = []

        if sys.argv[1] == "--dir":
            if len(sys.argv) < 3:
                print("Error: --dir requires a directory path")
                return
            directory = sys.argv[2]
            input_files = find_meeting_files(directory)
            print(f"Found {len(input_files)} files in {directory}")
        else:
            input_files = sys.argv[1:]

        if not input_files:
            print("No input files found")
            return

        # Validate files exist
        for file_path in input_files:
            if not Path(file_path).exists():
                print(f"Error: File not found: {file_path}")
                return

        # Process batch
        logger.info(f"Starting batch processing of {len(input_files)} files")
        await process_batch(input_files, config)

    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())