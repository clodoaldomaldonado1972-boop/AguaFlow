"""
Testes automatizados para BackupManager (utils/backup.py):
  - listar_backups
  - restaurar_backup
"""

import os
import sqlite3
import tempfile
import zipfile
import shutil
import pytest

# Redirect Database.DB_PATH to temp before any import
_tmp_dir = tempfile.mkdtemp()
_tmp_db = os.path.join(_tmp_dir, "test_aguaflow.db")
_backup_dir = os.path.join(_tmp_dir, "Backups")

import database.database as _db_module
_db_module.Database.DB_PATH = _tmp_db

from database.database import Database
from utils.backup import BackupManager


def _criar_db_simples(path):
    """Cria um banco SQLite mínimo válido para testes."""
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS leituras (id INTEGER PRIMARY KEY, unidade_id TEXT)")
    conn.execute("INSERT INTO leituras (unidade_id) VALUES ('101')")
    conn.commit()
    conn.close()


def _criar_zip_backup(zip_path, db_path):
    """Empacota um banco SQLite em um ZIP com o nome aguaflow.db."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, arcname="aguaflow.db")


@pytest.fixture(autouse=True)
def ambiente_limpo():
    """Garante DB e pasta de backups limpos antes de cada teste."""
    os.makedirs(_backup_dir, exist_ok=True)
    _criar_db_simples(_tmp_db)
    Database.DB_PATH = _tmp_db
    yield
    # Limpeza
    for f in os.listdir(_backup_dir):
        os.remove(os.path.join(_backup_dir, f))
    for ext in ("", ".antes_restauracao", ".restore_tmp"):
        p = _tmp_db + ext
        if os.path.exists(p):
            os.remove(p)


# ---------------------------------------------------------------------------
# listar_backups
# ---------------------------------------------------------------------------

class TestListarBackups:
    def test_pasta_vazia_retorna_lista_vazia(self):
        # Aponta BackupManager para pasta vazia sem ZIPs
        orig = _db_module.Database.DB_PATH
        Database.DB_PATH = _tmp_db
        resultado = BackupManager.listar_backups()
        assert isinstance(resultado, list)
        assert len(resultado) == 0

    def test_lista_um_backup(self):
        zip_path = os.path.join(_backup_dir, "aguaflow_backup_2026-05-17_120000.zip")
        _criar_zip_backup(zip_path, _tmp_db)

        resultado = BackupManager.listar_backups()
        assert len(resultado) == 1
        assert resultado[0]["nome"] == "aguaflow_backup_2026-05-17_120000.zip"
        assert resultado[0]["tamanho_kb"] >= 0
        assert "data" in resultado[0]
        assert "arquivo" in resultado[0]

    def test_lista_multiplos_ordenados_mais_recente(self):
        nomes = [
            "aguaflow_backup_2026-05-15_080000.zip",
            "aguaflow_backup_2026-05-17_120000.zip",
            "aguaflow_backup_2026-05-16_090000.zip",
        ]
        for nome in nomes:
            _criar_zip_backup(os.path.join(_backup_dir, nome), _tmp_db)

        resultado = BackupManager.listar_backups()
        assert len(resultado) == 3
        nomes_resultado = [r["nome"] for r in resultado]
        # Deve estar em ordem decrescente (mais recente primeiro)
        assert nomes_resultado == sorted(nomes_resultado, reverse=True)

    def test_ignora_arquivos_nao_zip(self):
        # Cria arquivo que não é ZIP
        open(os.path.join(_backup_dir, "lixo.txt"), "w").close()
        _criar_zip_backup(os.path.join(_backup_dir, "valido.zip"), _tmp_db)

        resultado = BackupManager.listar_backups()
        assert len(resultado) == 1
        assert resultado[0]["nome"] == "valido.zip"


# ---------------------------------------------------------------------------
# restaurar_backup
# ---------------------------------------------------------------------------

class TestRestaurarBackup:
    def test_restaura_banco_corretamente(self):
        # Cria um banco "antigo" com dados distintos
        db_antigo = _tmp_db + ".antigo"
        conn = sqlite3.connect(db_antigo)
        conn.execute("CREATE TABLE IF NOT EXISTS leituras (id INTEGER PRIMARY KEY, unidade_id TEXT)")
        conn.execute("INSERT INTO leituras (unidade_id) VALUES ('UNIDADE_RESTAURADA')")
        conn.commit()
        conn.close()

        zip_path = os.path.join(_backup_dir, "backup_teste.zip")
        _criar_zip_backup(zip_path, db_antigo)
        os.remove(db_antigo)

        resultado = BackupManager.restaurar_backup(zip_path)
        assert resultado["sucesso"] is True

        conn = sqlite3.connect(_tmp_db)
        rows = conn.execute("SELECT unidade_id FROM leituras").fetchall()
        conn.close()
        unidades = [r[0] for r in rows]
        assert "UNIDADE_RESTAURADA" in unidades

    def test_arquivo_inexistente_retorna_erro(self):
        resultado = BackupManager.restaurar_backup("/caminho/que/nao/existe.zip")
        assert resultado["sucesso"] is False
        assert "não encontrado" in resultado["mensagem"].lower()

    def test_zip_sem_db_retorna_erro(self):
        zip_path = os.path.join(_backup_dir, "zip_invalido.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("outro_arquivo.txt", "conteudo qualquer")

        resultado = BackupManager.restaurar_backup(zip_path)
        assert resultado["sucesso"] is False
        assert "aguaflow.db" in resultado["mensagem"]

    def test_banco_atual_preservado_em_falha(self):
        """Se o ZIP é inválido, o banco original deve permanecer intacto."""
        # Registra dado original
        conn = sqlite3.connect(_tmp_db)
        conn.execute("CREATE TABLE IF NOT EXISTS leituras (id INTEGER PRIMARY KEY, unidade_id TEXT)")
        conn.execute("INSERT OR IGNORE INTO leituras (unidade_id) VALUES ('DADO_ORIGINAL')")
        conn.commit()
        conn.close()

        # ZIP sem aguaflow.db
        zip_invalido = os.path.join(_backup_dir, "invalido.zip")
        with zipfile.ZipFile(zip_invalido, "w") as zf:
            zf.writestr("nada.txt", "vazio")

        BackupManager.restaurar_backup(zip_invalido)

        # Banco original deve continuar acessível
        conn = sqlite3.connect(_tmp_db)
        rows = conn.execute("SELECT unidade_id FROM leituras").fetchall()
        conn.close()
        assert any(r[0] == "DADO_ORIGINAL" for r in rows)

    def test_mensagem_sucesso_contem_nome_arquivo(self):
        zip_path = os.path.join(_backup_dir, "meu_backup_especial.zip")
        _criar_zip_backup(zip_path, _tmp_db)

        resultado = BackupManager.restaurar_backup(zip_path)
        assert resultado["sucesso"] is True
        assert "meu_backup_especial.zip" in resultado["mensagem"]
