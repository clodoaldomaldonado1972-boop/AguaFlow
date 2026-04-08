import os
import sys

# 1. PEGAR O CAMINHO DA RAIZ (C:\AguaFlow)
# O abspath(__file__) pega o local deste script, o primeiro dirname pega 'utils'
# e o segundo dirname pega 'AguaFlow'
caminho_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. ADICIONAR À BUSCA DO PYTHON ANTES DO IMPORT
if caminho_raiz not in sys.path:
    sys.path.append(caminho_raiz)

# 3. AGORA O IMPORT FUNCIONARÁ
try:
    from database.database import Database
except ImportError:
    print("❌ Erro: Não foi possível localizar a pasta 'database'.")
    sys.exit(1)


def forcar_reset():
    """Limpa os dados locais para novos testes de campo."""
    try:
        with Database.get_db() as conn:
            cursor = conn.cursor()
            # Limpa as leituras
            cursor.execute(
                "UPDATE leituras SET valor = NULL, sincronizado = 0, data_leitura = NULL")
            # Limpa a fila de sincronização
            cursor.execute("DELETE FROM sync_queue")
            conn.commit()
            print("✅ [AGUAFLOW] Banco Local Resetado com Sucesso!")
    except Exception as e:
        print(f"❌ Erro ao processar reset: {e}")


if __name__ == "__main__":
    forcar_reset()
