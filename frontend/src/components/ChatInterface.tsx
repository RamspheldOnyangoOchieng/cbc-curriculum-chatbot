"use client";

import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, User, Bot, Trash2, ShieldCheck, BookOpen, GraduationCap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Habari! I am your CBC & CBE Expert Guide. 🇰🇪\n\nThe transition to Senior School and Grade 10 is a major milestone. I'm here to help you navigate career pathways, placement details, and curriculum changes. What would you like to explore today?" }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [...messages, userMsg] }),
      });

      if (!response.ok) throw new Error("Failed to fetch response");

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.content }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, something went wrong. Please try again." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0a] text-zinc-100 font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-zinc-950/50 backdrop-blur-md border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-600/20 rounded-xl border border-red-500/30">
            <GraduationCap className="w-6 h-6 text-red-500" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-white via-red-500 to-green-500 bg-clip-text text-transparent">
              CBC Chatbot PRO
            </h1>
            <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider">Education Expert System</p>
          </div>
        </div>
        <button
          onClick={() => setMessages([{ role: "assistant", content: "Clean slate! 📝\n\nI'm ready for your next set of questions about Kenya's education transition. Whether it's about STEM pathways, Arts, or Social Sciences, ask away and let's unlock the future together!" }])}
          className="p-2 hover:bg-white/5 rounded-full transition-colors group"
          title="Clear Chat"
        >
          <Trash2 className="w-5 h-5 text-zinc-500 group-hover:text-red-400" />
        </button>
      </header>

      {/* Main Chat Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide"
      >
        <AnimatePresence>
          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "flex items-start gap-4 max-w-3xl mx-auto",
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              )}
            >
              <div className={cn(
                "p-2.5 rounded-2xl border",
                msg.role === "user"
                  ? "bg-zinc-900 border-zinc-800"
                  : "bg-green-600/10 border-green-500/20"
              )}>
                {msg.role === "user" ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5 text-green-500" />}
              </div>
              <div
                className={cn(
                  "max-w-[85%] rounded-2xl px-5 py-4 text-sm shadow-xl leading-relaxed backdrop-blur-sm",
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-tr-none border border-blue-500/50"
                    : "bg-zinc-900/80 text-zinc-100 border border-white/10 rounded-tl-none"
                )}
              >
                <div className="prose prose-sm max-w-none prose-invert prose-p:my-3 prose-headings:mb-3 prose-headings:mt-5 prose-ul:my-3 prose-li:my-1.5">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }: any) => <p className="mb-4 last:mb-0 text-zinc-200 leading-relaxed">{children}</p>,
                      h3: ({ children }: any) => <h3 className="text-xl font-bold mt-6 mb-3 text-white border-b border-white/10 pb-2">{children}</h3>,
                      li: ({ children }: any) => <li className="ml-4 list-disc mb-2 text-zinc-300">{children}</li>,
                      strong: ({ children }: any) => <strong className="text-blue-400 font-semibold">{children}</strong>,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {isLoading && (
          <div className="flex items-center gap-3 max-w-3xl mx-auto">
            <div className="p-2.5 rounded-2xl bg-green-600/10 border border-green-500/20">
              <Bot className="w-5 h-5 text-green-500 animate-pulse" />
            </div>
            <div className="flex gap-1.5 p-4">
              <div className="w-2 h-2 bg-green-500/50 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-green-500/50 rounded-full animate-bounce [animation-delay:0.2s]" />
              <div className="w-2 h-2 bg-green-500/50 rounded-full animate-bounce [animation-delay:0.4s]" />
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <footer className="p-6 bg-zinc-950/50 backdrop-blur-md border-t border-white/5">
        <div className="max-w-3xl mx-auto relative group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask anything about CBC..."
            className="w-full bg-zinc-900 border border-white/5 rounded-2xl py-4 pl-6 pr-14 text-sm focus:outline-none focus:border-green-500/50 transition-all placeholder:text-zinc-600"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-red-600 hover:bg-red-500 disabled:bg-zinc-800 disabled:text-zinc-500 text-white rounded-xl transition-all"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-[10px] text-center text-zinc-600 mt-4 font-medium uppercase tracking-[0.2em]">
          Powered by CBE Expert System | Built for Parents & Teachers
        </p>
      </footer>
    </div>
  );
}
