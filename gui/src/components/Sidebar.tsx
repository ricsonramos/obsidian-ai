"use client";

import React from "react";

interface SidebarProps {
  vaultPath: string;
  theme: string;
  onSelectFolder: () => void;
  onThemeChange: (theme: string) => void;
  onVaultPathChange: (path: string) => void;
  depth: number;
}

export default function Sidebar({ vaultPath, theme, onSelectFolder, onThemeChange, onVaultPathChange, depth }: SidebarProps) {
  const [pdfs, setPdfs] = React.useState<string[]>([]);
  const [selectedPdf, setSelectedPdf] = React.useState<string>("");
  const [forceAll, setForceAll] = React.useState<boolean>(false);
  const [isEnriching, setIsEnriching] = React.useState<boolean>(false);
  
  const [pendingNotes, setPendingNotes] = React.useState<{name: string, path: string}[]>([]);
  const [selectedNotes, setSelectedNotes] = React.useState<string[]>([]);

  const loadResources = async () => {
    try {
      const [pdfRes, noteRes] = await Promise.all([
        fetch("http://localhost:8000/api/pdfs"),
        fetch("http://localhost:8000/api/notes/pending")
      ]);
      const pdfData = await pdfRes.json();
      const noteData = await noteRes.json();
      if (pdfData.pdfs) setPdfs(pdfData.pdfs);
      if (noteData.notes) setPendingNotes(noteData.notes);
    } catch (err) {
      console.error("Erro ao carregar recursos:", err);
    }
  };

  React.useEffect(() => {
    loadResources();
  }, [vaultPath]);

  const themes = [
    { id: "obsidian", name: "Obsidian", color: "#7c4dff" },
    { id: "nebula", name: "Nebula", color: "#00d2ff" },
    { id: "cyberpunk", name: "Cyberpunk", color: "#ff00ff" },
    { id: "elysium", name: "Elysium", color: "#2563eb" },
  ];

  const handleEnrich = async () => {
    setIsEnriching(true);
    try {
      await fetch("http://localhost:8000/api/enrich", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pdf_name: selectedPdf || null,
          force_all: forceAll,
          vault_path: vaultPath,
          note_paths: selectedNotes.length > 0 ? selectedNotes : null
        })
      });
      // Limpa seleção após iniciar
      setSelectedNotes([]);
      setTimeout(loadResources, 2000); // Recarrega após um tempo
    } catch (err) {
      console.error("Erro no enriquecimento:", err);
    }
    setIsEnriching(false);
  };

  const toggleNote = (path: string) => {
    setSelectedNotes(prev => 
      prev.includes(path) ? prev.filter(p => p !== path) : [...prev, path]
    );
  };

  return (
    <aside className="sidebar glass" style={{ width: '320px', height: 'calc(100vh - 40px)', margin: '20px', padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px', overflowY: 'auto' }}>
      <div className="brand" style={{ fontSize: '24px', fontWeight: '800', letterSpacing: '-1px', color: 'var(--accent)' }}>
        ANTIGRAVITY
        <div style={{ fontSize: '10px', color: 'var(--text-secondary)', letterSpacing: '2px', marginTop: '-4px' }}>KNOWLEDGE ENGINE</div>
      </div>

      {/* VAULT SECTION */}
      <div className="section">
        <label style={{ display: 'block', fontSize: '10px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px', textTransform: 'uppercase' }}>Caminho do Vault</label>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            className="glass"
            type="text"
            value={vaultPath}
            onChange={(e) => onVaultPathChange(e.target.value)}
            style={{ flex: 1, padding: '10px', fontSize: '12px', background: 'var(--bg-main)', border: '1px solid var(--border)' }}
          />
          <button className="glass" onClick={onSelectFolder} style={{ padding: '0 12px', background: 'var(--accent)' }}>📂</button>
        </div>
      </div>

      {/* THEME SECTION */}
      <div className="section">
        <label style={{ display: 'block', fontSize: '10px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px', textTransform: 'uppercase' }}>Tema da Interface</label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
          {themes.map((t) => (
            <button
              key={t.id}
              className={`glass ${theme === t.id ? "active" : ""}`}
              onClick={() => onThemeChange(t.id)}
              style={{
                padding: '8px',
                fontSize: '11px',
                background: theme === t.id ? t.color : 'transparent',
                color: theme === t.id ? '#fff' : 'var(--text-primary)',
                border: theme === t.id ? 'none' : '1px solid var(--border)'
              }}
            >
              {t.name}
            </button>
          ))}
        </div>
      </div>

      <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '2px 0' }} />

      {/* RAG CONTROLS SECTION */}
      <div className="section">
        <label style={{ display: 'block', fontSize: '10px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px', textTransform: 'uppercase' }}>Fonte Doutrinária (PDF)</label>
        <select 
          className="glass"
          value={selectedPdf}
          onChange={(e) => setSelectedPdf(e.target.value)}
          style={{ width: '100%', padding: '10px', fontSize: '12px', background: 'var(--bg-main)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
        >
          <option value="">Auto-detectar (Primeiro PDF)</option>
          {pdfs.map(pdf => (
            <option key={pdf} value={pdf}>{pdf}</option>
          ))}
        </select>
      </div>

      {/* NOTE SELECTION SECTION */}
      <div className="section" style={{ flex: 1, minHeight: '150px', display: 'flex', flexDirection: 'column' }}>
        <label style={{ display: 'block', fontSize: '10px', fontWeight: '700', color: 'var(--text-secondary)', marginBottom: '6px', textTransform: 'uppercase' }}>
          Notas p/ Enriquecer ({selectedNotes.length}/{pendingNotes.length})
        </label>
        <div className="glass" style={{ flex: 1, background: 'var(--bg-main)', border: '1px solid var(--border)', overflowY: 'auto', padding: '8px' }}>
          {pendingNotes.length === 0 ? (
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textAlign: 'center', marginTop: '20px' }}>Nenhuma nota pendente</div>
          ) : (
            pendingNotes.map(note => (
              <div 
                key={note.path} 
                onClick={() => toggleNote(note.path)}
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px', 
                  padding: '8px', 
                  fontSize: '11px', 
                  cursor: 'pointer',
                  background: selectedNotes.includes(note.path) ? 'rgba(124, 77, 255, 0.1)' : 'transparent',
                  borderRadius: '4px',
                  marginBottom: '4px'
                }}
              >
                <input 
                  type="checkbox" 
                  checked={selectedNotes.includes(note.path)} 
                  readOnly 
                  style={{ accentColor: 'var(--accent)' }}
                />
                <span style={{ color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{note.name}</span>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="section" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
        <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-primary)' }}>💎 Forçar Sobrescrita</span>
        <input 
          type="checkbox" 
          checked={forceAll} 
          onChange={(e) => setForceAll(e.target.checked)}
          style={{ cursor: 'pointer', width: '18px', height: '18px', accentColor: 'var(--accent)' }}
        />
      </div>

      <div className="section">
        <button 
          className="glass" 
          onClick={handleEnrich}
          disabled={isEnriching}
          style={{ 
            width: '100%', 
            padding: '14px', 
            background: isEnriching ? 'var(--text-secondary)' : 'var(--accent)', 
            color: '#fff', 
            fontWeight: 'bold',
            fontSize: '12px',
            marginBottom: '10px',
            cursor: isEnriching ? 'default' : 'pointer',
            border: 'none'
          }}
        >
          {isEnriching ? "⏳ SINTETIZANDO..." : selectedNotes.length > 0 ? `🧠 ENRIQUECER ${selectedNotes.length} NOTAS` : "🧠 ENRIQUECER TUDO"}
        </button>
      </div>
    </aside>
  );
}
