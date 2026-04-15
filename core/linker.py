import os
import glob
import re
from core.utils import normalize_title

class Linker:
    def __init__(self, vault_path: str):
        self.vault_path = os.path.abspath(vault_path)

    def _get_all_titles_mapped(self) -> dict:
        """
        Retorna dicionário {titulo_normalizado: titulo_original}.
        O titulo_original é preferencialmente o H1 (# Title) ou o nome do arquivo.
        """
        mapped = {}
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        for file_path in md_files:
            try:
                # 1. Tenta extrair H1
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if match:
                        original_title = match.group(1).strip()
                        mapped[normalize_title(original_title)] = original_title
                
                # 2. Também mapeia pelo nome do arquivo (como fallback ou redundância)
                base = os.path.basename(file_path)
                name = os.path.splitext(base)[0].replace("_", " ")
                norm_name = normalize_title(name)
                if norm_name not in mapped:
                    mapped[norm_name] = name
            except Exception:
                pass
        return mapped

    def run(self):
        """Monitora e audita links baseados no mapeamento normalizado."""
        title_map = self._get_all_titles_mapped()
        if not title_map:
            return

        dead_links_detected = 0
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Busca wikilinks: [[link]]
                links = re.findall(r"\[\[(.*?)\]\]", content)
                for link in links:
                     # Se não existe o título original ou o normalizado no mapa
                     if normalize_title(link) not in title_map:
                          dead_links_detected += 1
                          
            except Exception:
                pass
                
        if dead_links_detected > 0:
             print(f"[AutoLinker | Auditor] Validação de Lacunas: Identificados cerca de {dead_links_detected} Orphan-Links semânticos pre-setados.")
        else:
             print("[AutoLinker | Auditor] O tecido criado é autossuficiente (Sem links fantasmas/pendentes).")

    def cross_link_vault(self):
        """Varre arquivos e insere wikilinks baseados em títulos existentes (accent-safe)."""
        title_map = self._get_all_titles_mapped()
        if not title_map:
             return
             
        # Ordena títulos normalizados por tamanho (maior primeiro) para evitar recursão parcial
        sorted_normalized = sorted(list(title_map.keys()), key=len, reverse=True)
        
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        files_modified = 0
        total_links_created = 0
        
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if len(content) < 10: continue

                # Identifica limites para não mexer no frontmatter nem nas seções de rodapé
                yaml_end_idx = 0
                match_yaml = re.search(r"^---\n.*?\n---\n", content, re.DOTALL | re.MULTILINE)
                if match_yaml:
                     yaml_end_idx = match_yaml.end()
                     
                relations_idx = content.find("## Relacoes")
                if relations_idx == -1:
                     relations_idx = content.find("## Conexoes")
                if relations_idx == -1:
                     relations_idx = len(content)
                     
                yaml_part = content[:yaml_end_idx]
                body_part = content[yaml_end_idx:relations_idx]
                footer_part = content[relations_idx:]
                
                original_body = body_part
                current_file_norm = normalize_title(os.path.basename(file_path).replace(".md", "").replace("_", " "))
                
                for norm_t in sorted_normalized:
                     if norm_t == current_file_norm: continue
                     # Não linka termos muito curtos (ruído)
                     if len(norm_t) < 3: continue
                     
                     original_t = title_map[norm_t]
                     safe_t = re.escape(original_t)
                     
                     # Regex: word boundary, ignora se já estiver dentro de [[...]] ou [...]
                     pattern = re.compile(rf"(?<!\[)(?<!\[\[)\b({safe_t})\b(?!\]\])(?!\])", re.IGNORECASE)
                     
                     def repl(m):
                          nonlocal total_links_created
                          total_links_created += 1
                          return f"[[{original_t}]]"
                          
                     body_part = pattern.sub(repl, body_part)
                
                if body_part != original_body:
                     new_content = yaml_part + body_part + footer_part
                     with open(file_path, "w", encoding="utf-8") as f:
                          f.write(new_content)
                     files_modified += 1
            except Exception as e:
                print(f"[AutoLinker] Erro formatando {file_path}: {e}")
                
        print(f"[AutoLinker | Ativo] Cross-linking concluído em {files_modified} documentos.")
        print(f"[AutoLinker | Ativo] Criados {total_links_created} novos backlinks orgânicos.")

    def semantic_link_vault(self, llm):
        """Varre os arquivos, vetoriza e liga arquivos semanticamente próximos (Stage 5)."""
        import json
        
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        cache_path = os.path.join(self.vault_path, ".embeddings_cache.json")
        
        cache = {}
        if os.path.exists(cache_path):
             try:
                 with open(cache_path, "r", encoding="utf-8") as fc:
                      cache = json.load(fc)
             except Exception:
                 pass
                 
        embeddings_db = {}
        files_embedded_now = 0
        title_map = self._get_all_titles_mapped()
        
        print("[SemanticLinker] Carregando e mapeando vetores textuais profundos...")
        
        for file_path in md_files:
             try:
                 mtime = os.path.getmtime(file_path)
                 file_name_clean = os.path.basename(file_path).replace(".md", "").replace("_", " ")
                 
                 with open(file_path, "r", encoding="utf-8") as f:
                      content = f.read()
                      
                 yaml_end_idx = 0
                 match_yaml = re.search(r"^---\n.*?\n---\n", content, re.DOTALL | re.MULTILINE)
                 if match_yaml:
                      yaml_end_idx = match_yaml.end()
                 body = content[yaml_end_idx:].strip()
                 
                 abs_path = os.path.abspath(file_path)
                 
                 if abs_path in cache and cache[abs_path].get("mtime") == mtime and cache[abs_path].get("embedding"):
                      embeddings_db[abs_path] = {
                          "embedding": cache[abs_path]["embedding"],
                          "title": file_name_clean,
                          "content": content
                      }
                 else:
                      print(f"[SemanticLinker] Vetorizando: {file_name_clean}")
                      vector = llm.get_embedding(body)
                      if vector:
                           embeddings_db[abs_path] = {
                                "embedding": vector,
                                "title": file_name_clean,
                                "content": content
                           }
                           cache[abs_path] = {
                                "mtime": mtime,
                                "embedding": vector
                           }
                           files_embedded_now += 1
             except Exception as e:
                 print(f"[SemanticLinker] Falha em {file_path}: {e}")
                 
        if files_embedded_now > 0:
             try:
                  with open(cache_path, "w", encoding="utf-8") as fc:
                       json.dump(cache, fc)
             except Exception:
                  pass
                  
        def cosine_sim(v1, v2):
             if not v1 or not v2: return 0.0
             dot = sum(a*b for a, b in zip(v1, v2))
             norm1 = sum(a*a for a in v1) ** 0.5
             norm2 = sum(b*b for b in v2) ** 0.5
             if norm1 == 0 or norm2 == 0: return 0.0
             return dot / (norm1 * norm2)
             
        threshold = float(os.getenv("SEMANTIC_THRESHOLD", "0.82"))
        file_paths = list(embeddings_db.keys())
        total_semantic_links = 0
        files_modified = set()
        memory_content = { p: embeddings_db[p]["content"] for p in file_paths }
        
        for i in range(len(file_paths)):
             for j in range(i + 1, len(file_paths)):
                  path_a = file_paths[i]
                  path_b = file_paths[j]
                  
                  sim = cosine_sim(embeddings_db[path_a]["embedding"], embeddings_db[path_b]["embedding"])
                  if sim >= threshold:
                        norm_a = normalize_title(embeddings_db[path_a]["title"])
                        norm_b = normalize_title(embeddings_db[path_b]["title"])
                        
                        title_a = title_map.get(norm_a, embeddings_db[path_a]["title"])
                        title_b = title_map.get(norm_b, embeddings_db[path_b]["title"])
                        
                        content_a = memory_content[path_a]
                        link_b = f"[[{title_b}]]"
                        if normalize_title(link_b) not in normalize_title(content_a):
                            if "## Relacoes" in content_a:
                                content_a += f"\n- {link_b}  <!-- Sim: {sim*100:.1f}% -->"
                            elif "## Conexoes" in content_a:
                                content_a += f"\n- {link_b}  <!-- Sim: {sim*100:.1f}% -->"
                            else:
                                content_a += f"\n\n## Relacoes\n- {link_b}  <!-- Sim: {sim*100:.1f}% -->"
                            memory_content[path_a] = content_a
                            files_modified.add(path_a)
                            total_semantic_links += 1
                            
                        content_b = memory_content[path_b]
                        link_a = f"[[{title_a}]]"
                        if normalize_title(link_a) not in normalize_title(content_b):
                            if "## Relacoes" in content_b:
                                content_b += f"\n- {link_a}  <!-- Sim: {sim*100:.1f}% -->"
                            elif "## Conexoes" in content_b:
                                content_b += f"\n- {link_a}  <!-- Sim: {sim*100:.1f}% -->"
                            else:
                                content_b += f"\n\n## Relacoes\n- {link_a}  <!-- Sim: {sim*100:.1f}% -->"
                            memory_content[path_b] = content_b
                            files_modified.add(path_b)
                            total_semantic_links += 1
                            
        for path in files_modified:
             with open(path, "w", encoding="utf-8") as f:
                  f.write(memory_content[path])
                  
        print(f"[SemanticLinker | Estágio 5] Concluído! Fez merge semântico em {len(files_modified)} ilhas.")
        print(f"[SemanticLinker | Estágio 5] Forjas puras criadas (Cosine > {threshold:.2f}): {total_semantic_links} conexões.")
