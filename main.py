import argparse
from dotenv import load_dotenv
import os
import sys

# Garante que scripts usem ./ corretamente no module resolution
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.graph_engine import GraphEngine

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Knowledge Engine CLI - Construtor de Árvores de Estudo (MoC)")
    parser.add_argument("command", choices=["graph"], help="O comando a executar")
    parser.add_argument("topic", help="Conceito base para iniciar mapeamento de ramificações")
    parser.add_argument("--depth", type=int, default=2, help="Profundidade da recursão arquitetural (evite maior que 3)")
    parser.add_argument("--dry-run", action="store_true", help="Executa e lista a árvore inferida sem gravar no disco")
    parser.add_argument("--resume", action="store_true", help="Recupera ultimo stage 1 salvo")
    parser.add_argument("--stage", choices=["all", "1", "2", "3"], default="all", help="Executar estagios limitados")
    parser.add_argument("--max-tokens", type=int, default=2000, help="Teto financeiro: aborta a arvore se os tokens escalarem.")
    
    args = parser.parse_args()
    
    if args.command == "graph":
        engine = GraphEngine(dry_run=args.dry_run, 
                             resume=args.resume, 
                             target_stage=args.stage,
                             max_tokens_budget=args.max_tokens)
        engine.run(args.topic, args.depth)

if __name__ == "__main__":
    main()
