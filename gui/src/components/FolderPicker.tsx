"use client";

import React, { useState, useEffect } from "react";

interface FolderPickerProps {
  onSelect: (path: string) => void;
  onClose: () => void;
}

export default function FolderPicker({ onSelect, onClose }: FolderPickerProps) {
  const [currentPath, setCurrentPath] = useState(".");
  const [folders, setFolders] = useState<{ name: string; path: string }[]>([]);
  const [parentPath, setParentPath] = useState("");

  const loadFolders = async (path: string) => {
    try {
      const resp = await fetch(`http://localhost:8000/api/fs/list?path=${encodeURIComponent(path)}`);
      const data = await resp.json();
      setCurrentPath(data.current_path);
      setFolders(data.folders);
      setParentPath(data.parent_path);
    } catch (e) {
      console.error("Erro ao listar pastas:", e);
    }
  };

  useEffect(() => {
    loadFolders(".");
  }, []);

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div className="glass" style={{ width: '500px', maxHeight: '80vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '24px' }}>
        <h3 style={{ marginBottom: '16px' }}>Selecionar Pasta do Vault</h3>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '12px', wordBreak: 'break-all' }}>
          {currentPath}
        </div>
        
        <div style={{ flex: 1, overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '8px', marginBottom: '20px' }}>
          <div 
            onClick={() => loadFolders(parentPath)} 
            style={{ padding: '12px', cursor: 'pointer', borderBottom: '1px solid var(--border)', background: 'rgba(255,255,255,0.03)' }}
          >
            📁 .. (Voltar)
          </div>
          {folders.map((f) => (
            <div 
              key={f.path} 
              onClick={() => loadFolders(f.path)} 
              style={{ padding: '12px', cursor: 'pointer', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between' }}
            >
              <span>📁 {f.name}</span>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '10px 20px', background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--border)' }}>Cancelar</button>
          <button onClick={() => onSelect(currentPath)} style={{ padding: '10px 20px', background: 'var(--accent)', color: '#fff' }}>Selecionar Esta Pasta</button>
        </div>
      </div>
    </div>
  );
}
