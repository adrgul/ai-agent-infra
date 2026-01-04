"""
Unit tests for infrastructure/openai_clients.py module.

Tests cover:
- OpenAIClientFactory singleton pattern
- LLM client creation and caching
- Embeddings client creation and caching
- Usage stats methods
- Client reset functionality
"""
import pytest
import os
from unittest.mock import Mock, patch
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from infrastructure.openai_clients import OpenAIClientFactory


class TestOpenAIClientFactory:
    """Tests for OpenAIClientFactory class."""
    
    def setup_method(self):
        """Reset factory state before each test."""
        OpenAIClientFactory.reset()
    
    def teardown_method(self):
        """Clean up after each test."""
        OpenAIClientFactory.reset()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    def test_get_llm_creates_instance(self, mock_chat_openai):
        """Test get_llm creates ChatOpenAI instance on first call."""
        mock_instance = Mock(spec=ChatOpenAI)
        mock_chat_openai.return_value = mock_instance
        
        llm = OpenAIClientFactory.get_llm()
        
        assert llm == mock_instance
        mock_chat_openai.assert_called_once()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    def test_get_llm_singleton_pattern(self, mock_chat_openai):
        """Test get_llm returns same instance on subsequent calls (singleton)."""
        mock_instance = Mock(spec=ChatOpenAI)
        mock_chat_openai.return_value = mock_instance
        
        llm1 = OpenAIClientFactory.get_llm()
        llm2 = OpenAIClientFactory.get_llm()
        llm3 = OpenAIClientFactory.get_llm()
        
        assert llm1 is llm2 is llm3
        mock_chat_openai.assert_called_once()  # Only created once
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123", "OPENAI_MODEL": "gpt-4o"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    def test_get_llm_uses_env_variables(self, mock_chat_openai):
        """Test get_llm uses environment variables for configuration."""
        OpenAIClientFactory.get_llm()
        
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs['model'] == 'gpt-4o'
        assert call_kwargs['openai_api_key'] == 'test-key-123'
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    def test_get_llm_custom_parameters(self, mock_chat_openai):
        """Test get_llm accepts custom parameters."""
        OpenAIClientFactory.get_llm(
            model="gpt-4-turbo",
            temperature=0.5,
            max_retries=5,
            request_timeout=120
        )
        
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs['model'] == 'gpt-4-turbo'
        assert call_kwargs['temperature'] == 0.5
        assert call_kwargs['max_retries'] == 5
        assert call_kwargs['request_timeout'] == 120
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_llm_missing_api_key_raises_error(self):
        """Test get_llm raises ValueError when OPENAI_API_KEY is missing."""
        with pytest.raises(ValueError) as exc_info:
            OpenAIClientFactory.get_llm()
        
        assert "OPENAI_API_KEY not set" in str(exc_info.value)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    def test_get_llm_default_values(self, mock_chat_openai):
        """Test get_llm uses correct default values."""
        OpenAIClientFactory.get_llm()
        
        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs['model'] == 'gpt-4o-mini'  # Default model
        assert call_kwargs['temperature'] == 0.7  # Default temperature
        assert call_kwargs['max_retries'] == 3  # Default retries
        assert call_kwargs['request_timeout'] == 60  # Default timeout
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.OpenAIEmbeddings')
    def test_get_embeddings_creates_instance(self, mock_embeddings):
        """Test get_embeddings creates OpenAIEmbeddings instance."""
        mock_instance = Mock(spec=OpenAIEmbeddings)
        mock_embeddings.return_value = mock_instance
        
        embeddings = OpenAIClientFactory.get_embeddings()
        
        assert embeddings == mock_instance
        mock_embeddings.assert_called_once()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.OpenAIEmbeddings')
    def test_get_embeddings_singleton_pattern(self, mock_embeddings):
        """Test get_embeddings returns same instance (singleton)."""
        mock_instance = Mock(spec=OpenAIEmbeddings)
        mock_embeddings.return_value = mock_instance
        
        emb1 = OpenAIClientFactory.get_embeddings()
        emb2 = OpenAIClientFactory.get_embeddings()
        emb3 = OpenAIClientFactory.get_embeddings()
        
        assert emb1 is emb2 is emb3
        mock_embeddings.assert_called_once()  # Only created once
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123", "EMBEDDING_MODEL": "text-embedding-3-large"})
    @patch('infrastructure.openai_clients.OpenAIEmbeddings')
    def test_get_embeddings_uses_env_variables(self, mock_embeddings):
        """Test get_embeddings uses environment variables."""
        OpenAIClientFactory.get_embeddings()
        
        call_kwargs = mock_embeddings.call_args[1]
        assert call_kwargs['model'] == 'text-embedding-3-large'
        assert call_kwargs['openai_api_key'] == 'test-key-123'
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.OpenAIEmbeddings')
    def test_get_embeddings_custom_parameters(self, mock_embeddings):
        """Test get_embeddings accepts custom parameters."""
        OpenAIClientFactory.get_embeddings(
            model="text-embedding-ada-002",
            max_retries=5
        )
        
        call_kwargs = mock_embeddings.call_args[1]
        assert call_kwargs['model'] == 'text-embedding-ada-002'
        assert call_kwargs['max_retries'] == 5
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_embeddings_missing_api_key_raises_error(self):
        """Test get_embeddings raises ValueError when API key missing."""
        with pytest.raises(ValueError) as exc_info:
            OpenAIClientFactory.get_embeddings()
        
        assert "OPENAI_API_KEY not set" in str(exc_info.value)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.OpenAIEmbeddings')
    def test_get_embeddings_default_values(self, mock_embeddings):
        """Test get_embeddings uses correct default values."""
        OpenAIClientFactory.get_embeddings()
        
        call_kwargs = mock_embeddings.call_args[1]
        assert call_kwargs['model'] == 'text-embedding-3-small'  # Default
        assert call_kwargs['max_retries'] == 3  # Default


class TestUsageStats:
    """Tests for usage statistics methods."""
    
    def setup_method(self):
        """Reset factory and tracker before each test."""
        OpenAIClientFactory.reset()
        # Reset usage tracker
        from infrastructure.error_handling import usage_tracker
        usage_tracker.reset()
    
    @patch('infrastructure.openai_clients.usage_tracker')
    def test_get_usage_stats(self, mock_tracker):
        """Test get_usage_stats returns tracker summary."""
        mock_summary = {
            "calls": 10,
            "prompt_tokens": 5000,
            "completion_tokens": 2000,
            "total_tokens": 7000,
            "total_cost_usd": 0.0123
        }
        mock_tracker.get_summary.return_value = mock_summary
        
        stats = OpenAIClientFactory.get_usage_stats()
        
        assert stats == mock_summary
        mock_tracker.get_summary.assert_called_once()
    
    @patch('infrastructure.openai_clients.usage_tracker')
    def test_reset_usage_stats(self, mock_tracker):
        """Test reset_usage_stats calls tracker.reset()."""
        OpenAIClientFactory.reset_usage_stats()
        
        mock_tracker.reset.assert_called_once()


class TestClientReset:
    """Tests for client reset functionality."""
    
    def setup_method(self):
        """Reset factory before each test."""
        OpenAIClientFactory.reset()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    @patch('infrastructure.openai_clients.OpenAIEmbeddings')
    def test_reset_clears_llm_instance(self, mock_embeddings, mock_chat):
        """Test reset() clears LLM instance."""
        mock_llm = Mock(spec=ChatOpenAI)
        mock_chat.return_value = mock_llm
        
        # Create instance
        llm1 = OpenAIClientFactory.get_llm()
        assert llm1 == mock_llm
        
        # Reset
        OpenAIClientFactory.reset()
        
        # Create new instance (should call ChatOpenAI again)
        llm2 = OpenAIClientFactory.get_llm()
        
        assert llm2 == mock_llm  # New instance after reset
        assert mock_chat.call_count == 2  # Called twice
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    @patch('infrastructure.openai_clients.OpenAIEmbeddings')
    def test_reset_clears_embeddings_instance(self, mock_embeddings, mock_chat):
        """Test reset() clears Embeddings instance."""
        mock_emb = Mock(spec=OpenAIEmbeddings)
        mock_embeddings.return_value = mock_emb
        
        # Create instance
        emb1 = OpenAIClientFactory.get_embeddings()
        assert emb1 == mock_emb
        
        # Reset
        OpenAIClientFactory.reset()
        
        # Create new instance
        emb2 = OpenAIClientFactory.get_embeddings()
        
        assert emb2 == mock_emb  # New instance after reset
        assert mock_embeddings.call_count == 2  # Called twice
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    @patch('infrastructure.openai_clients.OpenAIEmbeddings')
    def test_reset_clears_both_instances(self, mock_embeddings, mock_chat):
        """Test reset() clears both LLM and Embeddings instances."""
        # Setup mocks
        mock_llm = Mock(spec=ChatOpenAI)
        mock_emb = Mock(spec=OpenAIEmbeddings)
        mock_chat.return_value = mock_llm
        mock_embeddings.return_value = mock_emb
        
        # Create both instances
        OpenAIClientFactory.get_llm()
        OpenAIClientFactory.get_embeddings()
        
        assert mock_chat.call_count == 1
        assert mock_embeddings.call_count == 1
        
        # Reset
        OpenAIClientFactory.reset()
        
        # Create both again
        OpenAIClientFactory.get_llm()
        OpenAIClientFactory.get_embeddings()
        
        assert mock_chat.call_count == 2
        assert mock_embeddings.call_count == 2


class TestTemperatureHandling:
    """Tests for temperature parameter handling."""
    
    def setup_method(self):
        """Reset factory before each test."""
        OpenAIClientFactory.reset()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123", "LLM_TEMPERATURE": "0.9"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    def test_temperature_from_env(self, mock_chat):
        """Test temperature is read from LLM_TEMPERATURE env variable."""
        mock_instance = Mock(spec=ChatOpenAI)
        mock_chat.return_value = mock_instance
        
        OpenAIClientFactory.get_llm()
        
        call_kwargs = mock_chat.call_args[1]
        assert call_kwargs['temperature'] == 0.9
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    def test_temperature_zero(self, mock_chat):
        """Test temperature=0.0 is handled correctly."""
        mock_instance = Mock(spec=ChatOpenAI)
        mock_chat.return_value = mock_instance
        
        OpenAIClientFactory.get_llm(temperature=0.0)
        
        call_kwargs = mock_chat.call_args[1]
        assert call_kwargs['temperature'] == 0.0
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    def test_temperature_one(self, mock_chat):
        """Test temperature=1.0 is handled correctly."""
        mock_instance = Mock(spec=ChatOpenAI)
        mock_chat.return_value = mock_instance
        
        OpenAIClientFactory.get_llm(temperature=1.0)
        
        call_kwargs = mock_chat.call_args[1]
        assert call_kwargs['temperature'] == 1.0


# Integration tests
class TestOpenAIClientFactoryIntegration:
    """Integration tests for OpenAIClientFactory."""
    
    def setup_method(self):
        """Reset factory before each test."""
        OpenAIClientFactory.reset()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    @patch('infrastructure.openai_clients.OpenAIEmbeddings')
    def test_multiple_clients_independent(self, mock_embeddings, mock_chat):
        """Test LLM and Embeddings instances are independent."""
        mock_llm = Mock(spec=ChatOpenAI)
        mock_emb = Mock(spec=OpenAIEmbeddings)
        mock_chat.return_value = mock_llm
        mock_embeddings.return_value = mock_emb
        
        llm = OpenAIClientFactory.get_llm()
        embeddings = OpenAIClientFactory.get_embeddings()
        
        assert llm != embeddings
        assert isinstance(llm, Mock)
        assert isinstance(embeddings, Mock)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    def test_llm_configuration_persistence(self, mock_chat):
        """Test LLM configuration persists across calls."""
        mock_instance = Mock(spec=ChatOpenAI)
        mock_instance.model_name = "gpt-4o-mini"
        mock_instance.temperature = 0.7
        mock_chat.return_value = mock_instance
        
        llm1 = OpenAIClientFactory.get_llm()
        llm2 = OpenAIClientFactory.get_llm()
        
        # Should be same instance with same config
        assert llm1 is llm2
        assert llm1.model_name == "gpt-4o-mini"
        assert llm2.model_name == "gpt-4o-mini"
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123"})
    @patch('infrastructure.openai_clients.ChatOpenAI')
    @patch('infrastructure.openai_clients.usage_tracker')
    def test_full_workflow_with_tracking(self, mock_tracker, mock_chat):
        """Test complete workflow: create client → get stats → reset."""
        # Setup
        mock_stats = {"calls": 5, "total_cost_usd": 0.05}
        mock_tracker.get_summary.return_value = mock_stats
        
        # Create client
        OpenAIClientFactory.get_llm()
        
        # Get stats
        stats = OpenAIClientFactory.get_usage_stats()
        assert stats == mock_stats
        
        # Reset stats
        OpenAIClientFactory.reset_usage_stats()
        mock_tracker.reset.assert_called_once()
        
        # Reset clients
        OpenAIClientFactory.reset()
        
        # Should be able to create new client
        OpenAIClientFactory.get_llm()
        assert mock_chat.call_count == 2  # Created twice
