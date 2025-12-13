"""
Main entry point for MeetingAI CLI
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from meetingai.workflows.meeting_processor import MeetingProcessor
from meetingai.utils.config import Config
from meetingai.utils.logger import setup_logger

# Load environment variables
load_dotenv()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """MeetingAI - AI-Powered Meeting Assistant"""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--config", "-c", type=click.Path(), default="config.yaml",
              help="Path to configuration file")
@click.option("--jira", is_flag=True, help="Create Jira tickets")
@click.option("--email", is_flag=True, help="Send email notifications")
@click.option("--calendar", is_flag=True, help="Create calendar events")
@click.option("--slack", is_flag=True, help="Send Slack notifications")
def process(input_file: str, config: str, jira: bool, email: bool, calendar: bool, slack: bool):
    """Process a meeting document"""
    try:
        # Load configuration
        config_obj = Config.from_yaml(config)

        # Override integration flags
        if jira:
            config_obj.integrations.jira.enabled = True
        if email:
            config_obj.integrations.email.enabled = True
        if calendar:
            config_obj.integrations.calendar.enabled = True
        if slack:
            config_obj.integrations.slack.enabled = True

        # Initialize processor
        processor = MeetingProcessor(config_obj)

        # Process meeting
        click.echo(f"Processing {input_file}...")
        result = asyncio.run(processor.process(input_file))

        click.echo("✅ Processing complete!")
        click.echo(f"Summary: {result.summary.summary[:100]}...")
        click.echo(f"Tasks extracted: {len(result.tasks)}")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
@click.option("--config", "-c", type=click.Path(), default="config.yaml")
@click.option("--output-dir", "-o", type=click.Path(), default="./data/outputs")
def batch(input_files: list[str], config: str, output_dir: str):
    """Process multiple meeting documents"""
    try:
        config_obj = Config.from_yaml(config)
        processor = MeetingProcessor(config_obj)

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        for input_file in input_files:
            click.echo(f"Processing {input_file}...")
            result = asyncio.run(processor.process(input_file))

            # Save individual results
            output_file = output_path / f"{Path(input_file).stem}_result.json"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))

            click.echo(f"✅ Saved to {output_file}")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()