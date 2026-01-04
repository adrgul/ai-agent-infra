"""
Unit tests for SLA Advisor Agent.

Run with: pytest tests.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from pydantic import ValidationError

from models import TicketAnalysis
from config import Settings, get_settings
from tools import get_location_info, get_holidays, calculate_sla_deadline


# =============================================================================
# TicketAnalysis Model Tests
# =============================================================================

class TestTicketAnalysis:
    """Tests for the TicketAnalysis Pydantic model."""

    def test_valid_ticket_analysis(self):
        """Test creating a valid TicketAnalysis object."""
        analysis = TicketAnalysis(
            language="English",
            sentiment="frustrated",
            category="Billing",
            priority="P1",
            routing="Finance Team"
        )
        assert analysis.language == "English"
        assert analysis.sentiment == "frustrated"
        assert analysis.category == "Billing"
        assert analysis.priority == "P1"
        assert analysis.routing == "Finance Team"

    def test_all_sentiment_values(self):
        """Test all valid sentiment values."""
        for sentiment in ["frustrated", "neutral", "satisfied"]:
            analysis = TicketAnalysis(
                language="English",
                sentiment=sentiment,
                category="General",
                priority="P3",
                routing="General Support"
            )
            assert analysis.sentiment == sentiment

    def test_all_category_values(self):
        """Test all valid category values."""
        categories = ["Billing", "Technical", "Account", "Feature Request", "General"]
        for category in categories:
            analysis = TicketAnalysis(
                language="English",
                sentiment="neutral",
                category=category,
                priority="P3",
                routing="General Support"
            )
            assert analysis.category == category

    def test_all_priority_values(self):
        """Test all valid priority values."""
        for priority in ["P1", "P2", "P3", "P4"]:
            analysis = TicketAnalysis(
                language="English",
                sentiment="neutral",
                category="General",
                priority=priority,
                routing="General Support"
            )
            assert analysis.priority == priority

    def test_invalid_sentiment_raises_error(self):
        """Test that invalid sentiment raises ValidationError."""
        with pytest.raises(ValidationError):
            TicketAnalysis(
                language="English",
                sentiment="angry",  # Invalid
                category="General",
                priority="P3",
                routing="General Support"
            )

    def test_invalid_category_raises_error(self):
        """Test that invalid category raises ValidationError."""
        with pytest.raises(ValidationError):
            TicketAnalysis(
                language="English",
                sentiment="neutral",
                category="Invalid Category",  # Invalid
                priority="P3",
                routing="General Support"
            )

    def test_invalid_priority_raises_error(self):
        """Test that invalid priority raises ValidationError."""
        with pytest.raises(ValidationError):
            TicketAnalysis(
                language="English",
                sentiment="neutral",
                category="General",
                priority="P5",  # Invalid
                routing="General Support"
            )

    def test_model_dump(self):
        """Test model serialization to dictionary."""
        analysis = TicketAnalysis(
            language="Hungarian",
            sentiment="frustrated",
            category="Billing",
            priority="P2",
            routing="Finance Team"
        )
        data = analysis.model_dump()
        assert isinstance(data, dict)
        assert data["language"] == "Hungarian"
        assert data["priority"] == "P2"


# =============================================================================
# Settings Tests
# =============================================================================

class TestSettings:
    """Tests for the Settings configuration."""

    def test_settings_with_env_vars(self, monkeypatch):
        """Test Settings loads from environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")

        # Clear cache to force reload
        get_settings.cache_clear()

        settings = Settings()
        assert settings.openai_api_key == "test-api-key"
        assert settings.openai_model == "gpt-4"

    def test_default_values(self, monkeypatch):
        """Test default values are applied."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        settings = Settings()
        assert settings.openai_model == "gpt-4.1-mini"
        assert settings.ip_api_url == "http://ip-api.com/json"
        assert settings.holidays_api_url == "https://date.nager.at/api/v3/PublicHolidays"


# =============================================================================
# Tools Tests
# =============================================================================

class TestGetLocationInfo:
    """Tests for the get_location_info tool."""

    @patch('tools.requests.get')
    @patch('tools.get_settings')
    def test_successful_location_lookup(self, mock_settings, mock_get):
        """Test successful IP location lookup."""
        mock_settings.return_value = Mock(ip_api_url="http://ip-api.com/json")
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "status": "success",
                "country": "United States",
                "countryCode": "US",
                "city": "Mountain View",
                "regionName": "California",
                "timezone": "America/Los_Angeles",
                "isp": "Google LLC"
            }
        )
        mock_get.return_value.raise_for_status = Mock()

        result = get_location_info.invoke({"ip_address": "8.8.8.8"})

        assert result["error"] == False
        assert result["country"] == "United States"
        assert result["country_code"] == "US"
        assert result["city"] == "Mountain View"
        assert result["timezone"] == "America/Los_Angeles"

    @patch('tools.requests.get')
    @patch('tools.get_settings')
    def test_failed_location_lookup(self, mock_settings, mock_get):
        """Test failed IP location lookup."""
        mock_settings.return_value = Mock(ip_api_url="http://ip-api.com/json")
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "status": "fail",
                "message": "invalid query"
            }
        )
        mock_get.return_value.raise_for_status = Mock()

        result = get_location_info.invoke({"ip_address": "invalid"})

        assert result["error"] == True
        assert "Failed to query" in result["message"]

    @patch('tools.requests.get')
    @patch('tools.get_settings')
    def test_network_error(self, mock_settings, mock_get):
        """Test network error handling."""
        import requests
        mock_settings.return_value = Mock(ip_api_url="http://ip-api.com/json")
        mock_get.side_effect = requests.RequestException("Connection failed")

        result = get_location_info.invoke({"ip_address": "8.8.8.8"})

        assert result["error"] == True
        assert "Network error" in result["message"]


class TestGetHolidays:
    """Tests for the get_holidays tool."""

    @patch('tools.requests.get')
    @patch('tools.get_settings')
    def test_successful_holiday_lookup(self, mock_settings, mock_get):
        """Test successful holiday lookup."""
        mock_settings.return_value = Mock(
            holidays_api_url="https://date.nager.at/api/v3/PublicHolidays"
        )
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: [
                {"date": "2025-01-01", "name": "New Year's Day", "localName": "Újév"},
                {"date": "2025-12-25", "name": "Christmas Day", "localName": "Karácsony"}
            ]
        )
        mock_get.return_value.raise_for_status = Mock()

        result = get_holidays.invoke({"country_code": "HU", "year": 2025})

        assert result["error"] == False
        assert result["country_code"] == "HU"
        assert result["year"] == 2025
        assert len(result["holidays"]) == 2
        assert result["holidays"][0]["name"] == "New Year's Day"

    @patch('tools.requests.get')
    @patch('tools.get_settings')
    def test_country_not_found(self, mock_settings, mock_get):
        """Test holiday lookup for unknown country."""
        mock_settings.return_value = Mock(
            holidays_api_url="https://date.nager.at/api/v3/PublicHolidays"
        )
        mock_get.return_value = Mock(status_code=404)

        result = get_holidays.invoke({"country_code": "XX"})

        assert result["error"] == False
        assert result["holidays"] == []
        assert "No data available" in result["message"]


class TestCalculateSlaDeadline:
    """Tests for the calculate_sla_deadline tool."""

    @patch('tools.get_holidays')
    def test_p1_priority_deadline(self, mock_holidays):
        """Test P1 priority gives 4 hour deadline."""
        mock_holidays.invoke = Mock(return_value={"error": False, "holidays": []})

        result = calculate_sla_deadline.invoke({
            "timezone": "Europe/Budapest",
            "priority": "P1",
            "country_code": "HU"
        })

        assert result["priority"] == "P1"
        assert result["priority_name"] == "Critical"
        assert result["sla_hours"] == 4

    @patch('tools.get_holidays')
    def test_p2_priority_deadline(self, mock_holidays):
        """Test P2 priority gives 8 hour deadline."""
        mock_holidays.invoke = Mock(return_value={"error": False, "holidays": []})

        result = calculate_sla_deadline.invoke({
            "timezone": "Europe/Budapest",
            "priority": "P2",
            "country_code": ""
        })

        assert result["priority"] == "P2"
        assert result["priority_name"] == "High"
        assert result["sla_hours"] == 8

    @patch('tools.get_holidays')
    def test_p3_priority_deadline(self, mock_holidays):
        """Test P3 priority gives 24 hour deadline."""
        mock_holidays.invoke = Mock(return_value={"error": False, "holidays": []})

        result = calculate_sla_deadline.invoke({
            "timezone": "UTC",
            "priority": "P3",
            "country_code": ""
        })

        assert result["priority"] == "P3"
        assert result["priority_name"] == "Medium"
        assert result["sla_hours"] == 24

    @patch('tools.get_holidays')
    def test_p4_priority_deadline(self, mock_holidays):
        """Test P4 priority gives 72 hour deadline."""
        mock_holidays.invoke = Mock(return_value={"error": False, "holidays": []})

        result = calculate_sla_deadline.invoke({
            "timezone": "UTC",
            "priority": "P4",
            "country_code": ""
        })

        assert result["priority"] == "P4"
        assert result["priority_name"] == "Low"
        assert result["sla_hours"] == 72

    @patch('tools.get_holidays')
    def test_case_insensitive_priority(self, mock_holidays):
        """Test priority is case insensitive."""
        mock_holidays.invoke = Mock(return_value={"error": False, "holidays": []})

        result = calculate_sla_deadline.invoke({
            "timezone": "UTC",
            "priority": "p1",
            "country_code": ""
        })

        assert result["priority"] == "P1"

    def test_deadline_format(self):
        """Test deadline is formatted correctly."""
        result = calculate_sla_deadline.invoke({
            "timezone": "UTC",
            "priority": "P3",
            "country_code": ""
        })

        assert "deadline" in result
        assert "deadline_local_format" in result
        # Check format: YYYY-MM-DD HH:MM
        assert len(result["deadline"]) == 16


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests (require mocking external services)."""

    @patch('agent.ChatOpenAI')
    @patch('agent.get_settings')
    def test_agent_initialization(self, mock_settings, mock_llm):
        """Test agent initializes correctly."""
        mock_settings.return_value = Mock(
            openai_api_key="test-key",
            openai_model="gpt-4.1-mini"
        )
        mock_llm_instance = Mock()
        mock_llm_instance.with_structured_output = Mock(return_value=Mock())
        mock_llm.return_value = mock_llm_instance

        from agent import SLAAdvisorAgent
        agent = SLAAdvisorAgent()

        assert agent.llm is not None
        assert agent.graph is not None


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
