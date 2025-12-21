import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_llm(model="gpt-4o", temperature=0):
    """
    Returns a configured ChatOpenAI instance.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=api_key
    )
