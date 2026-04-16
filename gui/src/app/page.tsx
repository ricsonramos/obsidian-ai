"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import Chat from "@/components/Chat";
import FolderPicker from "@/components/FolderPicker";

export default function Home() {
  const [config, setConfig] = useState({
    vault_path: "",
    theme: "obsidian",
    depth: 2
  });
  const [showPicker, setShowPicker] = useState(false);

  // Carregar configurações iniciais
  useEffect(() => {
    fetch("http://localhost:8000/api/config")
      .then(r => r.json())
      .then(data => {
        setConfig(data);
        document.documentElement.setAttribute("data-theme", data.theme);
      })
      .catch(e => console.error("Erro ao carregar config:", e));
  }, []);

  const handleThemeChange = async (newTheme: string) => {
    setConfig(prev => ({ ...prev, theme: newTheme }));
    document.documentElement.setAttribute("data-theme", newTheme);
    await fetch("http://localhost:8000/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ theme: newTheme })
    });
  };

  const handleVaultSelect = async (newPath: string) => {
    setConfig(prev => ({ ...prev, vault_path: newPath }));
    setShowPicker(false);
    await saveVaultPath(newPath);
  };

  const saveVaultPath = async (path: string) => {
    await fetch("http://localhost:8000/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vault_path: path })
    });
  };

  return (
    <main style={{ display: 'flex', background: 'var(--bg-main)', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <Sidebar 
        vaultPath={config.vault_path} 
        theme={config.theme} 
        depth={config.depth}
        onSelectFolder={() => setShowPicker(true)} 
        onThemeChange={handleThemeChange} 
        onVaultPathChange={(path) => {
          setConfig(prev => ({ ...prev, vault_path: path }));
          saveVaultPath(path); // Salva a cada alteração (ou poderia usar debounce)
        }}
      />
      
      <Chat />

      {showPicker && (
        <FolderPicker 
          onSelect={handleVaultSelect} 
          onClose={() => setShowPicker(false)} 
        />
      )}

      {/* Background Decor */}
      <div style={{
        position: 'fixed',
        top: '-10%',
        right: '-10%',
        width: '500px',
        height: '500px',
        background: 'var(--accent)',
        filter: 'blur(150px)',
        opacity: 0.1,
        zIndex: -1,
        borderRadius: '50%'
      }} />
    </main>
  );
}
