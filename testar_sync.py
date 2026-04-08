from utils.sync_engine import SyncEngine
import os
import sys

# Ajusta o caminho para localizar as pastas
sys.path.append(os.path.abspath(os.path.dirname(__file__)))


def disparar_sincronia():
    print("☁️ Conectando ao Supabase...")
    resultado = SyncEngine.sincronizar_tudo()
    print(f"\nStatus: {resultado}")


if __name__ == "__main__":
    disparar_sincronia()
