"""
Configuration Service - system.ini Reader

Provides centralized access to system.ini configuration values.
"""

import configparser
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Singleton pattern for config parser
_config: Optional[configparser.ConfigParser] = None
_config_path = Path(__file__).parent / "system.ini"


def _load_config() -> configparser.ConfigParser:
    """Load system.ini configuration file (singleton)."""
    global _config
    
    if _config is None:
        _config = configparser.ConfigParser()
        if _config_path.exists():
            _config.read(_config_path, encoding='utf-8')
            logger.info(f"Loaded configuration from {_config_path}")
        else:
            logger.warning(f"Configuration file not found: {_config_path}")
    
    return _config


def get_config_value(section: str, key: str, fallback: Any = None) -> Any:
    """
    Get configuration value from system.ini.
    
    Args:
        section: Configuration section (e.g., 'application', 'rag')
        key: Configuration key (e.g., 'APP_VERSION', 'TOP_K_DOCUMENTS')
        fallback: Default value if key not found
    
    Returns:
        Configuration value or fallback
    
    Example:
        >>> get_config_value('application', 'APP_VERSION', '0.0.0')
        '0.2.0'
    """
    config = _load_config()
    
    try:
        if section in config and key in config[section]:
            value = config[section][key]
            
            # Type conversion based on value
            if value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            
            try:
                # Try integer
                return int(value)
            except ValueError:
                try:
                    # Try float
                    return float(value)
                except ValueError:
                    # Return as string
                    return value
        else:
            logger.debug(f"Config key [{section}].{key} not found, using fallback: {fallback}")
            return fallback
    
    except Exception as e:
        logger.error(f"Error reading config [{section}].{key}: {e}")
        return fallback


def reload_config() -> None:
    """Force reload of configuration from system.ini."""
    global _config
    _config = None
    logger.info("Configuration reloaded")
