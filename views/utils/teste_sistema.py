import pytesseract
from database.database import Database
from sync_engine import SyncEngine
from database.sync_engine import SyncEngine

# 1. Configura o caminho que acabamos de validar
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def realizar_teste_completo():
    print("--- INICIANDO TESTE INTEGRADO AGUAFLOW ---")

    # Passo A: Inicializar Banco
    Database.init_db()
    print("✅ Banco SQLite pronto.")

    # Passo B: Simular uma leitura de sucesso (Apartamento 166)
    # Aqui simulamos o que o leitor_ocr.py faria
    unidade_teste = "166"
    valor_simulado = "00452.10"

    print(f"📸 Simulando leitura da Unidade {unidade_teste}...")
    res = Database.registrar_leitura(unidade_teste, valor_simulado)

    if res['sucesso']:
        print(f"✅ Leitura salva no SQLite com status: {res['mensagem']}")
    else:
        print(f"❌ Falha ao salvar no banco: {res['mensagem']}")
        return

    # Passo C: Testar Sincronização
    print("📡 Iniciando sincronização com a Nuvem...")
    SyncEngine.sincronizar_tudo()

    print("\n--- TESTE FINALIZADO ---")
    print("Verifique se o dado apareceu no seu painel do Supabase!")


if __name__ == "__main__":
    realizar_teste_completo()
