import argparse
from dotenv import load_dotenv
import os
import sys

# Garante que scripts usem ./ corretamente no module resolution
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.graph_engine import GraphEngine

def main():
    load_dotenv()

    # Configurações de Segurança e Custo
    depth_default = int(os.getenv("DEFAULT_DEPTH", "2"))
    max_tokens_default = int(os.getenv("MAX_TOKENS_BUDGET", "5000")) 

    parser = argparse.ArgumentParser(
        description="Knowledge Engine CLI - Arquiteto Taxonomista para Second Brain",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Comandos principais
    parser.add_argument("command", choices=["graph", "link", "export"], help="Comando de execução")
    parser.add_argument("topic", nargs="?", default="", help="Conceito base para o mapeamento")

    # Parâmetros de Controle (Rigor Acadêmico)
    parser.add_argument("--depth", type=int, default=depth_default, 
                        help="Profundidade da árvore. NOTA: Valores > 2 geram alta redundância.")
    parser.add_argument("--mode", choices=["beginner", "advanced"], default="beginner",
                        help="Nível de partida do conhecimento (Zero Absoluto vs. Expansão Técnica)")
    parser.add_argument("--max-tokens", type=int, default=max_tokens_default, 
                        help="Teto financeiro para evitar loop infinito de tokens.")
    
    # Flags de Operação
    parser.add_argument("--dry-run", action="store_true", help="Simula a árvore sem criar arquivos .md")
    parser.add_argument("--resume", action="store_true", help="Retoma do último checkpoint (Stage 1)")
    parser.add_argument("--notebook-lm", action="store_true", 
                        help="Prepara estrutura de arquivos otimizada para upload no NotebookLM")

    args = parser.parse_args()

    # Validação de Premissas Críticas
    if args.command == "graph" and not args.topic:
        print("❌ ERRO CRÍTICO: O comando 'graph' exige um tópico base.")
        sys.exit(1)

    if args.depth > 3:
        print(f"⚠️ AVISO: Profundidade {args.depth} detectada. Risco de explosão horizontal e custo elevado.")
        confirm = input("Deseja continuar? (s/n): ")
        if confirm.lower() != 's': sys.exit(0)

    # Inicialização da Engine
    # Note que passamos o 'mode' para a engine decidir a densidade da taxonomia
    engine = GraphEngine(
        dry_run=args.dry_run, 
        resume=args.resume, 
        max_tokens_budget=args.max_tokens,
        user_mode=args.mode,
        notebook_lm_prep=args.notebook_lm
    )

    try:
        if args.command == "graph":
            print(f"🚀 Iniciando Mapeamento: '{args.topic}' (Modo: {args.mode}, Profundidade: {args.depth})")
            engine.run(args.topic, args.depth)
        
        elif args.command == "link":
            print("🔗 Executando AutoLinker (Otimização de Grafos)...")
            engine.run(args.topic or "AutoLinker Pass", args.depth)
            
        elif args.command == "export":
            print("📦 Consolidando base de conhecimento para NotebookLM...")
            # Lógica de exportação seria chamada aqui
            engine.export_for_notebook()

    except Exception as e:
        print(f"💥 FALHA NA EXECUÇÃO: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
