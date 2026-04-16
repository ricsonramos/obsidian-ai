import subprocess
import os
import time
import sys
import signal

def start():
    print("\n" + "="*40)
    print("🌌 ANTIGRAVITY ECOSYSTEM - STARTUP")
    print("="*40 + "\n")

    # 1. Iniciar Backend (FastAPI)
    print("🔌 [BACKEND] Iniciando API em http://localhost:8000...")
    backend = subprocess.Popen([sys.executable, "api.py"])

    # 2. Iniciar Frontend (Next.js)
    print("🎨 [FRONTEND] Iniciando Next.js Dashboard...")
    # No Windows, usamos shell=True para encontrar o npm no PATH
    frontend = subprocess.Popen("npm run dev", cwd="gui", shell=True)

    print("\n🚀 SUCESSO! Sistema rodando em paralelo.")
    print("👉 Interface: http://localhost:3000")
    print("👉 Documentação API: http://localhost:8000/docs")
    print("\n[INFO] Todas as mensagens do sistema aparecerão abaixo:\n")

    try:
        # Loop para manter o script vivo
        while True:
            time.sleep(1)
            if backend.poll() is not None:
                print("\n❌ O Backend parou inesperadamente.")
                break
            if frontend.poll() is not None:
                print("\n❌ O Frontend parou inesperadamente.")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 [SHUTDOWN] Desligando Antigravity...")
        backend.terminate()
        
        # O frontend (Next.js) as vezes precisa de um kill mais forte no Windows
        if os.name == 'nt':
            subprocess.run(f"taskkill /F /T /PID {frontend.pid}", shell=True, capture_output=True)
            subprocess.run(f"taskkill /F /T /PID {backend.pid}", shell=True, capture_output=True)
        else:
            frontend.terminate()
            
        print("✨ Motores desligados. Até a próxima missão.")

if __name__ == "__main__":
    start()
