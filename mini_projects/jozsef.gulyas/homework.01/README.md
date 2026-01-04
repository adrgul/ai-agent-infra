# Homework 01 - AI Chat Console Application

A command-line chatbot application that integrates with OpenAI's API to provide an interactive conversation experience with dynamic, contextual follow-up questions.

## Description

This console application allows users to interact with OpenAI's GPT-4o-mini model through a command-line interface. The application uses OpenAI's JSON mode to generate structured responses, maintaining conversation history throughout the session and providing contextual follow-up questions that make the interaction feel more natural and engaging.

## Features

- Interactive chat interface in the terminal
- **Dynamic follow-up questions** - AI generates contextual follow-up questions instead of generic prompts
- **JSON-structured responses** - Clean separation between answers and follow-up questions
- Conversation history maintained throughout the session
- Uses OpenAI's GPT-4o-mini model with JSON mode
- Configurable system prompt via external file
- Simple and intuitive user experience
- Graceful exit with 'exit' command

## Prerequisites

- Python 3.13 or higher
- An OpenAI API key (get one from [OpenAI Platform](https://platform.openai.com/api-keys))
- uv package manager (recommended) or pip

## Installation

1. Clone the repository or navigate to the project directory:
```bash
cd homework.01
```

2. Install dependencies using uv:
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

## Configuration

### Setting up the Environment File

The application requires an OpenAI API key to function. Follow these steps to configure it:

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Open the `.env` file in your text editor

3. Replace `your_openai_api_key_here` with your actual OpenAI API key:
```
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
```

4. Save the file

**Important:** Never commit your `.env` file to version control as it contains sensitive information.

## Usage

### Running the Application

Using uv:
```bash
uv run python -m application.main
```

Or if you've activated the virtual environment:
```bash
python -m application.main
```

### Interacting with the Chatbot

1. Once started, you'll see the initial prompt:
```
How can I help you today?
```

2. Type your message or question and press Enter

3. The assistant will respond with a helpful answer

4. After each response, you'll see a **contextual follow-up question** related to your conversation, making the interaction feel more natural:
```
Would you like to know more about this topic?
```

5. Continue the conversation - each response includes a new relevant follow-up question

6. Type `exit` at any prompt to end the session

### How It Works

The application uses OpenAI's JSON mode to receive structured responses containing:
- `answer`: The actual response to your question
- `followUpQuestion`: A contextual question to continue the conversation

This creates a more engaging and natural conversation flow compared to repetitive generic prompts.

## Dependencies

This project uses the following Python packages:

- **requests** (>=2.32.5) - For making HTTP requests to the OpenAI API
- **python-dotenv** (>=1.2.1) - For loading environment variables from .env file

## Project Structure

```
homework.01/
├── application/
│   ├── __init__.py
│   └── main.py              # Main application code
├── prompts/
│   ├── __init__.py
│   └── system_prompt.md     # System prompt configuration for OpenAI
├── .env.example             # Example environment file
├── .python-version          # Python version specification
├── PLAN.md                  # Implementation plan documentation
├── pyproject.toml           # Project configuration and dependencies
├── uv.lock                  # Lock file for uv package manager
└── README.md                # This file
```

## Customizing the System Prompt

The system prompt that instructs the AI how to behave is stored in `prompts/system_prompt.md`. You can edit this file to customize:
- The AI's personality and tone
- Response format instructions
- Follow-up question style

**Current system prompt:**
```
You are a helpful assistant.

Always respond with a JSON object containing two fields: 'answer' (your response to the user's question) and 'followUpQuestion' (a contextual follow-up question to continue the conversation). Pay attention when generating `answer` that you're going to ask question in `followUpQuestion`, so answer should not contain questions.
```

**Note:** The prompt must instruct the model to return JSON with `answer` and `followUpQuestion` fields for the application to work correctly.

## Troubleshooting

### Error: "OPENAI_API_KEY must be set"

This error means the application couldn't find your API key. Make sure:
1. You've created a `.env` file from `.env.example`
2. Your API key is correctly set in the `.env` file
3. There are no extra spaces or quotes around the API key

### Error: "FileNotFoundError: No such file or directory: '/prompts/system_prompt.txt'"

This error occurs if the application can't find the system prompt file. This usually happens if:
- The `prompts/system_prompt.md` file is missing
- The file path in `main.py` is incorrect

**Solution:** Ensure the `prompts/system_prompt.md` file exists and the path in `main.py` is correct (should use relative path)

### Error: "Error: 401"

This indicates an authentication problem:
- Verify your API key is correct and active
- Check that you have credits available in your OpenAI account
- Ensure the API key hasn't expired

### Error: "Error: 429"

This means you've hit rate limits:
- Wait a few moments before trying again
- Check your OpenAI account usage limits

## License

This is a homework project for educational purposes.
