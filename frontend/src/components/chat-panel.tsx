"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { apiFetchJson, getErrorMessage } from "@/lib/api";
import type { ChatResponse } from "@/lib/types";

interface Message {
  id: string;
  role: "assistant" | "user" | "error";
  content: string;
}

interface ChatPanelProps {
  title: string;
  subtitle: string;
  companyId?: number;
  companyName?: string;
}

function createIntroMessage(companyName?: string) {
  return companyName
    ? `${companyName}의 재무 흐름, 업황, 리스크 요인을 자연어로 물어보세요.`
    : "최신 업황, 업계 뉴스, 거래 판단 포인트를 바로 질문할 수 있습니다.";
}

function BotIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M20 9V7c0-1.1-.9-2-2-2h-3c0-1.66-1.34-3-3-3S9 3.34 9 5H6c-1.1 0-2 .9-2 2v2c-1.66 0-3 1.34-3 3s1.34 3 3 3v4c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-4c1.66 0 3-1.34 3-3s-1.34-3-3-3zm-2 10H6V7h12v12zM9 11c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1zm6 0c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1zm-3 6c1.9 0 3.63-.99 4.58-2.6H7.42C8.37 16.01 10.1 17 12 17z" />
    </svg>
  );
}

function ChatIcon() {
  return (
    <svg className="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 24 24">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12z" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
    </svg>
  );
}

export function ChatPanel({ title, subtitle, companyId, companyName }: ChatPanelProps) {
  const [open, setOpen] = useState(false);
  const initialMessage = useMemo(() => createIntroMessage(companyName), [companyName]);
  const [messages, setMessages] = useState<Message[]>([
    { id: "intro", role: "assistant", content: initialMessage },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setMessages([{ id: "intro", role: "assistant", content: createIntroMessage(companyName) }]);
  }, [companyId, companyName]);

  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
  }, [messages, sending]);

  async function handleSubmit() {
    const trimmed = input.trim();
    if (!trimmed || sending) return;

    setMessages((curr) => [...curr, { id: `user-${Date.now()}`, role: "user", content: trimmed }]);
    setInput("");
    setSending(true);

    try {
      const payload = await apiFetchJson<ChatResponse>("/api/chat", {
        method: "POST",
        body: JSON.stringify({ company_id: companyId, message: trimmed }),
      });
      setMessages((curr) => [
        ...curr,
        { id: `assistant-${Date.now()}`, role: payload.error ? "error" : "assistant", content: payload.reply },
      ]);
    } catch (error) {
      setMessages((curr) => [
        ...curr,
        { id: `error-${Date.now()}`, role: "error", content: getErrorMessage(error) },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="fixed bottom-8 right-8 z-[100]">
      <div className="flex flex-col items-end gap-4">
        {open && (
          <div className="w-96 glass-card rounded-3xl overflow-hidden flex flex-col shadow-2xl border-indigo-200/50">
            {/* 헤더 */}
            <div className="bg-gradient-to-r from-indigo-500 to-indigo-600 p-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-inner text-indigo-500">
                  <BotIcon />
                </div>
                <div>
                  <p className="text-white font-bold text-sm leading-none">{title}</p>
                  <p className="text-white/60 text-[10px] font-bold uppercase tracking-tighter mt-0.5">
                    Online · Ready to Help
                  </p>
                </div>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="text-white/40 hover:text-white transition-colors"
              >
                <CloseIcon />
              </button>
            </div>

            {/* 메시지 영역 */}
            <div className="h-72 p-5 overflow-y-auto space-y-3 bg-slate-50/50" ref={scrollRef}>
              <p className="text-[10px] text-slate-400 text-center mb-4">{subtitle}</p>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] px-4 py-3 rounded-3xl text-xs leading-relaxed ${
                      msg.role === "user"
                        ? "bg-indigo-500 text-white rounded-br-none"
                        : msg.role === "error"
                          ? "bg-rose-50 text-rose-700 border border-rose-200 rounded-tl-none"
                          : "bg-white border-2 border-slate-100 shadow-sm text-slate-700 rounded-tl-none"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="bg-white border-2 border-slate-100 shadow-sm rounded-3xl rounded-tl-none px-4 py-3 flex items-center gap-1">
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 입력 영역 */}
            <div className="p-4 bg-white border-t border-slate-100">
              <div className="relative">
                <input
                  type="text"
                  className="w-full pl-5 pr-12 py-3 bg-slate-50 border-none rounded-full text-xs font-medium focus:outline-none focus:ring-4 focus:ring-indigo-500/10 placeholder:text-slate-400"
                  placeholder="질문을 입력하세요..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void handleSubmit();
                    }
                  }}
                />
                <button
                  onClick={() => void handleSubmit()}
                  disabled={sending}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-indigo-500 hover:bg-indigo-600 text-white rounded-full flex items-center justify-center shadow-lg shadow-indigo-500/20 transition-all hover:scale-105 disabled:opacity-50"
                >
                  <SendIcon />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 토글 버튼 */}
        <button
          onClick={() => setOpen((v) => !v)}
          className="w-16 h-16 bg-indigo-500 rounded-full shadow-2xl shadow-indigo-500/30 flex items-center justify-center border-4 border-white hover:scale-110 transition-all"
        >
          <ChatIcon />
        </button>
      </div>
    </div>
  );
}
