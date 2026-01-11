import operator
from typing import List, Annotated, TypedDict, Union
from models import Task  # Assuming models.py is in the same directory/package

class MeetingState(TypedDict):
    """
    Represents the state of the meeting processing graph.
    """
    transcript: str
    notes: Annotated[List[str], operator.add]
    tasks: List[Union[dict, Task]] # Allow dict for flexibility during serialization/deserialization, primarily Task objects
    summary: str
    short_summary: str
    meeting_date: str # ISO format date string, extracted or defaulted
