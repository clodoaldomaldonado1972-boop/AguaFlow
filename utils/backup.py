import os
import sqlite3
import shutil
import zipfile
import gc
import logging
from datetime import datetime
from database.database import Database

logger = logging.getLogger(__name__)

# Pasta de relatórios — mesma definida no relatorio_engine
RELATORIOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "relatorios")


class BackupManager:
    """
    Gere a segurança física dos dados locais do AguaFlow.
    Realiza backups atómicos do banco SQLite e dos relatórios gerados.
    """

    @staticmethod
    def executar_backup_seguranca():
        """
        Backup completo: banco SQLite + arquivos da pasta relatorios/.
        Gera um arquivo ZIP único com timestamp em database/Backups/.
        Retorna True em caso de sucesso.
        """
        base_dir = os.path.dirname(Database.DB_PATH)
        pasta_backup = os.path.join(base_dir, "Backups")
        source_conn = None

        try:
            os.makedirs(pasta_backup, exist_ok=True)

            if not os.path.exists(Database.DB_PATH):
                logger.error("Backup: banco SQLite nao encontrado.")
                return False

            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            arquivo_zip = os.path.join(pasta_backup, f"aguaflow_backup_{timestamp}.zip")

            with zipfile.ZipFile(arquivo_zip, 'w', zipfile.ZIP_DEFLATED) as zf:

                # 1. Banco SQLite — backup atômico para arquivo temporário
                db_temp = arquivo_zip + ".db.tmp"
                try:
                    source_conn = sqlite3.connect(Database.DB_PATH)
                    dest_conn = sqlite3.connect(db_temp)
                    with dest_conn:
                        source_conn.backup(dest_conn)
                    dest_conn.close()
                    zf.write(db_temp, arcname="aguaflow.db")
                    logger.info("Backup: banco SQLite incluido no ZIP.")
                finally:
                    if source_conn:
                        source_conn.close()
                    if os.path.exists(db_temp):
                        os.remove(db_temp)

                # 2. Arquivos da pasta relatorios/
                relatorios_incluidos = 0
                if os.path.isdir(RELATORIOS_DIR):
                    for nome in os.listdir(RELATORIOS_DIR):
                        caminho = os.path.join(RELATORIOS_DIR, nome)
                        if os.path.isfile(caminho):
                            zf.write(caminho, arcname=os.path.join("relatorios", nome))
                            relatorios_incluidos += 1

                logger.info(
                    f"Backup: {relatorios_incluidos} relatorio(s) incluido(s) no ZIP.")

            tamanho_kb = os.path.getsize(arquivo_zip) // 1024
            print(f"[OK] Backup concluido: {os.path.basename(arquivo_zip)} ({tamanho_kb} KB)")
            logger.info(f"Backup ZIP criado: {arquivo_zip} ({tamanho_kb} KB)")

            BackupManager.limpar_backups_antigos(pasta_backup)
            return True

        except Exception as e:
            logger.error(f"Falha no backup: {e}", exc_info=True)
            print(f"[FALHA] Backup: {e}")
            return False
        finally:
            gc.collect()

    @staticmethod
    def inspecionar_ultimo_backup():
        """
        Retorna informações sobre o backup mais recente:
        {'arquivo': str, 'tamanho_kb': int, 'conteudo': [str], 'data': str}
        """
        base_dir = os.path.dirname(Database.DB_PATH)
        pasta_backup = os.path.join(base_dir, "Backups")

        if not os.path.isdir(pasta_backup):
            return None

        zips = sorted(
            [f for f in os.listdir(pasta_backup) if f.endswith(".zip")],
            reverse=True
        )
        if not zips:
            return None

        ultimo = os.path.join(pasta_backup, zips[0])
        try:
            with zipfile.ZipFile(ultimo, 'r') as zf:
                conteudo = zf.namelist()
            return {
                "arquivo":    ultimo,
                "tamanho_kb": os.path.getsize(ultimo) // 1024,
                "conteudo":   conteudo,
                "data":       datetime.fromtimestamp(
                                  os.path.getmtime(ultimo)
                              ).strftime("%d/%m/%Y %H:%M:%S"),
            }
        except Exception as e:
            logger.error(f"Erro ao inspecionar backup: {e}")
            return None

    @staticmethod
    def limpar_backups_antigos(pasta_backup, limite_dias=30):
        """Remove backups ZIP com mais de 30 dias."""
        try:
            agora = datetime.now().timestamp()
            for ficheiro in os.listdir(pasta_backup):
                caminho = os.path.join(pasta_backup, ficheiro)
                if os.path.isfile(caminho) and ficheiro.endswith(".zip"):
                    idade_dias = (agora - os.path.getmtime(caminho)) / 86400
                    if idade_dias > limite_dias:
                        os.remove(caminho)
                        logger.info(f"Backup antigo removido: {ficheiro}")
        except Exception:
            pass


# Alias de retrocompatibilidade
executar_backup_seguranca = BackupManager.executar_backup_seguranca