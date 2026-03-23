import React, { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL;

const ChatPanel = ({ onAnswer }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (event) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) {
      return;
    }

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      });
      const data = await response.json();
      const answer = data?.answer || "Something went wrong, please try again.";
      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
      if (onAnswer) {
        onAnswer(answer);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong, please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "#f5f5f5",
        padding: "16px 14px",
      }}
    >
      <div
        style={{
          backgroundColor: "#ffffff",
          border: "1px solid #e6e6e6",
          borderRadius: 12,
          padding: "16px 18px",
          marginBottom: 12,
          flexShrink: 0,
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 16 }}>Chat with Graph</div>
        <div style={{ fontSize: 12, color: "#7a7a7a", marginTop: 4 }}>
          Order to Cash
        </div>
      </div>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 16,
          padding: "8px 4px",
        }}
      >
        {messages.length === 0 && (
          <div style={{ color: "#777", fontSize: 14 }}>
            Ask a question about the Order to Cash dataset.
          </div>
        )}

        {messages.map((message, index) => {
          if (message.role === "assistant") {
            return (
              <div key={`assistant-${index}`} style={{ display: "flex", gap: 12 }}>
                <div
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: "50%",
                    backgroundColor: "#111111",
                    color: "#ffffff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: 14,
                  }}
                >
                  D
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 13 }}>Dodge AI</div>
                  <div style={{ fontSize: 12, color: "#7a7a7a", marginBottom: 6 }}>
                    Graph Agent
                  </div>
                  <div
                    style={{
                      backgroundColor: "#ffffff",
                      border: "1px solid #e2e2e2",
                      borderRadius: 12,
                      padding: "10px 12px",
                      fontSize: 14,
                      lineHeight: 1.5,
                    }}
                  >
                    {message.content}
                  </div>
                </div>
              </div>
            );
          }

          return (
            <div key={`user-${index}`} style={{ display: "flex", justifyContent: "flex-end" }}>
              <div style={{ maxWidth: "85%", textAlign: "right" }}>
                <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginBottom: 6 }}>
                  <div style={{ fontWeight: 600, fontSize: 12, color: "#4a4a4a" }}>You</div>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: "50%",
                      backgroundColor: "#d1d1d1",
                    }}
                  />
                </div>
                <div
                  style={{
                    backgroundColor: "#1a1a1a",
                    color: "#ffffff",
                    borderRadius: 12,
                    padding: "10px 12px",
                    fontSize: 14,
                    lineHeight: 1.5,
                  }}
                >
                  {message.content}
                </div>
              </div>
            </div>
          );
        })}

        {loading && (
          <div style={{ color: "#666", fontSize: 13 }}>Thinking...</div>
        )}

        <div ref={bottomRef} />
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 12,
          color: "#7a7a7a",
          margin: "8px 4px 10px",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            backgroundColor: "#22c55e",
            display: "inline-block",
          }}
        />
        Dodge AI is awaiting instructions
      </div>

      <form
        onSubmit={sendMessage}
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 10,
          padding: "14px",
          borderRadius: 12,
          backgroundColor: "#ffffff",
          border: "1px solid #e6e6e6",
          flexShrink: 0,
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Analyze anything"
          style={{
            border: "none",
            outline: "none",
            fontSize: 14,
            padding: "8px 4px",
            backgroundColor: "transparent",
          }}
        />
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button
            type="submit"
            disabled={loading || !input.trim()}
            style={{
              padding: "8px 16px",
              borderRadius: 10,
              border: "none",
              backgroundColor: loading || !input.trim() ? "#bdbdbd" : "#7c7c7c",
              color: "#ffffff",
              fontWeight: 600,
              cursor: loading || !input.trim() ? "not-allowed" : "pointer",
            }}
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatPanel;
