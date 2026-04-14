import os
import glob
import re

class Linker:
    def __init__(self, vault_path: str):
        self.vault_path = os.path.abspath(vault_path)

    def _get_all_titles(self) -> set:
        """Obtém todos os títulos validos e indexados fisicamente no vault."""
        titles = set()
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    match = re.search(r"^#\s+(.+)$", f.read(), re.MULTILINE)
                    if match:
                        titles.add(match.group(1).strip().lower())
            except Exception:
                pass
        return titles

    def run(self):
        """
        Validador de grafos final. O Markdown Generator (através da orientação da engine) já
        converteu conexões sugeridas no JSON e adicionou [[links]] nos bullets certos.
        O Linker foi rebaixado para atuar passivamente evitando poluição transversal:
        Monitorando o surgimento de links fantasmas/projetados para auditoria na tela do motor de observabilidade.
        """
        titles = self._get_all_titles()
        if not titles:
            return

        dead_links_detected = 0
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Conta dead-links que ainda estão pendentes
                links = re.findall(r"\[\[(.*?)\]\]", content)
                for link in links:
                     clean_link = link.lower().strip()
                     if clean_link not in titles:
                          dead_links_detected += 1
                          
            except Exception:
                pass
                
        if dead_links_detected > 0:
             print(f"[AutoLinker | Auditor] Validação de Lacunas: Identificados cerca de {dead_links_detected} Orphan-Links semânticos pre-setados.")
        else:
             print("[AutoLinker | Auditor] O tecido criado é autossuficiente (Sem links fantasmas/pendentes).")

    def cross_link_vault(self):
        """Varre os arquivos .md e insere wikilinks baseados em regex para conceitos existentes."""
        titles = self._get_all_titles()
        if not titles:
             return
             
        sorted_titles = sorted(list(titles), key=len, reverse=True)
        
        md_files = glob.glob(os.path.join(self.vault_path, "**", "*.md"), recursive=True)
        files_modified = 0
        total_links_created = 0
        
        for file_path in md_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                yaml_end_idx = 0
                match_yaml = re.search(r"^---\n.*?\n---\n", content, re.DOTALL | re.MULTILINE)
                if match_yaml:
                     yaml_end_idx = match_yaml.end()
                     
                relations_idx = content.find("## 🔗 Relações")
                if relations_idx == -1:
                     relations_idx = len(content)
                     
                yaml_part = content[:yaml_end_idx]
                body_part = content[yaml_end_idx:relations_idx]
                footer_part = content[relations_idx:]
                
                original_body = body_part
                file_name_clean = os.path.basename(file_path).replace(".md", "").replace("_", " ").lower()
                
                for t in sorted_titles:
                     if t == file_name_clean:
                         continue
                         
                     safe_t = re.escape(t)
                     # Regex ignorará matches precedidos diretamente por [ ou seguidos diretamente por ] (já estão em wikilinks)
                     # Adicionalmente garantindo word boundary para não engolir fragmentos de outras palavras
                     pattern = re.compile(rf"(?<!\[)(?<!\[\[)\b({safe_t})\b(?!\]\])(?!\])", re.IGNORECASE)
                     
                     def repl(m):
                         nonlocal total_links_created
                         total_links_created += 1
                         return f"[[{m.group(1)}]]"
                         
                     body_part = pattern.sub(repl, body_part)
                
                if body_part != original_body:
                     new_content = yaml_part + body_part + footer_part
                     with open(file_path, "w", encoding="utf-8") as f:
                          f.write(new_content)
                     files_modified += 1
            except Exception as e:
                print(f"[AutoLinker] Erro formatando {file_path}: {e}")
                
        print(f"[AutoLinker | Ativo] Cross-linking concluído em {files_modified} documentos.")
        print(f"[AutoLinker | Ativo] Criados {total_links_created} novos backlinks orgânicos através de pattern-matching local.")

    def semantic_link_vault(self, llm):
        """Varre os arquivos, vetoriza via LLM Embeddings + Cache, e liga arquivos semanticamente próximos (Stage 5)."""
        import json
        import math
        
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
                      print(f"[SemanticLinker] Vetorizando arquivo inédito/modificado: {file_name_clean}")
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
                 print(f"[SemanticLinker] Falha de extração vetorial em {file_path}: {e}")
                 
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
                  
                  vec_a = embeddings_db[path_a]["embedding"]
                  vec_b = embeddings_db[path_b]["embedding"]
                  
                  sim = cosine_sim(vec_a, vec_b)
                  if sim >= threshold:
                       title_a = embeddings_db[path_a]["title"].title()
                       title_b = embeddings_db[path_b]["title"].title()
                       
                       content_a = memory_content[path_a]
                       link_b = f"[[{title_b}]]"
                       if link_b.lower() not in content_a.lower():
                            if "## 🔗 Relações" in content_a:
                                content_a += f"\n- {link_b}  <!-- Sim: {sim*100:.1f}% -->"
                            else:
                                content_a += f"\n\n## 🔗 Relações\n- {link_b}  <!-- Sim: {sim*100:.1f}% -->"
                            memory_content[path_a] = content_a
                            files_modified.add(path_a)
                            total_semantic_links += 1
                            
                       content_b = memory_content[path_b]
                       link_a = f"[[{title_a}]]"
                       if link_a.lower() not in content_b.lower():
                            if "## 🔗 Relações" in content_b:
                                content_b += f"\n- {link_a}  <!-- Sim: {sim*100:.1f}% -->"
                            else:
                                content_b += f"\n\n## 🔗 Relações\n- {link_a}  <!-- Sim: {sim*100:.1f}% -->"
                            memory_content[path_b] = content_b
                            files_modified.add(path_b)
                            total_semantic_links += 1
                            
        for path in files_modified:
             with open(path, "w", encoding="utf-8") as f:
                  f.write(memory_content[path])
                  
        print(f"[SemanticLinker | Estágio 5] Concluído! Fez merge semântico em {len(files_modified)} ilhas.")
        print(f"[SemanticLinker | Estágio 5] Forjas puras criadas (Cosine > {threshold:.2f}): {total_semantic_links} conexões.")
