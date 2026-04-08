# Nome ajustado para seu arquivo atual[cite: 1, 15]
from utils.sync_service import SyncEngine
from database.database import Database
import pytesseract
import os
import sys

# Garante que o Python encontre os módulos na pasta raiz ao rodar da pasta tests/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- IMPORTS CORRIGIDOS PARA A NOVA ESTRUTURA ---

# Configuração do Tesseract para Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def realizar_teste_completo():
    print("--- INICIANDO TESTE INTEGRADO AGUAFLOW ---")

    # Passo A: Inicializar Banco e Unidades (Aptos 166 ao 11)[cite: 12, 15]
    Database.init_db()
    print("✅ Banco SQLite inicializado com as unidades do Vivere Prudente.")

    # Passo B: Simular uma leitura de sucesso[cite: 15]
    unidade_teste = "Apto 166"
    valor_simulado = "00452.10"
    tipo_teste = "Água"

    print(
        f"📸 Simulando registro: {unidade_teste} | Valor: {valor_simulado} | Tipo: {tipo_teste}")

    # Registro utilizando a lógica revisada do database.py[cite: 12, 15]
    res = Database.registrar_leitura(unidade_teste, valor_simulado, tipo_teste)

    if res['sucesso']:
        print(f"✅ Leitura salva com sucesso no SQLite local.")
    else:
        print(f"❌ Falha ao salvar no banco: {res.get('mensagem')}")
        return

    # Passo C: Testar Sincronização com Supabase[cite: 15]
    print("📡 Iniciando sincronização via SyncEngine (Pasta Utils)...")
    try:
        SyncEngine.sincronizar_tudo()
        print("✅ Processo de sincronização finalizado.")
    except Exception as e:
        print(f"⚠️ Erro na sincronização: {e} (Verifique seu .env)")

    print("\n--- TESTE FINALIZADO ---")


if __name__ == "__main__":
    realizar_teste_completo()
