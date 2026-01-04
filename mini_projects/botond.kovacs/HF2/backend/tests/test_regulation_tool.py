import pytest
from unittest.mock import AsyncMock, MagicMock
from services.tools import RegulationTool

class DummyRegulationClient:
    def __init__(self, response=None, info=None):
        self._response = response or {"answer": "dummy answer", "sources": [], "regulation_title": "test"}
        self._info = info or {"title": "test", "chunks_count": 5, "pages_count": 10, "status": "loaded_from_cache"}
        self.query = AsyncMock(return_value=self._response)
        self.get_regulation_info = AsyncMock(return_value=self._info)

@pytest.mark.asyncio
async def test_regulation_tool_query_success():
    client = DummyRegulationClient()
    tool = RegulationTool(client)
    result = await tool.execute(action="query", question="Mely paragrafusok?", top_k=3)
    assert result["success"] is True
    assert "answer" in result["data"]
    assert result["system_message"].startswith("Found answer")

@pytest.mark.asyncio
async def test_regulation_tool_query_error():
    client = DummyRegulationClient()
    client.query = AsyncMock(return_value={"error": "Nincs találat"})
    tool = RegulationTool(client)
    result = await tool.execute(action="query", question="Nincs ilyen", top_k=3)
    assert result["success"] is False
    assert result["error"] == "Nincs találat"

@pytest.mark.asyncio
async def test_regulation_tool_info_success():
    client = DummyRegulationClient()
    tool = RegulationTool(client)
    result = await tool.execute(action="info")
    assert result["success"] is True
    assert result["data"]["title"] == "test"
    assert "indexed chunks" in result["system_message"]

@pytest.mark.asyncio
async def test_regulation_tool_info_error():
    client = DummyRegulationClient()
    client.get_regulation_info = AsyncMock(return_value={"error": "Nincs info"})
    tool = RegulationTool(client)
    result = await tool.execute(action="info")
    assert result["success"] is False
    assert result["error"] == "Nincs info"

@pytest.mark.asyncio
async def test_regulation_tool_unknown_action():
    client = DummyRegulationClient()
    tool = RegulationTool(client)
    result = await tool.execute(action="invalid_action")
    assert result["success"] is False
    assert "Unknown regulation action" in result["system_message"]
