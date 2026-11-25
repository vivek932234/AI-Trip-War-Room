
import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./GroupChat.css";

function GroupChat() {
    const { tripId } = useParams();
    const navigate = useNavigate();

    const socketRef = useRef(null);
    const messagesEndRef = useRef(null);

    const [messages, setMessages] = useState([]);
    const [message, setMessage] = useState("");
    const [connectionStatus, setConnectionStatus] = useState("Connecting...");
    const [error, setError] = useState("");

    // CONNECT TO WEBSOCKET
    useEffect(() => {
        const token = localStorage.getItem("access_token");

        if (!token) {
            setError("Please login to access group chat.");
            setConnectionStatus("Disconnected");
            return;
        }

        const API_BASE_URL =
    import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const WS_BASE_URL = API_BASE_URL
    .replace(/^https:/, "wss:")
    .replace(/^http:/, "ws:")
    .replace(/\/$/, "");

const socket = new WebSocket(
    `${WS_BASE_URL}/ws/trips/${tripId}?token=${encodeURIComponent(token)}`
);
        socketRef.current = socket;

        socket.onopen = () => {
            setConnectionStatus("Connected");
            setError("");
        };


socket.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);

        // LOAD PREVIOUS CHAT HISTORY
        if (data.event === "chat_history") {
            const previousMessages = data.messages.map((item) => ({
                id: item.id,
                event: "new_message",
                user: item.user,
                user_id: item.user_id,
                data: {
                    message: item.message
                },
                receivedAt: new Date(
                    item.created_at
                ).toLocaleTimeString()
            }));

            setMessages(previousMessages);
            return;
        }

        // RECEIVE NEW MESSAGES AND NOTIFICATIONS
        setMessages((previous) => [
            ...previous,
            {
                id: data.id || `${Date.now()}-${Math.random()}`,
                ...data,
                receivedAt: data.created_at
                    ? new Date(data.created_at).toLocaleTimeString()
                    : new Date().toLocaleTimeString()
            }
        ]);

    } catch (err) {
        console.error("Unable to read chat message:", err);
    }
};


        socket.onerror = () => {
            setError("Unable to connect to group chat.");
            setConnectionStatus("Connection Error");
        };

        socket.onclose = () => {
            setConnectionStatus("Disconnected");
        };

        return () => {
            socket.close();
            socketRef.current = null;
        };
    }, [tripId]);

    // AUTO SCROLL
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({
            behavior: "smooth"
        });
    }, [messages]);

    // SEND MESSAGE
    const handleSendMessage = (e) => {
        e.preventDefault();

        const trimmedMessage = message.trim();

        if (!trimmedMessage) return;

        if (
            socketRef.current &&
            socketRef.current.readyState === WebSocket.OPEN
        ) {
            socketRef.current.send(
                JSON.stringify({
                    message: trimmedMessage
                })
            );

            setMessage("");
        } else {
            setError("Chat is not connected. Please try again.");
        }
    };

    return (
        <div className="group-chat-container">

            <header className="chat-header">
                <div>
                    <h1>💬 Group Trip Chat</h1>
                    <p>Communicate with your trip members in real time.</p>
                </div>

                <button onClick={() => navigate(`/trips/${tripId}`)}>
                    Back to Trip
                </button>
            </header>

            <div className="chat-status">
                <span
                    className={
                        connectionStatus === "Connected"
                            ? "status-dot connected"
                            : "status-dot disconnected"
                    }
                ></span>

                {connectionStatus}
            </div>

            {error && <p className="chat-error">{error}</p>}

            <div className="chat-messages">

                {messages.length === 0 && (
                    <div className="empty-chat">
                        <h2>Welcome to Group Chat!</h2>
                        <p>Start a conversation with your trip members.</p>
                    </div>
                )}

                {messages.map((item) => (
                    <div className="chat-message" key={item.id}>

                        {item.event === "new_message" && (
                            <>
                                <strong>{item.user}</strong>

                                <p>
                                    {item.data?.message || "Message"}
                                </p>

                                <small>{item.receivedAt}</small>
                            </>
                        )}

                        {item.event === "user_connected" && (
                            <div className="system-message">
                                🟢 {item.user} joined the trip
                            </div>
                        )}

                        {item.event === "user_disconnected" && (
                            <div className="system-message">
                                ⚪ {item.user} left the trip
                            </div>
                        )}

                    </div>
                ))}

                <div ref={messagesEndRef}></div>

            </div>

            <form className="chat-input-form" onSubmit={handleSendMessage}>

                <input
                    type="text"
                    placeholder="Type your message..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                />

                <button
                    type="submit"
                    disabled={
                        connectionStatus !== "Connected" ||
                        !message.trim()
                    }
                >
                    Send
                </button>

            </form>

        </div>
    );
}

export default GroupChat;
