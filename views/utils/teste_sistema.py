import pytesseract
from sync_engine import SyncEngine
from database.database import Database

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def realizar_teste_completo():
    print("--- INICIANDO TESTE INTEGRADO AGUAFLOW ---")

    # Passo A: Inicializar Banco
    Database.init_db()
    print("✅ Banco SQLite pronto.")

    # Passo B: Simular uma leitura de sucesso
    unidade_teste = "Apto 166"  # Ajustado para o padrão do seu init_db
    valor_simulado = "00452.10"
    tipo_teste = "Água"  # O argumento que estava faltando!

    print(f"📸 Simulando leitura da Unidade {unidade_teste} ({tipo_teste})...")

    # Agora com os 3 argumentos: unidade, valor, tipo
    res = Database.registrar_leitura(unidade_teste, valor_simulado, tipo_teste)

    if res['sucesso']:
        print(f"✅ Leitura salva no SQLite local.")
    else:
        print(f"❌ Falha ao salvar no banco: {res.get('mensagem')}")
        return

    # Passo C: Testar Sincronização
    print("📡 Iniciando sincronização com a Nuvem...")
    SyncEngine.sincronizar_tudo()

    print("\n--- TESTE FINALIZADO ---")


if __name__ == "__main__":
    realizar_teste_completo()
