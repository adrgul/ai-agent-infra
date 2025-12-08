"""Agent planning and orchestration logic."""
from dataclasses import dataclass
from datetime import date
from enum import Enum

from loguru import logger


class AgentState(Enum):
    """Agent execution states."""

    PLANNING = "planning"
    GEOCODING = "geocoding"
    FETCHING_WEATHER = "fetching_weather"
    GENERATING_BRIEFING = "generating_briefing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentPlan:
    """Agent execution plan."""

    goal: str
    steps: list[str]
    current_step: int = 0
    state: AgentState = AgentState.PLANNING

    def next_step(self) -> str | None:
        """Get next step in plan."""
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self.current_step += 1
            return step
        return None

    def is_complete(self) -> bool:
        """Check if plan is complete."""
        return self.current_step >= len(self.steps)


class AgentPlanner:
    """Agent planner that creates execution plans."""

    @staticmethod
    def create_briefing_plan(city: str, target_date: date) -> AgentPlan:
        """
        Create a plan for generating a weather briefing.

        Args:
            city: City name
            target_date: Target date

        Returns:
            Agent execution plan
        """
        goal = f"Generate weather briefing for {city} on {target_date}"

        steps = [
            f"Geocode city '{city}' to coordinates",
            f"Fetch weather forecast for {target_date}",
            "Generate AI briefing with outfit and activity suggestions",
            "Save to history",
        ]

        logger.info(f"Created agent plan: {goal}")
        logger.debug(f"Plan steps: {steps}")

        return AgentPlan(goal=goal, steps=steps, state=AgentState.PLANNING)
