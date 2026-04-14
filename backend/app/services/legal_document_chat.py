"""
Legal Document Chat Service with Conversation Memory
Enables interactive Q&A on legal documents with context awareness and memory management
Supports both in-memory and MongoDB-persisted conversations
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from bson import ObjectId
import json
import uuid

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation history and context"""
    
    def __init__(self, doc_content: str, doc_id: str, user_id: str):
        self.doc_content = doc_content
        self.doc_id = doc_id
        self.user_id = user_id
        self.messages: List[Dict[str, str]] = []
        self.context_summary = ""
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.updated_at = datetime.now(timezone.utc)
    
    def get_conversation_history(self) -> str:
        """Format conversation history for context"""
        if not self.messages:
            return ""
        
        history = "Previous conversation:\n"
        for msg in self.messages[-10:]:  # Keep last 10 messages for context
            history += f"\n{msg['role'].upper()}: {msg['content']}"
        return history
    
    def get_system_prompt(self) -> str:
        """Get system prompt with context"""
        history = self.get_conversation_history()
        
        system_prompt = f"""You are an expert legal document analyzer specializing in Indian real estate law and contracts.

Your task is to:
1. Analyze the provided legal document carefully
2. Answer user questions about the document accurately
3. Provide context from the document to support your answers
4. Highlight any potential legal risks or important clauses
5. Explain legal terminology in simple terms
6. Remember the previous conversation context to provide consistent answers

LEGAL DOCUMENT CONTENT:
{self.doc_content}

{history}

Guidelines:
- Always cite specific sections or clauses from the document
- If information is not in the document, clearly state that
- Provide practical advice based on Indian real estate law
- Be careful with legal interpretations - advise consulting a lawyer for specific cases
- Keep responses clear and concise
"""
        return system_prompt


class LegalDocumentChatService:
    """Service for chat-based interaction with legal documents"""
    
    def __init__(self, api_key: Optional[str] = None):
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai package is required")
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.5-flash"
        self.conversations: Dict[str, ConversationMemory] = {}
    
    def create_conversation(self, doc_id: str, user_id: str, doc_content: str) -> str:
        """Create a new conversation session"""
        conversation_id = f"{user_id}_{doc_id}_{datetime.now(timezone.utc).timestamp()}"
        self.conversations[conversation_id] = ConversationMemory(doc_content, doc_id, user_id)
        logger.info(f"Created conversation {conversation_id}")
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationMemory]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    async def ask_question(
        self,
        conversation_id: str,
        question: str,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Ask a question about the legal document with conversation memory
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        try:
            # Build system prompt with conversation history
            system_prompt = conversation.get_system_prompt()
            
            # Add user question to history
            conversation.add_message("user", question)
            
            # Get previous messages for context
            messages_for_api = []
            for msg in conversation.messages[-5:]:  # Send last 5 messages to API
                messages_for_api.append({
                    "role": msg["role"],
                    "parts": [{"text": msg["content"]}]
                })
            
            # Call Gemini API
            response = self.client.models.generate_content_stream(
                model=self.model_id,
                contents=messages_for_api,
                system_instruction=system_prompt,
                config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                }
            )
            
            # Collect streamed response
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
            
            # Add assistant response to history
            conversation.add_message("assistant", full_response)
            
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "question": question,
                "answer": full_response,
                "message_count": len(conversation.messages),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error in ask_question: {str(e)}")
            raise
    
    def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """Get full conversation history"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        return {
            "conversation_id": conversation_id,
            "doc_id": conversation.doc_id,
            "user_id": conversation.user_id,
            "messages": conversation.messages,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "total_messages": len(conversation.messages)
        }
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Cleared conversation {conversation_id}")
            return True
        return False


# Global service instance
_chat_service: Optional[LegalDocumentChatService] = None


def get_chat_service() -> LegalDocumentChatService:
    """Get or initialize the legal document chat service"""
    global _chat_service
    if _chat_service is None:
        try:
            _chat_service = LegalDocumentChatService()
        except ImportError as e:
            logger.error(f"Failed to initialize chat service: {e}")
            raise
    return _chat_service
