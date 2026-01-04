# AI Meeting Assistant

An intelligent meeting assistant built with LangChain and LangGraph that automatically processes meeting transcripts to generate executive summaries and extract actionable items.

## Features

- **Executive Summaries**: Generates concise 2-4 sentence summaries capturing the essence of meetings
- **Action Item Extraction**: Automatically identifies tasks with assignees, deadlines, and priorities
- **Structured Output**: Produces validated JSON output using Pydantic models
- **Flexible Processing**: Supports both sequential and parallel workflow execution
- **LangGraph Orchestration**: Uses state graphs for robust, maintainable workflow management

## Architecture

```
Meeting Transcript
       ↓
   [Parser Node] - Cleans and normalizes text
       ↓
   [Summarizer Node] - GPT-4 generates executive summary
       ↓
   [Action Items Node] - GPT-4 extracts actionable tasks
       ↓
   Structured JSON Output
```

## Project Structure

```
ai-meeting-assistant/
├── src/
│   ├── models/
│   │   └── schemas.py          # Pydantic models for data validation
│   ├── nodes/
│   │   ├── parser.py           # Transcript cleaning/parsing
│   │   ├── summarizer.py       # Summary generation with LLM
│   │   └── action_items.py     # Action item extraction with LLM
│   └── workflow/
│       └── graph.py            # LangGraph workflow definition
├── main.py                     # Entry point with sample transcript
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Prerequisites

- Python 3.12
- OpenAI API key (for GPT-4 access)

## Installation

1. **Clone or download this project**

2. **Create a virtual environment**:
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env and add your OpenAI API key
   OPENAI_API_KEY=your_actual_api_key_here
   OPENAI_MODEL=gpt-4-turbo-preview
   ```

## Usage

### Basic Usage

Run the demo with the included sample transcript:

```bash
python main.py
```

This will process the sample meeting transcript and display:
- Executive summary
- Key discussion points
- Action items with assignees, deadlines, and priorities
- JSON output saved to `meeting_output.json`

### Using in Your Code

```python
from dotenv import load_dotenv
import os
from src.workflow.graph import process_meeting

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Your meeting transcript
transcript = """
John: Let's discuss the Q4 roadmap...
Sarah: I can lead the frontend work, should be done by end of month...
"""

# Process the meeting
result = process_meeting(
    transcript=transcript,
    openai_api_key=openai_api_key,
    model_name="gpt-4-turbo-preview",
    use_parallel=False
)

# Access results
print(result.summary.summary)
for action in result.action_items:
    print(f"Task: {action.task}")
    print(f"Assignee: {action.assignee}")
    print(f"Deadline: {action.deadline}")
```

### Async Processing

For better performance with parallel execution:

```python
import asyncio
from src.workflow.graph import process_meeting_async

async def main():
    result = await process_meeting_async(
        transcript=your_transcript,
        openai_api_key=api_key,
        use_parallel=True  # Enables parallel processing
    )
    return result

result = asyncio.run(main())
```

## Output Format

The system produces structured JSON output:

```json
{
  "summary": {
    "summary": "Executive summary of the meeting...",
    "key_points": [
      "First key point",
      "Second key point"
    ],
    "participants": ["John", "Sarah", "Mike"],
    "meeting_date": "March 8, 2024"
  },
  "action_items": [
    {
      "task": "Prepare initial mockups for user dashboard",
      "assignee": "Sarah",
      "deadline": "Friday, March 10th",
      "priority": "medium"
    }
  ],
  "processed_at": "2024-03-08T10:30:00"
}
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model to use (default: `gpt-4-turbo-preview`)
- `LANGCHAIN_TRACING_V2`: Enable LangSmith tracing for debugging (optional)
- `LANGCHAIN_API_KEY`: LangSmith API key (optional)

### Model Options

Supported OpenAI models:
- `gpt-4-turbo-preview` (recommended)
- `gpt-4`
- `gpt-3.5-turbo` (faster, less accurate)

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
# Format code
black .

# Lint code
ruff check .
```

## How It Works

1. **Parser Node**: Cleans the transcript by removing timestamps, filler words, and normalizing formatting

2. **Summarizer Node**: Uses GPT-4 with a specialized prompt to generate:
   - Concise executive summary
   - Key discussion points
   - Identified participants
   - Meeting date (if mentioned)

3. **Action Items Node**: Uses GPT-4 to extract actionable tasks by looking for:
   - Action verbs and task descriptions
   - Assignee mentions
   - Deadline references
   - Priority indicators (urgent, ASAP, etc.)

4. **LangGraph Workflow**: Orchestrates the nodes in a state graph, automatically managing state flow and enabling parallel execution

## Customization

### Modify Prompts

Edit the prompts in:
- `src/nodes/summarizer.py` - Summary generation prompts
- `src/nodes/action_items.py` - Action item extraction prompts

### Add New Nodes

1. Create a new node function in `src/nodes/`
2. Add it to the workflow in `src/workflow/graph.py`
3. Update the `GraphState` model if needed

### Change Models

Edit the `model_name` parameter when calling `process_meeting()`:

```python
result = process_meeting(
    transcript=transcript,
    openai_api_key=api_key,
    model_name="gpt-3.5-turbo"  # Faster, cheaper option
)
```

## Troubleshooting

**API Key Error**:
- Ensure your `.env` file exists and contains a valid `OPENAI_API_KEY`
- Check that you've activated your virtual environment

**Import Errors**:
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify you're using Python 3.11 or higher

**Empty Results**:
- Check that your transcript has sufficient content (minimum 50 characters)
- Review the `errors` field in the output for processing issues

## License

MIT License - feel free to use this project for any purpose.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Acknowledgments

Built with:
- [LangChain](https://python.langchain.com/) - LLM application framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Graph-based workflow orchestration
- [OpenAI](https://openai.com/) - GPT-4 language model
- [Pydantic](https://docs.pydantic.dev/) - Data validation