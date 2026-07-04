"use client";
import { useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { Send, Bot, Loader2 } from "lucide-react";

export default function ChatPage() {
  const token = useAuthStore((s) => s.token);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{role:string;content:string}[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });
      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [...prev, { role: "assistant", content: data.response || data.message || "No response" }]);
      } else {
        setMessages((prev) => [...prev, { role: "assistant", content: "*AI chat requires an LLM provider (Ollama/llama.cpp) to be configured.*" }]);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "*Connection error. Ensure the master server is running.*" }]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)]">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">AI Chat</h1>
        <p className="text-muted-foreground">Chat with AI models running on the cluster.</p>
      </div>
      <div className="flex-1 overflow-y-auto space-y-4 py-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <Bot className="h-12 w-12 mb-4" />
            <p>Send a message to start chatting with the AI.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
            <div className={`rounded-lg px-4 py-2 max-w-[70%] ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {loading && <div className="flex justify-center"><Loader2 className="h-5 w-5 animate-spin" /></div>}
      </div>
      <div className="flex gap-2 border-t pt-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type a message..."
          className="flex-1 rounded-md border bg-background px-3 py-2 text-sm"
        />
        <button onClick={sendMessage} disabled={loading} className="rounded-md bg-primary px-3 py-2 text-primary-foreground text-sm">
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
