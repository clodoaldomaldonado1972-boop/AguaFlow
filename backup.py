import shutil
import os
from datetime import datetime


def executar_backup_seguranca():
    """Faz uma cópia física do banco de dados para a pasta Backups."""
    pasta_backup = "Backups"
    if not os.path.exists(pasta_backup):
        os.makedirs(pasta_backup)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    arquivo_origem = "aguaflow.db"
    arquivo_destino = os.path.join(
        pasta_backup, f"aguaflow_backup_{timestamp}.db")

    try:
        if os.path.exists(arquivo_origem):
            shutil.copy2(arquivo_origem, arquivo_destino)
            print(f"✅ Backup concluído com sucesso: {arquivo_destino}")
            return True
        else:
            print("❌ Erro: Arquivo aguaflow.db não encontrado para backup.")
            return False
    except Exception as e:
        print(f"❌ Falha crítica no backup: {e}")
        return False


# O bloco abaixo garante que o teste SÓ rode se você executar o backup.py diretamente
if __name__ == "__main__":
    print("Iniciando teste manual de backup...")
    executar_backup_seguranca()
