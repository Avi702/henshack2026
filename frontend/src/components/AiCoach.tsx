"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from 'react-markdown';

type Message = {
    role: "user" | "assistant";
    content: string;
};

const SUGGESTIONS = [
  "How can I fix a butt wink when squatting?",
  "What is the valsalva maneuver?",
  "How wide should my bench grip be?",
  "Conventional vs Sumo deadlifts?"
];

export default function AiCoach() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hi! I'm HenShack AI Coach. Ask me any questions about your lifting form, programming, or workout advice." }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const newMessages = [...messages, { role: "user" as const, content: text }];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantResponse = "";

      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const textChunk = decoder.decode(value, { stream: true });
        assistantResponse += textChunk;

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].content = assistantResponse;
          return updated;
        });
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev, 
        { role: "assistant", content: "Sorry, my API connection failed. Did you configure the GEMINI_API_KEY?" }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl overflow-hidden shadow-xl shadow-black/30 w-full animate-fade-in">
      <div className="bg-zinc-200 dark:bg-zinc-800 p-4 border-b border-zinc-300 dark:border-zinc-700 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-accent text-white flex items-center justify-center font-bold shadow-lg shadow-accent/20">
            🤖
        </div>
        <div>
            <h3 className="font-bold text-sm text-zinc-900 dark:text-zinc-100 leading-tight">HenShack AI Coach</h3>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Powered by Gemini</p>
        </div>
      </div>

      <div className="flex-1 p-4 overflow-y-auto space-y-4 text-sm" ref={scrollRef}>
        {messages.map((m, idx) => (
          <div key={idx} className={`flex w-full ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[90%] md:max-w-[85%] rounded-2xl px-4 py-3 shadow-sm ${
              m.role === "user" 
                ? "bg-accent text-white rounded-br-sm" 
                : "bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-800 dark:text-zinc-200 rounded-bl-sm"
            }`}>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown>{m.content}</ReactMarkdown>
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-zinc-200 dark:bg-zinc-800 text-zinc-500 rounded-2xl rounded-bl-none px-4 py-2 text-sm italic">
                Analyzing form mechanics...
            </div>
          </div>
        )}
      </div>

      <div className="p-3 border-t border-zinc-300 dark:border-zinc-800 bg-zinc-200/50 dark:bg-zinc-900">
        <div className="flex flex-wrap gap-2 mb-3">
          {SUGGESTIONS.map((s, i) => (
             <button 
                key={i} 
                onClick={() => handleSubmit(s)}
                disabled={isLoading}
                className="text-xs py-1 px-2.5 rounded-full border border-zinc-300 dark:border-zinc-700 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors whitespace-nowrap overflow-hidden text-ellipsis max-w-50"
                title={s}
             >
                {s}
             </button>
          ))}
        </div>
        
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSubmit(input); }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Ask AI Coach a question..."
            className="flex-1 bg-zinc-100 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 text-sm rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-accent transition-all"
          />
          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="bg-accent text-white p-2 rounded-xl hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-zinc-900 transition-all font-bold disabled:opacity-50"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
