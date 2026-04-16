import argparse
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.graph_engine import GraphEngine
from core.research_manager import ResearchManager


def main():
    load_dotenv()

    depth_default = int(os.getenv("DEFAULT_DEPTH", "2"))
    max_tokens_default = int(os.getenv("MAX_TOKENS_BUDGET", "2000"))
    vault_path = os.getenv("VAULT_PATH", "./vault")

    parser = argparse.ArgumentParser(
        description="Antigravity — Sistema Autônomo de Gestão de Conhecimento para Obsidian"
    )
    parser.add_argument(
        "command",
        choices=["graph", "link", "research", "sanitize"],
        help=(
            "graph   → Mapeia tema e gera notas no vault\n"
            "link    → Executa cross-link e semantic bridge\n"
            "research→ Gera research_list.txt com queries NotebookLM\n"
            "sanitize→ Limpa e normaliza nomes de arquivos no vault"
        ),
    )
    parser.add_argument(
        "topic",
        nargs="?",
        default="",
        help="Conceito base para mapeamento (obrigatório para 'graph')",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=depth_default,
        help="Profundidade máxima de recursão (padrão: 2)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula a execução sem gravar nenhum arquivo no vault",
    )
    parser.add_argument(
        "--stage",
        choices=["all", "1", "2", "3", "4", "5"],
        default="all",
        help="Executa apenas os estágios selecionados",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=max_tokens_default,
        help="Limite de tokens estimados antes de abortar a expansão",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Executa automaticamente o enriquecimento RAG via Ollama após gerar o grafo",
    )

    args = parser.parse_args()

    # ── graph ──────────────────────────────────────────────────────
    if args.command == "graph":
        if not args.topic:
            print("❌ Erro: O comando 'graph' exige um tópico. Ex: python main.py graph \"Machine Learning\"")
            sys.exit(1)

        engine = GraphEngine(
            dry_run=args.dry_run,
            resume=False,
            target_stage=args.stage,
            max_tokens_budget=args.max_tokens,
        )
        engine.run(args.topic, args.depth)
        
        if args.enrich:
            print("\n🚀 Iniciando Enriquecimento RAG automático...")
            from core.ollama_rag import OllamaRAG
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "llama3")
            rag = OllamaRAG(host, model)
            
            import glob
            md_files = glob.glob(os.path.join(vault_path, "**", "*.md"), recursive=True)
            for f in md_files:
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        if 'status: "waiting_ollama_rag"' in file.read():
                            rag.enrich_note(f)
                except: pass

    # ── link ───────────────────────────────────────────────────────
    elif args.command == "link":
        t_stage = args.stage if args.stage != "all" else "link_all"
        engine = GraphEngine(
            dry_run=args.dry_run,
            resume=False,
            target_stage=t_stage,
            max_tokens_budget=args.max_tokens,
        )
        engine.run(args.topic or "AutoLinker Pass", args.depth)

    # ── research ───────────────────────────────────────────────────
    elif args.command == "research":
        manager = ResearchManager(vault_path=vault_path)
        output_path = manager.generate_manifest()
        print(f"\n✅ research_list.txt gerado em:\n   {output_path}")
        print("\nPróximos passos:")
        print("  1. Use as queries acima para baixar PDFs (ArXiv, Z-Library, Google Scholar)")
        print("  2. Faça upload dos PDFs no NotebookLM e gere o resumo (Guide/Audio)")
        print("  3. Cole o resumo na nota do Obsidian e altere: status: research → status: learned")

    # ── sanitize ───────────────────────────────────────────────────
    elif args.command == "sanitize":
        from core.vault_manager import VaultManager
        vm = VaultManager(vault_path)
        vm.sanitize_vault()

    # ── enrich (RAG) ───────────────────────────────────────────────
    elif args.command == "enrich":
        from core.ollama_rag import OllamaRAG
        from core.vault_manager import VaultManager
        
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        model = os.getenv("OLLAMA_MODEL", "llama3")
        
        rag = OllamaRAG(host, model)
        vm = VaultManager(vault_path)
        
        print("🔍 Buscando notas pendentes de processamento RAG...")
        # Varre o vault em busca de notas com status "waiting_ollama_rag"
        import glob
        md_files = glob.glob(os.path.join(vault_path, "**", "*.md"), recursive=True)
        
        for f in md_files:
            try:
                with open(f, "r", encoding="utf-8") as file:
                    if 'status: "waiting_ollama_rag"' in file.read():
                        rag.enrich_note(f)
            except Exception as e:
                print(f"Erro ao processar {f}: {e}")


if __name__ == "__main__":
    main()
