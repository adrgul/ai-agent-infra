import logging
import os
from typing import List, Dict, Any
from openai import OpenAI

from database.db import (
    get_user_by_id,
    create_session,
    insert_message,
    get_session_messages
)

logger = logging.getLogger(__name__)


class ChatService:
    """Service layer for chat operations."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)
    
    def process_chat_message(self, user_id: int, session_id: str, message: str) -> str:
        """
        Process a chat message through the full pipeline:
        1. Validate user
        2. Load user record
        3. Load recent messages
        4. Build LLM context
        5. Call OpenAI
        6. Persist messages
        7. Return assistant response
        """
        # Step 1: Validate user exists and is active
        user = get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        if not user["is_active"]:
            raise ValueError(f"User {user['firstname']} {user['lastname']} is not active")
        
        logger.info(f"Processing message for user {user['nickname']} (ID: {user_id})")
        
        # Step 2: Check if session exists, if not create it
        try:
            create_session(session_id, user_id)
            logger.info(f"Created new session: {session_id}")
        except Exception:
            # Session might already exist, which is fine
            pass
        
        # Step 3: Load last N messages for this session
        recent_messages = get_session_messages(session_id, limit=20)
        
        # Step 4: Build LLM input context
        messages = self._build_llm_context(user, recent_messages, message)
        
        # Step 5: Persist user message BEFORE calling OpenAI
        insert_message(session_id, user_id, "user", message)
        
        # Step 6: Call OpenAI Chat Completion API
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            assistant_reply = response.choices[0].message.content
            logger.info(f"Received response from OpenAI: {len(assistant_reply)} chars")
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            error_message = "I apologize, but I'm having trouble connecting to the AI service. Please try again later."
            insert_message(session_id, user_id, "assistant", error_message)
            raise RuntimeError(error_message)
        
        # Step 7: Persist assistant response
        insert_message(session_id, user_id, "assistant", assistant_reply)
        
        return assistant_reply
    
    def _build_llm_context(
        self, 
        user: Dict[str, Any], 
        recent_messages: List[Dict[str, Any]], 
        current_message: str
    ) -> List[Dict[str, str]]:
        """Build the message context for OpenAI API."""
        # System message with user identity
        user_lang = user.get('default_lang', 'en')
        lang_instruction = "Respond in Hungarian." if user_lang == 'hu' else "Respond in English."
        
        system_message = {
            "role": "system",
            "content": (
                f"You are a helpful AI assistant in a test-mode internal chat system. "
                f"You are currently chatting with {user['firstname']} {user['lastname']} "
                f"(nickname: {user['nickname']}, role: {user['role']}, email: {user['email']}, preferred language: {user_lang}). "
                f"{lang_instruction} Provide helpful, concise responses. This is a test environment."
            )
        }
        
        # Build message history
        messages = [system_message]
        
        # Add recent messages (excluding the current one we're about to send)
        for msg in recent_messages:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages
    
    def generate_user_summary(self, user_id: int, messages: List[Dict[str, Any]]) -> str:
        """
        Generate an AI summary of what we know about the user based on conversation history.
        """
        if not messages:
            return "Nincs még beszélgetési előzmény."
        
        # Build context from messages
        conversation_text = ""
        for msg in messages[-20:]:  # Last 20 messages
            role_label = "Felhasználó" if msg["role"] == "user" else "Asszisztens"
            conversation_text += f"{role_label}: {msg['content']}\n"
        
        # Call OpenAI to generate summary
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Készíts egy rövid összefoglalót (3-5 mondat) arról, hogy mit tudunk a felhasználóról a beszélgetési előzmények alapján. Milyen témákról beszélt, milyen érdeklődési köre van, stb. Magyar nyelven válaszolj."
                    },
                    {
                        "role": "user",
                        "content": f"Beszélgetési előzmények:\n\n{conversation_text}"
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content or "Nem sikerült összefoglalót generálni."
        except Exception as e:
            logger.error(f"Failed to generate user summary: {e}")
            return f"Hiba az összefoglaló generálása során: {str(e)}"
