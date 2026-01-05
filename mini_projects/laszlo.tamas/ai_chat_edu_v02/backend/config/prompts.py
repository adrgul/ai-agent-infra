"""
System Prompt Configuration
Hierarchical prompt system: Application → Tenant → User
"""

import configparser
import os
from pathlib import Path

# Load system.ini configuration
_config = configparser.ConfigParser()
_config_path = Path(__file__).parent / "system.ini"

if not _config_path.exists():
    raise FileNotFoundError(f"Configuration file not found: {_config_path}")

_config.read(_config_path, encoding='utf-8')

# Application-level system prompt (loaded from system.ini)
APPLICATION_SYSTEM_PROMPT = _config.get("application", "SYSTEM_PROMPT", fallback="""You are a helpful AI assistant in a multi-tenant internal chat system.
- Always maintain professional tone
- Prioritize user privacy and data security
- Follow company policies and guidelines
- Provide helpful, accurate, and concise responses
- This is a production environment - be careful with sensitive information

IMPORTANT: When answering questions about the USER'S PERSONAL INFORMATION (their name, email, role), 
use the information from the "CURRENT USER" section below. DO NOT search documents for this information.
Documents contain domain knowledge and uploaded content - they do NOT contain the current user's personal data.""")

# Chat history handling instructions
CHAT_HISTORY_INSTRUCTIONS = _config.get("application", "CHAT_HISTORY_INSTRUCTIONS", fallback="")


def build_system_prompt(
    user_context: dict,
    tenant_prompt: str | None = None,
    user_prompt: str | None = None
) -> str:
    """
    Build a hierarchical system prompt by combining:
    1. Application-level prompt (global)
    2. Tenant-level prompt (company policy)
    3. User-level prompt (personal preferences)
    
    Args:
        user_context: User information (firstname, lastname, nickname, role, email, default_lang)
        tenant_prompt: Optional tenant-specific instructions
        user_prompt: Optional user-specific instructions
    
    Returns:
        Combined system prompt string
    """
    # Start with application-level prompt
    prompt_parts = [APPLICATION_SYSTEM_PROMPT]
    
    # Add tenant-level prompt if exists
    if tenant_prompt and tenant_prompt.strip():
        prompt_parts.append(f"\n\nCOMPANY POLICY:\n{tenant_prompt.strip()}")
    
    # Add user-level prompt if exists
    if user_prompt and user_prompt.strip():
        prompt_parts.append(f"\n\nUSER PREFERENCES:\n{user_prompt.strip()}")
    
    # Add user context (handle None safely)
    if user_context:
        user_lang = user_context.get('default_lang', 'en')
        lang_instruction = "Respond in Hungarian." if user_lang == 'hu' else "Respond in English."
        
        user_info = (
            f"\n\nCURRENT USER:\n"
            f"You are currently chatting with {user_context['firstname']} {user_context['lastname']} "
            f"(nickname: {user_context['nickname']}, role: {user_context['role']}, "
            f"email: {user_context['email']}, preferred language: {user_lang}).\n"
            f"{lang_instruction}"
        )
        
        prompt_parts.append(user_info)
    else:
        # No user context available
        prompt_parts.append("\n\nCURRENT USER:\nUnknown user. Respond in a friendly, general manner.")
    
    # Add chat history instructions at the end (cached part)
    if CHAT_HISTORY_INSTRUCTIONS and CHAT_HISTORY_INSTRUCTIONS.strip():
        prompt_parts.append(f"\n\nCHAT HISTORY INSTRUCTIONS:\n{CHAT_HISTORY_INSTRUCTIONS.strip()}")
    
    # Combine all parts
    return "\n".join(prompt_parts)


def build_system_prompt_structured(
    user_context: dict,
    tenant_prompt: str | None = None,
    user_prompt: str | None = None
) -> dict:
    """
    Build a hierarchical system prompt and return it as structured data for debugging.
    
    Returns:
        Dict with separate layers:
        {
            "application": str,
            "tenant": str | None,
            "user": str | None,
            "user_context": str,
            "combined": str
        }
    """
    # Application-level prompt
    application = APPLICATION_SYSTEM_PROMPT
    
    # Tenant-level prompt
    tenant = f"COMPANY POLICY:\n{tenant_prompt.strip()}" if tenant_prompt and tenant_prompt.strip() else None
    
    # User-level prompt
    user = f"USER PREFERENCES:\n{user_prompt.strip()}" if user_prompt and user_prompt.strip() else None
    
    # User context
    user_lang = user_context.get('default_lang', 'en')
    lang_instruction = "Respond in Hungarian." if user_lang == 'hu' else "Respond in English."
    
    user_context_text = (
        f"CURRENT USER:\n"
        f"You are currently chatting with {user_context['firstname']} {user_context['lastname']} "
        f"(nickname: {user_context['nickname']}, role: {user_context['role']}, "
        f"email: {user_context['email']}, preferred language: {user_lang}).\n"
        f"{lang_instruction}"
    )
    
    # Combined
    prompt_parts = [application]
    if tenant:
        prompt_parts.append(f"\n\n{tenant}")
    if user:
        prompt_parts.append(f"\n\n{user}")
    prompt_parts.append(f"\n\n{user_context_text}")
    
    combined = "\n".join(prompt_parts)
    
    return {
        "application": application,
        "tenant": tenant,
        "user": user,
        "user_context": user_context_text,
        "combined": combined
    }
