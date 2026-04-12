# Legal Document Chat Feature - Implementation Guide

## Overview

The Legal Document Chat feature enables users to have interactive conversations about legal documents with context-aware responses and conversation memory. Users can ask follow-up questions, and the system maintains the conversation history to provide consistent, context-aware answers.

## Features

✅ **Conversation Memory** - Maintains dialog history across multiple messages  
✅ **Context Awareness** - Follow-up questions understand previous conversation context  
✅ **Multi-language Support** - English, Hindi, and mixed language responses  
✅ **Expert Analysis** - Focused on Indian real estate law and contracts  
✅ **Session Management** - Start, continue, and clear chat conversations  
✅ **Real-time Responses** - Streaming responses from Gemini AI  

---

## Backend Implementation

### 1. Chat Service (`backend/app/services/legal_document_chat.py`)

The core service manages conversation memory and AI interactions:

```python
class ConversationMemory:
    """Manages conversation history and context"""
    - add_message(role, content)      # Add user/assistant message
    - get_history()                    # Get formatted history
    - get_system_prompt()              # Generate context-aware prompt

class LegalDocumentChatService:
    """Service for chat interactions"""
    - create_conversation()            # Start new session
    - ask_question()                   # Process questions with memory
    - get_conversation_history()       # Retrieve full history
    - clear_conversation()             # Delete session
```

### 2. API Routes (`backend/app/routes/legal_chat.py`)

**Endpoints:**

#### Start Chat Conversation
```
POST /api/legal/chat/start

Request:
{
  "doc_id": "document_123",
  "user_id": "user_456",
  "doc_content": "Full PDF text content..."
}

Response:
{
  "status": "success",
  "conversation_id": "user_456_document_123_timestamp",
  "message": "Chat session started successfully"
}
```

#### Ask Question
```
POST /api/legal/chat/ask

Request:
{
  "conversation_id": "session_id",
  "question": "What are the key terms of this agreement?",
  "language": "english"
}

Response:
{
  "status": "success",
  "conversation_id": "session_id",
  "question": "...",
  "answer": "The agreement contains the following key terms...",
  "message_count": 3,
  "timestamp": "2024-04-12T10:30:00Z"
}
```

#### Get Conversation History
```
GET /api/legal/chat/history/{conversation_id}

Response:
{
  "conversation_id": "session_id",
  "doc_id": "document_123",
  "user_id": "user_456",
  "messages": [
    {
      "role": "user",
      "content": "Question?",
      "timestamp": "2024-04-12T10:25:00Z"
    },
    {
      "role": "assistant",
      "content": "Answer...",
      "timestamp": "2024-04-12T10:25:05Z"
    }
  ],
  "created_at": "2024-04-12T10:20:00Z",
  "updated_at": "2024-04-12T10:30:00Z",
  "total_messages": 3
}
```

#### Clear Chat Session
```
DELETE /api/legal/chat/clear/{conversation_id}

Response: 204 No Content
```

---

## Frontend Implementation

### React Component (`frontend/src/components/LegalDocumentChat.jsx`)

**Features:**
- Clean chat interface with message history
- Real-time message streaming
- Language selection (English, Hindi, Mixed)
- Error handling and loading states
- Auto-scroll to latest messages
- Clear conversation option

**Integration Example:**

```jsx
import LegalDocumentChat from '@/components/LegalDocumentChat';

export default function LegalPage() {
  const documentContent = "Your PDF content here...";
  const docId = "doc_123";
  const userId = "user_456";

  return (
    <div>
      <h1>Legal Document Analysis</h1>
      
      {/* Your existing analysis component */}
      
      {/* Add Chat Interface */}
      <LegalDocumentChat 
        docId={docId}
        docContent={documentContent}
        userId={userId}
      />
    </div>
  );
}
```

### Component Props

| Prop | Type | Description |
|------|------|-------------|
| `docId` | string | Unique identifier for the document |
| `docContent` | string | Full text content of the legal document |
| `userId` | string | ID of the current user |

### UI Components

1. **Start Screen** - Button to initiate chat
2. **Chat Interface** - Message display and input area
3. **Header** - Language selector and clear button
4. **Messages** - User and assistant messages with timestamps
5. **Input Area** - Question input with submit button
6. **Info Footer** - Feature information and tips

---

## How It Works

### Conversation Memory Flow

```
1. User starts chat
   └─> Creates conversation with document content

2. User asks question
   ├─> Question added to message history
   ├─> System builds context with last 10 messages
   ├─> API request with conversation ID + question
   ├─> AI responds with context awareness
   └─> Response added to history

3. Follow-up question
   ├─> System provides previous messages as context
   ├─> AI remembers earlier discussion
   └─> Consistent and coherent answers
```

### Memory Management

- **Last 10 Messages** - Used for context in API calls
- **Full History** - Stored in service memory (in-session)
- **Conversation ID** - Unique per document per user per session
- **Timestamps** - All messages timestamped for tracking

---

## System Prompts

The service automatically generates context-aware system prompts:

```
You are an expert legal document analyzer specializing in Indian real estate law.

Your task is to:
1. Analyze the provided legal document carefully
2. Answer user questions about the document accurately
3. Provide context from the document
4. Highlight potential legal risks
5. Explain legal terminology in simple terms
6. Remember the previous conversation context

[LEGAL DOCUMENT CONTENT]

[PREVIOUS CONVERSATION]

Guidelines:
- Always cite specific sections or clauses
- If information is not in the document, state that clearly
- Provide practical advice based on Indian real estate law
- Be careful with legal interpretations
```

---

## Usage Example

### Backend Setup

1. **Environment Variables** (`.env`):
```
GOOGLE_API_KEY=your_api_key_here
ENV=development  # or production
```

2. **Install Dependencies** (already in `requirements.txt`):
```
google-genai
langchain
fastapi
```

3. **Server runs with**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Usage

```jsx
import LegalDocumentChat from '@/components/LegalDocumentChat';

function LegalAnalyzeView() {
  const [pdfText, setPdfText] = useState("");
  
  const handlePdfUpload = (content) => {
    setPdfText(content);
  };

  return (
    <div>
      {/* Analysis component */}
      
      {/* Chat interface */}
      {pdfText && (
        <LegalDocumentChat 
          docId="rental_agreement_2024"
          docContent={pdfText}
          userId="user@example.com"
        />
      )}
    </div>
  );
}
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `GOOGLE_API_KEY not set` | Missing API key | Set in environment |
| `Conversation not found` | Invalid ID | Start new conversation |
| `Question cannot be empty` | Empty question | Provide valid question |
| `Document content empty` | No document | Upload/select document |

### Error Responses

```json
{
  "detail": "Failed to process question: error message"
}
```

---

## Performance Considerations

1. **Message Context** - Limited to last 10 messages to balance context vs. performance
2. **Response Streaming** - Real-time chunked responses for better UX
3. **Memory Storage** - In-memory (session-scoped) vs. MongoDB (to be implemented)
4. **Concurrent Conversations** - Each session is isolated

---

## Security Notes

1. **API Keys** - Never expose GOOGLE_API_KEY in frontend
2. **User ID** - Use authenticated user IDs to track ownership
3. **Document Privacy** - Conversations are session-scoped, not persisted by default
4. **Rate Limiting** - Implement rate limits for production use

---

## Future Enhancements

- [ ] MongoDB persistence for chat history
- [ ] User chat archive/search
- [ ] Document indexing for faster analysis
- [ ] Multi-document conversations
- [ ] Chat export (PDF/CSV)
- [ ] Collaborative chat sessions
- [ ] Advanced memory management with summarization
- [ ] Integration with email/notifications

---

## Testing

### Backend Tests

```bash
# Test chat endpoint
curl -X POST http://localhost:8000/api/legal/chat/start \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "test_doc",
    "user_id": "test_user",
    "doc_content": "Sample legal document content..."
  }'

# Ask a question
curl -X POST http://localhost:8000/api/legal/chat/ask \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conversation_id",
    "question": "What are the main clauses?",
    "language": "english"
  }'
```

### Frontend Testing

- Test with sample legal documents
- Verify message history persistence
- Test language switching
- Test error scenarios
- Test mobile responsiveness

---

## Deployment

1. **Ensure bcrypt is installed**:
```bash
pip install bcrypt cffi
```

2. **Set environment variables** in Render/deployment platform:
```
GOOGLE_API_KEY=your_key
MONGODB_URL=optional_mongo_connection
ENV=production
```

3. **Backend runs on**:
```
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

---

## Support & Debugging

- Check server logs for import errors
- Verify GOOGLE_API_KEY is valid
- Ensure document content is not empty
- Check browser console for frontend errors
- Validate JSON payloads in API requests

---

**Last Updated**: April 12, 2024  
**Status**: Production Ready
