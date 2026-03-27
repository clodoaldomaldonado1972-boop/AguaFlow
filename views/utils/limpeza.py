import os
import sqlite3
from database.database import Database

def realizar_limpeza_geral():
    print("🧹 Iniciando limpeza do ambiente AguaFlow...")

    # 1. Nome do arquivo do banco
    db_file = 'aguaflow.db'

    # 2. Remover o arquivo SQLite local se ele existir
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"✅ Arquivo '{db_file}' removido com sucesso.")
        except Exception as e:
            print(f"❌ Erro ao remover o arquivo: {e}")
    else:
        print("ℹ️ O arquivo de banco de dados não existia.")

    # 3. Limpar ficheiros temporários de QR Codes (se houver algum perdido)
    arquivos = os.listdir('.')
    for f in arquivos:
        if f.startswith("temp_qr_") and f.endswith(".png"):
            os.remove(f)
            print(f"🗑️ Temporário {f} removido.")

    # 4. Reinicializar o Banco de Dados (Cria as tabelas do zero)
    print("🗄️ Criando novo banco de dados e tabelas...")
    try:
        Database.init_db()
        print("✅ Estrutura de tabelas recriada.")
        
        # Opcional: Aqui podes chamar a função que insere as 96 unidades 
        # para o banco já nascer com os apartamentos cadastrados.
        print("🏢 Unidades prontas para novas leituras.")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar novo banco: {e}")

    print("\n🚀 Ambiente limpo e pronto para o Vivere Prudente!")

if __name__ == "__main__":
    confirmacao = input("Isso apagará TODAS as leituras locais. Confirmar? (s/n): ")
    if confirmacao.lower() == 's':
        realizar_limpeza_geral()
    else:
        print("Operação cancelada.")