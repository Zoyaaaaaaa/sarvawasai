"""
Complete Housing Scheme Advisor with LangGraph Memory Management and TTS
Single file implementation with all features integrated
"""

import os
import re
import json
import base64
import asyncio
import unicodedata
import websockets
from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass
from dotenv import load_dotenv

# LangChain and LangGraph imports
from langgraph.graph import MessagesState, StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage, AIMessage
from langchain_tavily import TavilySearch

# FastAPI imports
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
import io
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# ==================== CONFIGURATION ====================

# API Keys
MURF_API_KEY = os.getenv("MURF_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# TTS Configuration
MURF_WS_URL = "wss://api.murf.ai/v1/speech/stream-input"
SAMPLE_RATE = 24000

# ==================== LANGUAGE DETECTION ====================

class LanguageDetector:
    """Intelligent language detection for Indian languages and English"""
    
    LANGUAGE_PATTERNS = {
        'hindi': {
            'pattern': r'[\u0900-\u097F]',
            'voice_id': 'en-IN-aarav',
            'name': 'Hindi',
            'code': 'hi'
        },
        'tamil': {
            'pattern': r'[\u0B80-\u0BFF]',
            'voice_id': 'ta-IN-iniya',
            'name': 'Tamil',
            'code': 'ta'
        },
        'telugu': {
            'pattern': r'[\u0C00-\u0C7F]',
            'voice_id': 'en-IN-aarav',
            'name': 'Telugu',
            'code': 'te'
        },
        'bengali': {
            'pattern': r'[\u0980-\u09FF]',
            'voice_id': 'en-IN-aarav',
            'name': 'Bengali',
            'code': 'bn'
        },
        'gujarati': {
            'pattern': r'[\u0A80-\u0AFF]',
            'voice_id': 'en-IN-aarav',
            'name': 'Gujarati',
            'code': 'gu'
        },
        'punjabi': {
            'pattern': r'[\u0A00-\u0A7F]',
            'voice_id': 'en-IN-aarav',
            'name': 'Punjabi',
            'code': 'pa'
        },
        'kannada': {
            'pattern': r'[\u0C80-\u0CFF]',
            'voice_id': 'en-IN-aarav',
            'name': 'Kannada',
            'code': 'kn'
        },
        'malayalam': {
            'pattern': r'[\u0D00-\u0D7F]',
            'voice_id': 'en-IN-aarav',
            'name': 'Malayalam',
            'code': 'ml'
        },
        'english': {
            'pattern': r'^[a-zA-Z\s.,!?\'"()-]+$',
            'voice_id': 'en-US-amara',
            'name': 'English',
            'code': 'en'
        }
    }
    
    @classmethod
    def detect_language(cls, text: str) -> Tuple[str, Dict]:
        """
        Detect language from text and return language info
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (language_key, language_config)
        """
        if not text.strip():
            return 'english', cls.LANGUAGE_PATTERNS['english']
        
        # Count matches for each language
        scores = {}
        for lang_key, lang_config in cls.LANGUAGE_PATTERNS.items():
            pattern = lang_config['pattern']
            matches = re.findall(pattern, text)
            scores[lang_key] = len(matches)
        
        # Find language with highest score
        detected_lang = max(scores.items(), key=lambda x: x[1])
        
        # If no specific language detected, check for English
        if detected_lang[1] == 0:
            # Check if text is primarily Latin script
            latin_chars = sum(1 for char in text if unicodedata.category(char).startswith('L') 
                            and ord(char) < 256)
            total_chars = sum(1 for char in text if unicodedata.category(char).startswith('L'))
            
            if total_chars > 0 and latin_chars / total_chars > 0.8:
                detected_lang = ('english', scores['english'])
        
        # Default to the language with most matches, fallback to English
        lang_key = detected_lang[0] if detected_lang[1] > 0 else 'english'
        return lang_key, cls.LANGUAGE_PATTERNS[lang_key]


# ==================== TTS ENGINE ====================

class MultilingualTTS:
    """Enhanced TTS class with language detection and streaming"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.detector = LanguageDetector()
        
    async def generate_audio(self, 
                           text: str, 
                           style: str = "Conversational",
                           rate: int = 0,
                           pitch: int = 0,
                           variation: int = 1,
                           auto_detect: bool = True) -> bytes:
        """
        Convert text to speech with automatic language detection
        
        Args:
            text: Text to convert
            style: Speaking style
            rate: Speech rate (-50 to 50)
            pitch: Voice pitch (-20 to 20)
            variation: Voice variation (1 to 5)
            auto_detect: Whether to auto-detect language
            
        Returns:
            Audio bytes in WAV format
        """
        
        if not text.strip():
            raise ValueError("No text provided")
            
        # Detect language
        lang_key, lang_config = self.detector.detect_language(text)
        voice_id = lang_config['voice_id']
        lang_name = lang_config['name']
        
        print(f"🌍 Detected Language: {lang_name}")
        print(f"🎤 Using Voice: {voice_id}")
        
        # Connect to WebSocket
        ws_url = f"{MURF_WS_URL}?api-key={self.api_key}&sample_rate={SAMPLE_RATE}&channel_type=MONO&format=WAV"
        
        async with websockets.connect(ws_url) as ws:
            # Send voice configuration
            voice_config_msg = {
                "voice_config": {
                    "voiceId": voice_id,
                    "style": style,
                    "rate": rate,
                    "pitch": pitch,
                    "variation": variation
                }
            }
            
            await ws.send(json.dumps(voice_config_msg))
            
            # Send text
            text_msg = {
                "text": text,
                "end": True
            }
            
            await ws.send(json.dumps(text_msg))
            
            # Collect audio data
            audio_data = bytearray()
            first_chunk = True
            
            try:
                while True:
                    response = await ws.recv()
                    data = json.loads(response)
                    
                    if "audio" in data:
                        chunk_data = base64.b64decode(data["audio"])
                        
                        # Skip WAV header for first chunk only
                        if first_chunk and len(chunk_data) > 44:
                            chunk_data = chunk_data[44:]
                            first_chunk = False
                        
                        audio_data.extend(chunk_data)
                    
                    if data.get("final"):
                        break
                        
            except Exception as e:
                print(f"❌ Error during audio generation: {e}")
                raise
                
            return bytes(audio_data)


# ==================== USER PROFILE ====================

@dataclass
class UserProfile:
    """User profile information"""
    income: str = ""
    category: str = ""
    location: str = ""
    employment: str = ""
    language: str = "English"
    
    def to_dict(self):
        return {
            "income": self.income,
            "category": self.category,
            "location": self.location,
            "employment": self.employment,
            "language": self.language
        }
    
    def update(self, **kwargs):
        """Update profile with new information"""
        for key, value in kwargs.items():
            if hasattr(self, key) and value:
                setattr(self, key, value)


# ==================== LANGGRAPH STATE ====================

class HousingAdvisorState(MessagesState):
    """Extended state with user profile and conversation summary"""
    summary: str
    user_profile: dict


# ==================== HOUSING SCHEME ADVISOR ====================

class HousingSchemeAdvisor:
    """
    Complete Housing Scheme Advisor with:
    - LangGraph conversation memory management
    - Automatic summarization
    - User profile tracking
    - Multilingual support
    - Text-to-Speech integration
    - Real-time scheme search
    """
    
    SYSTEM_PROMPT = """You are an expert Housing Scheme Advisor for India, fluent in both English and Hindi. 

**Your Role:**
- Help users find suitable government housing schemes from myscheme.gov.in
- Provide clear, actionable information in the user's preferred language
- Be conversational, friendly, and empathetic
- Always include official links when available

**Response Format (Use Markdown):**

## 🏠 [Scheme Name]

### 📋 Overview
Brief description of the scheme

### ✅ Eligibility
- Who can apply
- Income criteria
- Category requirements

### 💰 Benefits
- Financial assistance amount
- Subsidy details
- Additional benefits

### 📝 Application Process
1. Step-by-step guide
2. How to apply
3. Where to apply

### 📄 Required Documents
- List of documents needed

### 🔗 Official Link
[Apply Here](actual_url)

**Context:**
{conversation_context}

**User Profile:**
- Income: {income}
- Category: {category}
- Location: {location}
- Employment: {employment}
- Language: {language}

**Guidelines:**
- Match language to user (Hindi/English)
- Use markdown formatting
- Include emojis for readability
- Provide working links from myscheme.gov.in
- Be conversational and supportive
- Use search when needed for current schemes
"""

    def __init__(
        self, 
        model_name: str = "llama-3.3-70b-versatile",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        summarize_threshold: int = 8,
        enable_tts: bool = False
    ):
        """
        Initialize the Housing Scheme Advisor
        
        Args:
            model_name: The Groq model to use
            temperature: LLM temperature (0-1)
            max_tokens: Maximum tokens per response
            summarize_threshold: Number of messages before summarization
            enable_tts: Whether to enable text-to-speech
        """
        # Initialize LLM
        self.llm = ChatGroq(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Initialize search tool
        self.search_tool = TavilySearch(
            max_results=5,
            include_domains=["myscheme.gov.in"],
            search_depth="advanced"
        )
        
        # TTS engine
        self.enable_tts = enable_tts
        if enable_tts and MURF_API_KEY:
            self.tts_engine = MultilingualTTS(MURF_API_KEY)
        else:
            self.tts_engine = None
        
        # Configuration
        self.summarize_threshold = summarize_threshold
        self.checkpointer = InMemorySaver()
        
        # Build the graph
        self.graph = self._build_graph()
        
    def _build_graph(self):
        """Build the LangGraph conversation graph"""
        
        builder = StateGraph(HousingAdvisorState)
        
        # Add nodes
        builder.add_node("chat", self._chat_node)
        builder.add_node("summarize", self._summarize_conversation)
        
        # Define flow
        builder.add_edge(START, "chat")
        builder.add_conditional_edges(
            "chat",
            self._should_summarize,
            {
                "summarize": "summarize",
                "__end__": "__end__",
            }
        )
        builder.add_edge("summarize", "__end__")
        
        return builder.compile(checkpointer=self.checkpointer)
    
    def _summarize_conversation(self, state: HousingAdvisorState):
        """Create or extend conversation summary"""
        
        existing_summary = state.get("summary", "")
        
        if existing_summary:
            prompt = (
                f"Existing summary:\n{existing_summary}\n\n"
                "Extend the summary with the new conversation above. "
                "Focus on:\n"
                "- User's updated housing requirements\n"
                "- Schemes discussed and user's interest\n"
                "- Any decisions or next steps mentioned\n"
                "- Important details about eligibility or documentation"
            )
        else:
            prompt = (
                "Create a concise summary of this conversation focusing on:\n"
                "- User's housing needs and preferences\n"
                "- Their financial situation and eligibility\n"
                "- Schemes discussed and which ones interested them\n"
                "- Any concerns or questions raised\n"
                "- Next steps or pending actions"
            )
        
        messages_for_summary = state["messages"] + [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages_for_summary)
        
        # Keep last 4 messages (2 exchanges) and remove older ones
        messages_to_delete = state["messages"][:-4]
        
        return {
            "summary": response.content,
            "messages": [RemoveMessage(id=m.id) for m in messages_to_delete],
        }
    
    def _chat_node(self, state: HousingAdvisorState):
        """Main chat processing node"""
        
        # Build conversation context
        conversation_context = ""
        if state.get("summary"):
            conversation_context = f"**Previous Conversation:**\n{state['summary']}\n"
        
        # Get user profile
        profile = state.get("user_profile", {})
        
        # Create system message
        system_content = self.SYSTEM_PROMPT.format(
            conversation_context=conversation_context,
            income=profile.get("income", "Not provided"),
            category=profile.get("category", "Not provided"),
            location=profile.get("location", "Not provided"),
            employment=profile.get("employment", "Not provided"),
            language=profile.get("language", "English")
        )
        
        messages = [SystemMessage(content=system_content)]
        messages.extend(state["messages"])
        
        # Generate response
        response = self.llm.invoke(messages)
        
        return {"messages": [response]}
    
    def _should_summarize(self, state: HousingAdvisorState) -> Literal["summarize", "__end__"]:
        """Determine if conversation should be summarized"""
        return "summarize" if len(state["messages"]) > self.summarize_threshold else "__end__"
    
    def create_session(self, session_id: str) -> dict:
        """Create a session configuration"""
        return {"configurable": {"thread_id": session_id}}
    
    def chat(
        self, 
        message: str, 
        session_id: str,
        user_profile: Optional[UserProfile] = None,
        return_audio: bool = False
    ) -> Dict:
        """
        Send a message and get a response
        
        Args:
            message: User's message
            session_id: Session identifier
            user_profile: Optional user profile information
            return_audio: Whether to generate audio response
            
        Returns:
            Dictionary with response text and optional audio
        """
        config = self.create_session(session_id)
        
        input_data = {
            "messages": [HumanMessage(content=message)],
            "summary": ""
        }
        
        if user_profile:
            input_data["user_profile"] = user_profile.to_dict()
        
        result = self.graph.invoke(input_data, config=config)
        
        # Extract the last AI message
        response_text = None
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                response_text = msg.content
                break
        
        if not response_text:
            response_text = "I apologize, but I couldn't generate a response. Please try again."
        
        # Generate audio if requested
        audio_data = None
        if return_audio and self.tts_engine:
            try:
                audio_data = asyncio.run(self.tts_engine.generate_audio(response_text))
            except Exception as e:
                print(f"TTS Error: {e}")
        
        return {
            "text": response_text,
            "audio": audio_data,
            "audio_base64": base64.b64encode(audio_data).decode() if audio_data else None
        }
    
    def get_conversation_state(self, session_id: str) -> dict:
        """Get the current state of a conversation"""
        config = self.create_session(session_id)
        snap = self.graph.get_state(config)
        vals = snap.values
        
        return {
            "summary": vals.get("summary", ""),
            "message_count": len(vals.get("messages", [])),
            "user_profile": vals.get("user_profile", {}),
            "messages": [
                {
                    "type": type(m).__name__,
                    "content": m.content[:100] + "..." if len(m.content) > 100 else m.content
                }
                for m in vals.get("messages", [])[-4:]
            ]
        }
    
    async def generate_audio_for_text(
        self, 
        text: str, 
        style: str = "Conversational",
        rate: int = 0,
        pitch: int = 0
    ) -> bytes:
        """Generate audio for any text"""
        if not self.tts_engine:
            raise ValueError("TTS is not enabled")
        return await self.tts_engine.generate_audio(text, style, rate, pitch)


# ==================== INITIALIZATION ====================

# Create router for FastAPI
router = APIRouter(prefix="/schemes", tags=["Housing Schemes"])

# Initialize Global Advisor instance for web routes
advisor = HousingSchemeAdvisor(
    model_name="llama-3.3-70b-versatile",
    temperature=0.3,
    enable_tts=True if MURF_API_KEY else False
)


# ==================== PYDANTIC MODELS (for API) ====================

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str
    user_details: Optional[Dict] = None
    language: Optional[str] = "en"
    session_id: Optional[str] = None
    return_audio: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str
    audio_base64: Optional[str] = None
    status: str = "success"
    session_id: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    style: Optional[str] = "Conversational"
    rate: Optional[int] = 0
    pitch: Optional[int] = 0


class LanguageDetectRequest(BaseModel):
    text: str


# ==================== WEB ROUTES ====================

@router.get("/")
async def get_schemes_info():
    return {
        "message": "Housing Scheme Advisor API",
        "status": "active",
        "features": [
            "LangGraph memory management",
            "Automatic summarization",
            "Multilingual support",
            "Text-to-Speech integration"
        ]
    }

@router.post("/chat", response_model=ChatResponse)
async def chat_with_advisor(request: ChatRequest):
    """Chat with the housing advisor"""
    try:
        session_id = request.session_id or f"web_{datetime.now().timestamp()}"
        
        # Create profile from request
        profile = None
        if request.user_details:
            profile = UserProfile(**request.user_details)
            if request.language:
                profile.language = "Hindi" if request.language == "hi" else "English"
        
        # Run advisor chat
        result = advisor.chat(
            message=request.query,
            session_id=session_id,
            user_profile=profile,
            return_audio=request.return_audio
        )
        
        return ChatResponse(
            response=result["text"],
            audio_base64=result["audio_base64"],
            session_id=session_id,
            status="success"
        )
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech"""
    try:
        audio_data = await advisor.generate_audio_for_text(
            text=request.text,
            style=request.style,
            rate=request.rate,
            pitch=request.pitch
        )
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav"
        )
    except Exception as e:
        print(f"Error in TTS endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-language")
async def detect_lang(request: LanguageDetectRequest):
    """Detect language of text"""
    try:
        # Use advisor's tts_engine if available, otherwise use a new detector instance
        if advisor.tts_engine:
            lang_key, lang_config = advisor.tts_engine.detector.detect_language(request.text)
        else:
            detector = LanguageDetector()
            lang_key, lang_config = detector.detect_language(request.text)
            
        return {
            "detected_language": lang_key,
            "language_name": lang_config['name'],
            "code": lang_config['code']
        }
    except Exception as e:
        print(f"Error in language detection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/state/{session_id}")
async def get_state(session_id: str):
    """Get conversation state"""
    try:
        return advisor.get_conversation_state(session_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found or error: {str(e)}")


# ==================== CLI INTERFACE ====================

def interactive_cli():
    """Interactive command-line interface"""
    
    print("\n" + "="*70)
    print("🏠  INDIAN HOUSING SCHEME ADVISOR  🏠")
    print("="*70)
    print("With LangGraph Memory Management + TTS Support")
    print("="*70 + "\n")
    
    # Check API keys
    if not GROQ_API_KEY:
        print("⚠️  Warning: GROQ_API_KEY not found!")
        return
    
    # Collect user profile
    print("📋 Let's start by collecting some basic information:\n")
    
    income = input("💰 Your annual income: ").strip()
    category = input("👥 Category (General/SC/ST/OBC/EWS): ").strip()
    location = input("📍 Your location/city: ").strip()
    employment = input("💼 Employment type: ").strip()
    
    language_choice = input("🌐 Language (1=English, 2=Hindi): ").strip()
    language = "Hindi" if language_choice == "2" else "English"
    
    enable_tts = input("🔊 Enable text-to-speech? (y/n): ").strip().lower() == 'y'
    
    profile = UserProfile(
        income=income or "Not provided",
        category=category or "Not provided",
        location=location or "Not provided",
        employment=employment or "Not provided",
        language=language
    )
    
    print("\n" + "─"*70)
    print("📊 Your Profile:")
    for key, value in profile.to_dict().items():
        print(f"   {key.title()}: {value}")
    print("─"*70 + "\n")
    
    # Initialize advisor
    print("🔄 Initializing advisor...")
    advisor = HousingSchemeAdvisor(
        model_name="llama-3.3-70b-versatile",
        temperature=0.3,
        summarize_threshold=8,
        enable_tts=enable_tts and bool(MURF_API_KEY)
    )
    print("✅ Advisor ready!\n")
    
    session_id = "interactive_session"
    
    print("💡 Commands: /help, /profile, /state, /quit")
    print("="*70 + "\n")
    
    # Main loop
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                if user_input in ['/quit', '/exit']:
                    print("\n👋 Thank you for using Housing Scheme Advisor!\n")
                    break
                elif user_input == '/help':
                    print("\n📖 Available commands:")
                    print("  /profile - View your profile")
                    print("  /state   - Show conversation state")
                    print("  /quit    - Exit application\n")
                    continue
                elif user_input == '/profile':
                    print("\n📊 Your Profile:")
                    for key, value in profile.to_dict().items():
                        print(f"   {key.title()}: {value}")
                    print()
                    continue
                elif user_input == '/state':
                    state = advisor.get_conversation_state(session_id)
                    print("\n📊 Conversation State:")
                    print(f"   Messages: {state['message_count']}")
                    print(f"   Has summary: {'Yes' if state['summary'] else 'No'}")
                    if state['summary']:
                        print(f"   Summary: {state['summary'][:100]}...")
                    print()
                    continue
            
            # Process message
            print("\n🤖 Advisor: (Thinking...)", end="\r", flush=True)
            
            response = advisor.chat(
                user_input,
                session_id,
                profile,
                return_audio=enable_tts
            )
            
            print("\r🤖 Advisor:                    ")
            print(response['text'])
            
            if response.get('audio'):
                print("🔊 [Audio generated - would play here in a GUI app]")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted! Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


# ==================== MAIN ====================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  HOUSING SCHEME ADVISOR")
    print("  LangGraph + Memory Management + TTS")
    print("="*70)
    
    print("\nFeatures:")
    print("✅ Conversation memory with automatic summarization")
    print("✅ Multilingual support (English + 8 Indian languages)")
    print("✅ Text-to-Speech integration")
    print("✅ Real-time scheme search")
    print("✅ User profile tracking")
    
    print("\nSelect mode:")
    print("1. Interactive CLI")
    print("2. Quick demo")
    
    choice = input("\nEnter choice (1-2): ").strip()
    
    if choice == "1":
        interactive_cli()
    elif choice == "2":
        # Quick demo
        print("\n🚀 Running quick demo...\n")
        
        advisor = HousingSchemeAdvisor(
            summarize_threshold=4  # Low threshold for demo
        )
        
        user = UserProfile(
            income="5 lakhs per year",
            category="General",
            location="Mumbai",
            language="English"
        )
        
        queries = [
            "I need affordable housing in Mumbai",
            "What is PMAY?",
            "Am I eligible?",
            "What documents do I need?",
            "How do I apply?",
        ]
        
        session_id = "demo"
        
        for i, query in enumerate(queries, 1):
            print(f"Turn {i}: {query}")
            response = advisor.chat(query, session_id, user)
            print(f"Response: {response['text'][:200]}...\n")
            
            if i == 3:
                state = advisor.get_conversation_state(session_id)
                print(f"[State: {state['message_count']} messages, "
                      f"Summary: {'Yes' if state['summary'] else 'No'}]\n")
        
        print("✅ Demo complete!")
    else:
        print("Invalid choice!")
