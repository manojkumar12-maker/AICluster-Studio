"use client";

import { Bot } from "lucide-react";

export default function ChatPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AI Chat</h1>
        <p className="text-sm text-muted-foreground">Chat with the AI coding assistant</p>
      </div>
      <div className="flex flex-col items-center justify-center rounded-xl border border-border py-16">
        <Bot className="mb-4 h-12 w-12 text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground">AI chat interface coming soon</p>
      </div>
    </div>
  );
}
