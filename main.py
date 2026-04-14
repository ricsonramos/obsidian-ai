import argparse
from dotenv import load_dotenv
import os
import sys

# Garante que scripts usem ./ corretamente no module resolution
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.graph_engine import GraphEngine

def main():
    load_dotenv()
    
    # Criar .env se não existir pra evitar erros silêncios, ou apenas focar nos default getters.
    parser = argparse.ArgumentParser(description="Knowledge Engine CLI - Roteamento em Grafos MD")
    parser.add_argument("command", choices=["graph"], help="O comando a executar")
    parser.add_argument("topic", help="Topic base para a pesquisa e mapeamento em grafos")
    parser.add_argument("--depth", type=int, default=2, help="Profundidade da recursão de expansão via subconcepts")
    parser.add_argument("--dry-run", action="store_true", help="Executa e passa pelo LLM sem depositar no Vault Local")
    parser.add_argument("--resume", action="store_true", help="Recupera ultimo stage 1 salvo e pula requisicao do Gemini")
    parser.add_argument("--stage", choices=["all", "1", "2", "3"], default="all", help="Executa apenas o estagio demarcado (1=Decompose, 2=Expand, 3=Link)")
    
    args = parser.parse_args()
    
    if args.command == "graph":
        engine = GraphEngine(dry_run=args.dry_run, resume=args.resume, target_stage=args.stage)
        engine.run(args.topic, args.depth)

if __name__ == "__main__":
    main()
