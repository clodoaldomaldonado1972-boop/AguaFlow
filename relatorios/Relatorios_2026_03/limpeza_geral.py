import sqlite3
import os

def limpar_tudo():
    print("--- 🛠️ FAXINA AGUAFLOW ---")
    
    # 1. Tenta deletar o banco antigo para eliminar erros de 'coluna não encontrada'
    if os.path.exists("aguaflow.db"):
        try:
            os.remove("aguaflow.db")
            print("✅ Banco de dados antigo removido (Limpeza de Colunas).")
        except:
            print("⚠️ Feche o VS Code ou o App para conseguir apagar o banco.")
            return

    # 2. Se não quiser apagar o banco, vamos apenas destravar o 166 via SQL
    try:
        conn = sqlite3.connect("aguaflow.db")
        cursor = conn.cursor()
        
        # Cria a tabela caso ela não exista após o delete
        cursor.execute("UPDATE leituras SET status = 'CONCLUIDO' WHERE unidade = '166'")
        conn.commit()
        conn.close()
        print("✅ Unidade 166 marcada como CONCLUÍDA.")
    except Exception as e:
        print(f"ℹ️ Info: {e}")

if __name__ == "__main__":
    limpar_tudo()