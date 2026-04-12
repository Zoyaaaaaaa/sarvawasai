/**
 * Legal Document Chat Component
 * Enables interactive Q&A on legal documents with conversation memory
 */

import React, { useState, useRef, useEffect } from 'react';
import './LegalDocumentChat.css';

const LegalDocumentChat = ({ docId, docContent, userId }) => {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState('english');
  const [error, setError] = useState(null);
  const [chatStarted, setChatStarted] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Start chat conversation
  const startChat = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/legal/chat/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_id: docId,
          user_id: userId,
          doc_content: docContent,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start chat');
      }

      const data = await response.json();
      setConversationId(data.conversation_id);
      setChatStarted(true);
      setMessages([
        {
          role: 'assistant',
          content:
            'Hello! I am your legal document expert. I can help you understand this legal document, answer questions about specific clauses, and highlight important points. What would you like to know?',
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Ask a question
  const handleAskQuestion = async (e) => {
    e.preventDefault();

    if (!question.trim()) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Add user question to messages
      const userMessage = {
        role: 'user',
        content: question,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setQuestion('');

      // Send to API
      const response = await fetch('/api/legal/chat/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: conversationId,
          question: question,
          language: language,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to get answer');
      }

      const data = await response.json();

      // Add assistant response to messages
      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        timestamp: data.timestamp,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err.message);
      setQuestion(''); // Clear question on error
    } finally {
      setLoading(false);
    }
  };

  // Clear conversation
  const handleClearChat = async () => {
    if (!conversationId) return;

    try {
      await fetch(`/api/legal/chat/clear/${conversationId}`, {
        method: 'DELETE',
      });
      setConversationId(null);
      setMessages([]);
      setChatStarted(false);
      setQuestion('');
      setError(null);
    } catch (err) {
      setError('Failed to clear chat');
    }
  };

  if (!chatStarted) {
    return (
      <div className="legal-chat-container legal-chat-start">
        <div className="legal-chat-start-content">
          <h2>Legal Document Chat</h2>
          <p>Ask questions about this legal document and get expert answers with conversation memory.</p>
          <button
            onClick={startChat}
            disabled={loading}
            className="legal-chat-btn legal-chat-btn-primary"
          >
            {loading ? 'Starting...' : 'Start Conversation'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="legal-chat-container">
      {/* Header */}
      <div className="legal-chat-header">
        <h3>Document Chat</h3>
        <div className="legal-chat-header-controls">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="legal-chat-select"
          >
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
            <option value="mixed">Mixed (English + Hindi)</option>
          </select>
          <button
            onClick={handleClearChat}
            className="legal-chat-btn legal-chat-btn-danger legal-chat-btn-small"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="legal-chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`legal-chat-message legal-chat-message-${msg.role}`}>
            <div className="legal-chat-message-avatar">
              {msg.role === 'user' ? '👤' : '⚖️'}
            </div>
            <div className="legal-chat-message-content">
              <div className="legal-chat-message-text">{msg.content}</div>
              <div className="legal-chat-message-time">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="legal-chat-message legal-chat-message-assistant">
            <div className="legal-chat-message-avatar">⚖️</div>
            <div className="legal-chat-message-content">
              <div className="legal-chat-typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="legal-chat-error">
          <span>⚠️ {error}</span>
          <button
            onClick={() => setError(null)}
            className="legal-chat-error-close"
          >
            ✕
          </button>
        </div>
      )}

      {/* Input Area */}
      <form onSubmit={handleAskQuestion} className="legal-chat-input-area">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about this legal document..."
          className="legal-chat-input"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="legal-chat-btn legal-chat-btn-primary"
        >
          {loading ? 'Sending...' : 'Ask'}
        </button>
      </form>

      {/* Info */}
      <div className="legal-chat-info">
        <p>💡 The chat maintains conversation memory, so follow-up questions understand previous context.</p>
      </div>
    </div>
  );
};

export default LegalDocumentChat;
