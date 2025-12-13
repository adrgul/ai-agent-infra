#!/usr/bin/env python3
"""
Local development runner for MeetingAI
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meetingai.workflows.meeting_processor import MeetingProcessor
from meetingai.utils.config import Config
from meetingai.utils.logger import setup_logger

logger = setup_logger()


async def main():
    """Main function for local testing"""
    try:
        # Load configuration
        config_path = Path("../config.yaml")
        if not config_path.exists():
            logger.error("config.yaml not found. Please copy config.yaml.example to config.yaml")
            return

        config = Config.from_yaml(str(config_path))
        logger.info("Configuration loaded successfully")

        # Initialize processor
        processor = MeetingProcessor(config)
        logger.info("Meeting processor initialized")

        # Get input file from command line
        if len(sys.argv) < 2:
            logger.error("Usage: python run_local.py <input_file>")
            logger.info("Available sample files:")
            sample_dir = Path("../data/sample_meetings")
            if sample_dir.exists():
                for file in sample_dir.glob("*"):
                    logger.info(f"  {file.name}")
            return

        input_file = sys.argv[1]
        if not Path(input_file).exists():
            logger.error(f"Input file not found: {input_file}")
            return

        # Process meeting
        logger.info(f"Processing meeting file: {input_file}")
        result = await processor.process(input_file)

        # Display results
        print("\n" + "="*50)
        print("MEETING PROCESSING RESULTS")
        print("="*50)

        print(f"\nMeeting ID: {result.summary.meeting_id}")
        print(f"Title: {result.summary.title}")
        print(f"Date: {result.summary.date}")
        print(f"Participants: {', '.join(result.summary.participants)}")

        print(f"\nSummary:\n{result.summary.summary}")

        if result.summary.key_decisions:
            print(f"\nKey Decisions:")
            for decision in result.summary.key_decisions:
                print(f"  • {decision}")

        if result.summary.next_steps:
            print(f"\nNext Steps:")
            for step in result.summary.next_steps:
                print(f"  • {step}")

        if result.tasks:
            print(f"\nAction Items ({len(result.tasks)}):")
            for task in result.tasks:
                print(f"  • {task.title} ({task.assignee}) - Due: {task.due_date or 'TBD'} - Priority: {task.priority}")

        print(f"\nOutput files saved in: {config.output.save_path}")
        print("="*50)

        logger.info("Processing completed successfully")

    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())