import os
import sqlite3
from datetime import datetime

# Importação protegida: Como o arquivo está em 'utils', ele sobe um nível para achar 'database'
try:
    from database.database import Database
except (ImportError, ValueError):
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from database.database import Database

def executar_backup_seguranca():
    """Realiza uma cópia consistente e segura do banco de dados local."""
    # Garante que pegamos o caminho correto do banco
    base_dir = getattr(Database, 'BASE_DIR', os.path.dirname(os.path.abspath(__file__)))
    pasta_backup = os.path.join(os.path.dirname(base_dir), "Backups")
    
    source_conn = None
    dest_conn = None
    
    try:
        if not os.path.exists(pasta_backup):
            os.makedirs(pasta_backup)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        arquivo_origem = Database.DB_PATH
        arquivo_destino = os.path.join(pasta_backup, f"aguaflow_backup_{timestamp}.db")

        if not os.path.exists(arquivo_origem):
            print(f"❌ Erro: Arquivo {arquivo_origem} não encontrado.")
            return False

        # Backup atômico do SQLite
        source_conn = sqlite3.connect(arquivo_origem)
        dest_conn = sqlite3.connect(arquivo_destino)

        with dest_conn:
            source_conn.backup(dest_conn)

        print(f"✅ Backup concluído: {arquivo_destino}")
        return True

    except Exception as e:
        print(f"❌ Falha crítica no backup: {e}")
        return False
        
    finally:
        if source_conn:
            source_conn.close()
        if dest_conn:
            dest_conn.close()

def limpar_backups_antigos(limite_dias=7):
    """Remove backups antigos para poupar espaço."""
    base_dir = getattr(Database, 'BASE_DIR', os.getcwd())
    pasta_backup = os.path.join(os.path.dirname(base_dir), "Backups")
    
    if not os.path.exists(pasta_backup):
        return

    agora = datetime.now().timestamp()
    for ficheiro in os.listdir(pasta_backup):
        caminho_completo = os.path.join(pasta_backup, ficheiro)
        if os.path.isfile(caminho_completo):
            tempo_ficheiro = os.path.getmtime(caminho_completo)
            if (agora - tempo_ficheiro) > (limite_dias * 86400):
                os.remove(caminho_completo)
                print(f"🗑️ Backup antigo removido: {ficheiro}")