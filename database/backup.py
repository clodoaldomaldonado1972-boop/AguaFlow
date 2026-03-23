import os
import sqlite3
from datetime import datetime


def executar_backup_seguranca():
    """Faz uma cópia consistente do banco de dados usando API do SQLite."""
    pasta_backup = "Backups"
    if not os.path.exists(pasta_backup):
        os.makedirs(pasta_backup)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    arquivo_origem = "aguaflow.db"
    arquivo_destino = os.path.join(
        pasta_backup, f"aguaflow_backup_{timestamp}.db")

    source_conn = None
    dest_conn = None

    try:
        if not os.path.exists(arquivo_origem):
            print("❌ Erro: Arquivo aguaflow.db não encontrado para backup.")
            return False

        source_conn = sqlite3.connect(arquivo_origem)
        dest_conn = sqlite3.connect(arquivo_destino)

        # Backup consistente via API SQLite
        source_conn.backup(dest_conn)

        print(f"✅ Backup concluído com sucesso: {arquivo_destino}")
        return True

    except Exception as e:
        print(f"❌ Falha crítica no backup: {e}")
        return False
    finally:
        if source_conn:
            source_conn.close()
        if dest_conn:
            dest_conn.close()


if __name__ == "__main__":
    print("Iniciando teste manual de backup...")
    executar_backup_seguranca()
