"""
Unit tests for infrastructure health check system.
Tests startup validation and configuration checks.
"""
import os
from unittest.mock import patch
from infrastructure.health_check import validate_startup_config_sync


class TestHealthCheckSystem:
    """Test health check validation system."""
    
    def test_health_check_with_all_services_available(self):
        """Test health check passes when all critical services are configured."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-12345678901234567890',
            'QDRANT_URL': 'http://qdrant:6333',
            'POSTGRES_HOST': 'postgres',
            'REDIS_URL': 'redis://redis:6379'
        }):
            result = validate_startup_config_sync()
            assert result is True, "Health check should pass with all services configured"
    
    def test_health_check_with_missing_openai_key(self):
        """Test health check fails when OPENAI_API_KEY is missing."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': '',
            'QDRANT_URL': 'http://qdrant:6333'
        }, clear=True):
            result = validate_startup_config_sync()
            assert result is False, "Health check should fail without OpenAI API key"
    
    def test_health_check_masks_api_key(self, capsys):
        """Test that API keys are masked in output."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-proj-very-secret-key-123456789',
            'QDRANT_URL': 'http://qdrant:6333'
        }):
            validate_startup_config_sync()
            captured = capsys.readouterr()
            
            # Should NOT contain full key
            assert 'sk-proj-very-secret-key-123456789' not in captured.out
            # Should contain masked version
            assert '***' in captured.out
    
    def test_health_check_displays_critical_services(self, capsys):
        """Test that critical services section is displayed."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key',
            'QDRANT_URL': 'http://qdrant:6333'
        }):
            validate_startup_config_sync()
            captured = capsys.readouterr()
            
            assert '📌 CRITICAL SERVICES:' in captured.out
            assert 'OPENAI_API_KEY' in captured.out
            assert 'Qdrant URL configured' in captured.out
    
    def test_health_check_displays_optional_services(self, capsys):
        """Test that optional services section is displayed."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key',
            'POSTGRES_HOST': 'postgres',
            'REDIS_URL': 'redis://redis:6379'
        }):
            validate_startup_config_sync()
            captured = capsys.readouterr()
            
            assert '📋 OPTIONAL SERVICES:' in captured.out
            assert 'PostgreSQL will use lazy init' in captured.out
            assert 'Redis configured' in captured.out
    
    def test_health_check_with_short_api_key(self):
        """Test health check handles short API keys correctly."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'short',
            'QDRANT_URL': 'http://qdrant:6333'
        }):
            result = validate_startup_config_sync()
            # Still passes since key is present (validation happens elsewhere)
            assert result is True


class TestHealthCheckIntegration:
    """Integration tests for health check system."""
    
    def test_health_check_uses_default_urls(self, capsys):
        """Test health check uses default values when env vars not set."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'sk-test-key'
        }, clear=True):
            validate_startup_config_sync()
            captured = capsys.readouterr()
            
            # Should use default Qdrant URL
            assert 'http://qdrant:6333' in captured.out
    
    def test_health_check_banner_formatting(self, capsys):
        """Test that health check banner is properly formatted."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key'}):
            validate_startup_config_sync()
            captured = capsys.readouterr()
            
            # Check for banner elements
            assert '🏥 INFRASTRUCTURE HEALTH CHECK' in captured.out
            assert '=' * 70 in captured.out
            assert '✅ ALL CRITICAL SERVICES READY' in captured.out or '❌ SOME CRITICAL SERVICES UNAVAILABLE' in captured.out
