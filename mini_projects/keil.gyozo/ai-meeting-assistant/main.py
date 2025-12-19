"""
Main entry point for the AI Meeting Assistant.

This script demonstrates how to use the meeting processing workflow
with a sample transcript.
"""

import os
import json
from dotenv import load_dotenv
from src.workflow.graph import process_meeting
from src.models.schemas import ProcessedMeeting


# Sample meeting transcript
SAMPLE_TRANSCRIPT = """
John: Good morning everyone. Thanks for joining today's product planning meeting.
We have a lot to cover, so let's get started.

Sarah: Morning! I wanted to discuss the timeline for the new user dashboard feature.
Based on our last sprint, I think we can have the initial mockups ready by next Friday.

John: That sounds great, Sarah. Can you take ownership of that? We'll need those mockups
for the client presentation on the 15th.

Sarah: Absolutely. I'll have them done by Friday, March 10th.

Mike: I wanted to bring up the API integration issues we've been experiencing.
The third-party payment service has been timing out frequently. This is urgent and
needs to be addressed ASAP.

John: Mike, can you investigate the root cause and propose a solution?
Let's aim to have an update by end of day tomorrow.

Mike: Will do. I'll also loop in the DevOps team to check if it's an infrastructure issue.

Sarah: On another note, we should schedule a user testing session for the new onboarding flow.
I think it would be valuable to get feedback before we launch.

John: Good idea. Sarah, can you coordinate with the UX team to set that up sometime next week?

Sarah: Sure, I'll reach out to them today.

Mike: One more thing - we need to update the API documentation. It's been outdated since
the last release. Not urgent, but should be done soon.

John: Mike, add that to your backlog. Let's try to get it done within the next two weeks
if possible.

Mike: Noted.

John: Alright, I think that covers everything. Let's reconvene next Monday to check on progress.
Thanks everyone!
"""


def main():
    """Main function to process a meeting transcript."""
    # Load environment variables
    load_dotenv()

    # Get OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please create a .env file with your API key."
        )

    # Get model name (optional)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    print("=" * 80)
    print("AI MEETING ASSISTANT")
    print("=" * 80)
    print("\nProcessing meeting transcript...\n")

    try:
        # Process the meeting
        result = process_meeting(
            transcript=SAMPLE_TRANSCRIPT,
            openai_api_key=openai_api_key,
            model_name=model_name,
            use_parallel=False  # Set to True for parallel processing
        )

        # Check for errors
        if result.errors:
            print("⚠️  Warnings/Errors encountered:")
            for error in result.errors:
                print(f"  - {error}")
            print()

        # Display summary
        if result.summary:
            print("📋 EXECUTIVE SUMMARY")
            print("-" * 80)
            print(f"{result.summary.summary}\n")

            if result.summary.key_points:
                print("Key Points:")
                for i, point in enumerate(result.summary.key_points, 1):
                    print(f"  {i}. {point}")
                print()

            if result.summary.participants:
                print(f"Participants: {', '.join(result.summary.participants)}")

            if result.summary.meeting_date:
                print(f"Meeting Date: {result.summary.meeting_date}")

            print()

        # Display action items
        if result.action_items:
            print("✅ ACTION ITEMS")
            print("-" * 80)
            for i, item in enumerate(result.action_items, 1):
                print(f"\n{i}. {item.task}")
                if item.assignee:
                    print(f"   👤 Assignee: {item.assignee}")
                if item.deadline:
                    print(f"   📅 Deadline: {item.deadline}")
                if item.priority:
                    priority_emoji = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢"
                    }.get(item.priority.lower(), "⚪")
                    print(f"   {priority_emoji} Priority: {item.priority.upper()}")
            print()
        else:
            print("No action items found.\n")

        # Create ProcessedMeeting object for JSON export
        if result.summary:
            processed = ProcessedMeeting(
                summary=result.summary,
                action_items=result.action_items or []
            )

            # Save to JSON file
            output_file = "meeting_output.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    processed.model_dump(mode="json"),
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            print(f"💾 Results saved to: {output_file}")
            print()

        print("=" * 80)
        print("Processing complete!")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error processing meeting: {str(e)}")
        raise


if __name__ == "__main__":
    main()
