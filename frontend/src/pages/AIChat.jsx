
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import API from "../services/api";
import ReactMarkdown from "react-markdown";

function AIChat() {
  const { tripId } = useParams();

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // AUTO SCROLL TO LATEST MESSAGE
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end"
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // FETCH PREVIOUS CHAT HISTORY
  const fetchHistory = useCallback(async () => {
    try {
      const response = await API.get(
        `/ai/trips/${tripId}/chat/history`
      );

      setMessages(response.data.history || []);
      setError("");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load chat history."
      );
    }
  }, [tripId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // SEND MESSAGE TO GEMINI
  const sendMessage = async (e) => {
    e.preventDefault();

    const userMessage = input.trim();

    if (!userMessage || loading) return;

    setInput("");
    setError("");

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        message: userMessage
      }
    ]);

    setLoading(true);

    try {
      const response = await API.post(
        `/ai/trips/${tripId}/chat`,
        {
          message: userMessage
        }
      );

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          message: response.data.answer
        }
      ]);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to get an AI response. Please try again."
      );

      await fetchHistory();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-chat-card">

      {/* CHAT HEADER */}
      <div className="ai-chat-header">

        <div className="ai-chat-avatar">
          ✨
        </div>

        <div className="ai-chat-heading">
          <h2>AI Travel Concierge</h2>
          <p>● Your personal travel assistant</p>
        </div>

        <span className="ai-chat-status">
          Online
        </span>

      </div>

      {/* CHAT DESCRIPTION */}
      <div className="ai-chat-description">
        Ask questions, discover destinations and plan your trip.
        Your assistant remembers your previous conversations.
      </div>

      {/* CHAT MESSAGES */}
      <div
        className="ai-chat-messages"
        ref={chatContainerRef}
        role="log"
        aria-live="polite"
        aria-label="AI conversation"
      >

        {messages.length === 0 && !loading && (
          <div className="ai-chat-empty">
            <div className="ai-empty-icon">✈️</div>
            <h3>Where would you like to go?</h3>
            <p>
              Ask me about destinations, food, budgets,
              activities or your travel itinerary.
            </p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={msg.id || index}
            className={`ai-message-row ${
              msg.role === "user"
                ? "user-message-row"
                : "assistant-message-row"
            }`}
          >

            {msg.role === "assistant" && (
              <div className="ai-message-avatar">
                ✨
              </div>
            )}

            <div
              className={`ai-message-bubble ${
                msg.role === "user"
                  ? "user-message"
                  : "assistant-message"
              }`}
            >

              <div className="ai-message-author">
                {msg.role === "user" ? "You" : "AI Assistant"}
              </div>

              <div className="ai-markdown">
                <ReactMarkdown>
                  {msg.message}
                </ReactMarkdown>
              </div>

            </div>

          </div>
        ))}

        {/* AI THINKING INDICATOR */}
        {loading && (
          <div className="ai-message-row assistant-message-row">

            <div className="ai-message-avatar">
              ✨
            </div>

            <div className="ai-thinking-bubble">
              <span></span>
              <span></span>
              <span></span>
              <small>AI is thinking...</small>
            </div>

          </div>
        )}

        <div ref={messagesEndRef} />

      </div>

      {/* ERROR MESSAGE */}
      {error && (
        <div className="ai-chat-error">
          {error}
        </div>
      )}

      {/* MESSAGE INPUT */}
      <form
        className="ai-chat-input-form"
        onSubmit={sendMessage}
      >

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything about your trip..."
          disabled={loading}
          aria-label="Message to AI travel assistant"
        />

        <button
          type="submit"
          disabled={loading || !input.trim()}
        >
          {loading ? "Sending..." : "➤ Send"}
        </button>

      </form>

      <p className="ai-chat-footer">
        AI-generated travel suggestions may need independent verification.
      </p>

    </div>
  );
}

export default AIChat;
