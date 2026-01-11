import os
import json
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from state import MeetingState
from models import MeetingNotes, Task

# Initialize LLM
# Note: In a real environment, allow configuring the model name.
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def note_taker(state: MeetingState) -> Dict[str, Any]:
    """
    Agent that extracts structured meeting notes from the transcript.
    """
    transcript = state["transcript"]
    
    parser = PydanticOutputParser(pydantic_object=MeetingNotes)
    
    system_prompt = (
        "You are an expert meeting note taker. "
        "Your goal is to extract key points and decisions from the transcript. "
        "Ignore chit-chat and focus on facts. "
        "\n{format_instructions}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Transcript:\n{transcript}")
    ])
    
    chain = prompt | llm | parser
    
    notes: MeetingNotes = chain.invoke({
        "transcript": transcript,
        "format_instructions": parser.get_format_instructions()
    })
    
    # Return as a list of strings for the 'notes' accumulator in state
    # We'll format the structured notes into strings for simplicity in the accumulator,
    # or we can pass the object itself if we change the state definition.
    # The state definition says `notes` is List[str].
    # Let's serialize the key points and decisions into readable strings.
    
    note_strings = []
    for kp in notes.key_points:
        note_strings.append(f"Key Point: {kp}")
    for dec in notes.decisions:
        note_strings.append(f"Decision: {dec}")
        
    return {"notes": note_strings}

def task_assigner(state: MeetingState) -> Dict[str, Any]:
    """
    Agent that extracts actionable tasks from the transcript.
    """
    transcript = state["transcript"]
    
    # We need to extract a List[Task]. PydanticOutputParser usually extracts a single object.
    # To extract a list, we can wrap it in a container model or ask for a list in the prompt.
    # Here, let's create a wrapper model for parsing list of tasks.
    from pydantic import BaseModel, Field
    
    class TaskList(BaseModel):
        tasks: List[Task] = Field(description="List of actionable tasks.")

    parser = PydanticOutputParser(pydantic_object=TaskList)
    
    system_prompt = (
        "You are a project manager. "
        "Identify actionable items and owners from the transcript. "
        "Extract them as a list of tasks. "
        "If no assignee is mentioned, use 'Unassigned'. "
        "\n{format_instructions}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Transcript:\n{transcript}")
    ])
    
    chain = prompt | llm | parser
    
    result: TaskList = chain.invoke({
        "transcript": transcript,
        "format_instructions": parser.get_format_instructions()
    })
    
    # Return tasks into the state
    return {"tasks": result.tasks}

def summarizer(state: MeetingState) -> Dict[str, Any]:
    """
    Agent that writes a markdown summary based ONLY on notes and tasks.
    """
    notes = state.get("notes", [])
    tasks = state.get("tasks", [])
    
    # Convert tasks to string representation for the prompt if they are objects
    tasks_str = ""
    for t in tasks:
        if isinstance(t, Task):
            tasks_str += f"- {t.title} (Assignee: {t.assignee}, Due: {t.due_date})\n"
        else:
            tasks_str += f"- {t}\n"
            
    notes_str = "\n".join(notes)
    
    # Define output structure
    from pydantic import BaseModel, Field
    
    class MeetingSummaries(BaseModel):
        full_summary: str = Field(description="The full executive summary in Markdown format with subheaders.")
        short_summary: str = Field(description="A very short summary (1-2 sentences) suitable for a list view card.")

    parser = PydanticOutputParser(pydantic_object=MeetingSummaries)

    system_prompt = (
        "You are a professional technical writer. "
        "Generate two summaries based strictly on the provided notes and tasks:\n"
        "1. A full executive summary in Markdown format. Do NOT include a top-level heading like 'Executive Summary'; start directly with the content or subheadings.\n"
        "2. A very short summary (1-2 sentences) for a preview card.\n"
        "Do NOT reference the raw transcript. "
        "\n{format_instructions}"
    )
    
    human_input = (
        f"Notes:\n{notes_str}\n\n"
        f"Tasks:\n{tasks_str}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    
    chain = prompt | llm | parser
    
    response = chain.invoke({
        "input": human_input,
        "format_instructions": parser.get_format_instructions()
    })
    
    return {
        "summary": response.full_summary,
        "short_summary": response.short_summary
    }


def metadata_extractor(state: MeetingState) -> Dict[str, Any]:
    """
    Agent that extracts metadata like meeting date from the transcript.
    """
    transcript = state["transcript"]
    
    from pydantic import BaseModel, Field
    
    class MeetingMetadata(BaseModel):
        meeting_date: Optional[str] = Field(description="The date of the meeting if mentioned in the transcript (ISO format YYYY-MM-DD). If not mentioned, return null.")

    parser = PydanticOutputParser(pydantic_object=MeetingMetadata)
    
    system_prompt = (
        "You are an expert at extracting metadata from meeting transcripts. "
        "Extract the meeting date if it is explicitly mentioned or can be inferred from the context (e.g. 'today is January 1st'). "
        "If the date is not found, return null."
        "\n{format_instructions}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Transcript:\n{transcript}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        metadata: MeetingMetadata = chain.invoke({
            "transcript": transcript[:10000], # Limit context for efficiency if needed, but important for date which is usually at start
            "format_instructions": parser.get_format_instructions()
        })
        return {"meeting_date": metadata.meeting_date}
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return {"meeting_date": None}
