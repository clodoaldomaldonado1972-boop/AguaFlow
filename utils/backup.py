import os
import sqlite3
import shutil
import gc
from datetime import datetime
from database.database import Database

class BackupManager:
    """
    Gere a segurança física dos dados locais do AguaFlow.
    Realiza backups atómicos para prevenir perda de dados no Vivere Prudente.
    """

    @staticmethod
    def executar_backup_seguranca():
        """Realiza uma cópia consistente e segura da base de dados."""
        # Define pasta de backup (mesmo nível da pasta database)
        base_dir = os.path.dirname(Database.DB_PATH)
        pasta_backup = os.path.join(base_dir, "Backups")
        
        source_conn = None
        dest_conn = None
        
        try:
            if not os.path.exists(pasta_backup):
                os.makedirs(pasta_backup)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            arquivo_destino = os.path.join(pasta_backup, f"aguaflow_backup_{timestamp}.db")

            if not os.path.exists(Database.DB_PATH):
                return False

            # Backup Atómico (Cópia bit-a-bit segura)
            source_conn = sqlite3.connect(Database.DB_PATH)
            dest_conn = sqlite3.connect(arquivo_destino)

            with dest_conn:
                source_conn.backup(dest_conn)

            print(f"✅ Backup concluído: {arquivo_destino}")
            
            # Limpa backups com mais de 7 dias para poupar espaço no Android
            BackupManager.limpar_backups_antigos(pasta_backup)
            return True

        except Exception as e:
            print(f"❌ Falha no backup: {e}")
            return False
        finally:
            if source_conn: source_conn.close()
            if dest_conn: dest_conn.close()
            gc.collect()

    @staticmethod
    def limpar_backups_antigos(pasta_backup, limite_dias=7):
        """Remove ficheiros de backup obsoletos."""
        try:
            agora = datetime.now().timestamp()
            for ficheiro in os.listdir(pasta_backup):
                caminho = os.path.join(pasta_backup, ficheiro)
                if os.path.isfile(caminho):
                    idade_dias = (agora - os.path.getmtime(caminho)) / (24 * 3600)
                    if idade_dias > limite_dias:
                        os.remove(caminho)
        except:
            pass # Falha silenciosa na limpeza para não travar o app
# No final do arquivo, fora da classe BackupManager:
executar_backup_seguranca = BackupManager.executar_backup_seguranca