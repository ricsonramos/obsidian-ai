"use client";

import React, { useState, useEffect, useRef } from "react";

interface Message {
  role: "user" | "bot" | "log";
  content: string;
  level?: "info" | "warning" | "error";
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", content: "Olá! Sou o Antigravity. O que vamos mapear hoje?" }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Conectar ao WebSocket de logs
    const socket = new WebSocket("ws://localhost:8000/api/ws/logs");
    socketRef.current = socket;

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, { role: "log", content: data.message, level: data.level }]);
    };

    return () => socket.close();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = input;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setIsTyping(true);

    try {
      const resp = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await resp.json();
      setMessages(prev => [...prev, { role: "bot", content: data.response }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "bot", content: "Erro ao comunicar com o servidor. Verifique se o backend está rodando." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: 'calc(100vh - 40px)', margin: '20px 20px 20px 0' }}>
      <div 
        ref={scrollRef} 
        style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px' }}
      >
        {messages.map((m, i) => (
          <div 
            key={i} 
            style={{ 
              alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: m.role === 'log' ? '100%' : '80%',
              width: m.role === 'log' ? '100%' : 'auto'
            }}
          >
            {m.role === 'log' ? (
              <div style={{ 
                fontSize: '11px', 
                fontFamily: 'monospace', 
                color: m.level === 'error' ? '#ef4444' : m.level === 'warning' ? '#f59e0b' : 'var(--text-secondary)',
                borderLeft: `2px solid ${m.level === 'error' ? '#ef4444' : 'var(--border)'}`,
                paddingLeft: '12px',
                margin: '4px 0'
              }}>
                {m.content}
              </div>
            ) : (
              <div className="glass" style={{ 
                padding: '12px 18px', 
                background: m.role === 'user' ? 'var(--accent)' : 'var(--bg-card)',
                color: m.role === 'user' ? '#fff' : 'var(--text-primary)',
                borderRadius: m.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                boxShadow: m.role === 'user' ? '0 4px 15px var(--accent-glow)' : 'none'
              }}>
                {m.content}
              </div>
            )}
          </div>
        ))}
        {isTyping && <div style={{ color: 'var(--text-secondary)', fontSize: '12px', marginLeft: '20px' }}>Digitando...</div>}
      </div>

      <div style={{ padding: '0 20px 20px 20px' }}>
        <div style={{ display: 'flex', gap: '12px' }}>
          <input 
            className="glass"
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Digite sua mensagem (ex: Mapear sobre Inteligência Artificial)..."
            style={{ flex: 1, padding: '16px 24px', fontSize: '15px' }}
          />
          <button 
            onClick={handleSend}
            style={{ background: 'var(--accent)', color: '#fff', padding: '0 32px', fontSize: '18px' }}
          >
            →
          </button>
        </div>
      </div>
    </div>
  );
}
