"""
Legal Document Chat API Routes
Endpoints for interactive Q&A on legal documents with conversation memory
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from ..services.legal_document_chat import get_chat_service, LegalDocumentChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/legal/chat", tags=["legal-chat"])


# ==================== REQUEST/RESPONSE MODELS ====================

class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="ISO format timestamp")


class StartChatRequest(BaseModel):
    """Request to start a new chat conversation"""
    doc_id: str = Field(..., description="ID of the legal document")
    user_id: str = Field(..., description="ID of the user")
    doc_content: str = Field(..., description="The legal document content")


class StartChatResponse(BaseModel):
    """Response when starting a chat conversation"""
    status: str = Field(default="success")
    conversation_id: str = Field(..., description="Unique conversation ID")
    message: str = Field(default="Chat session started successfully")


class AskQuestionRequest(BaseModel):
    """Request to ask a question in a chat"""
    conversation_id: str = Field(..., description="ID of the conversation")
    question: str = Field(..., description="Question about the legal document")
    language: str = Field(default="english", description="Response language")


class AskQuestionResponse(BaseModel):
    """Response to a question"""
    status: str = Field(default="success")
    conversation_id: str = Field(..., description="Conversation ID")
    question: str = Field(..., description="The asked question")
    answer: str = Field(..., description="Answer from AI")
    message_count: int = Field(..., description="Total messages in conversation")
    timestamp: str = Field(..., description="When the response was generated")


class ConversationHistoryResponse(BaseModel):
    """Full conversation history"""
    conversation_id: str = Field(...)
    doc_id: str = Field(...)
    user_id: str = Field(...)
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: str = Field(...)
    updated_at: str = Field(...)
    total_messages: int = Field(...)


# ==================== ROUTES ====================

@router.post("/start", response_model=StartChatResponse, status_code=201)
async def start_chat(request: StartChatRequest, service: LegalDocumentChatService = Depends(get_chat_service)):
    """
    Start a new chat conversation for a legal document.
    
    The document content is stored in memory along with conversation history.
    """
    try:
        if not request.doc_content.strip():
            raise HTTPException(
                status_code=400,
                detail="Document content cannot be empty"
            )
        
        conversation_id = service.create_conversation(
            doc_id=request.doc_id,
            user_id=request.user_id,
            doc_content=request.doc_content
        )
        
        return StartChatResponse(
            status="success",
            conversation_id=conversation_id,
            message="Chat session started successfully"
        )
    
    except Exception as e:
        logger.error(f"Error starting chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start chat: {str(e)}"
        )


@router.post("/ask", response_model=AskQuestionResponse, status_code=200)
async def ask_question(
    request: AskQuestionRequest,
    service: LegalDocumentChatService = Depends(get_chat_service)
):
    """
    Ask a question about the legal document.
    
    The system maintains conversation memory, so follow-up questions can reference previous context.
    """
    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )
        
        # Validate language
        valid_languages = ["english", "hindi", "mixed"]
        if request.language not in valid_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid language. Must be one of: {', '.join(valid_languages)}"
            )
        
        response = await service.ask_question(
            conversation_id=request.conversation_id,
            question=request.question,
            language=request.language
        )
        
        return AskQuestionResponse(**response)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error asking question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}"
        )


@router.get("/history/{conversation_id}", response_model=ConversationHistoryResponse, status_code=200)
async def get_chat_history(
    conversation_id: str,
    service: LegalDocumentChatService = Depends(get_chat_service)
):
    """
    Get the full conversation history for a chat session.
    """
    try:
        history = service.get_conversation_history(conversation_id)
        return ConversationHistoryResponse(**history)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.delete("/clear/{conversation_id}", status_code=204)
async def clear_chat(
    conversation_id: str,
    service: LegalDocumentChatService = Depends(get_chat_service)
):
    """
    Clear/delete a chat conversation.
    """
    try:
        success = service.clear_conversation(conversation_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found"
            )
        return None
    except Exception as e:
        logger.error(f"Error clearing chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear conversation: {str(e)}"
        )


@router.get("/health", status_code=200)
async def chat_health_check(service: LegalDocumentChatService = Depends(get_chat_service)):
    """
    Health check for legal document chat service.
    """
    return {
        "status": "healthy",
        "service": "Legal Document Chat",
        "model": service.model_id,
        "feature": "Interactive Q&A with conversation memory"
    }
