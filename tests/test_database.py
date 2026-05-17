"""
Testes automatizados para os métodos do Database adicionados na sessão de 17/05/2026:
  - editar_leitura
  - deletar_leitura
  - buscar_leituras_filtradas
  - schema_version (criado em inicializar_tabelas)
"""

import os
import sqlite3
import tempfile
import pytest
from datetime import datetime

# Apontamos DB_PATH para um arquivo temporário ANTES de importar Database
_tmp_dir = tempfile.mkdtemp()
_tmp_db = os.path.join(_tmp_dir, "test_aguaflow.db")

# Monkeypatch no nível de módulo (antes do import)
import database.database as _db_module
_db_module.Database.DB_PATH = _tmp_db

from database.database import Database


@pytest.fixture(autouse=True)
def banco_limpo():
    """Recria o banco do zero antes de cada teste."""
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)
    Database.DB_PATH = _tmp_db
    Database.inicializar_tabelas()
    yield
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)


def _inserir_leitura(unidade="101", agua=100.0, gas=50.0, mes=None):
    """Helper: insere uma leitura e retorna o id."""
    mes = mes or datetime.now().strftime("%Y-%m")
    data = f"{mes}-15 10:00:00"
    with Database.get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO leituras
               (unidade_id, leitura_agua, leitura_gas, tipo, data_hora_coleta, sincronizado, valor_leitura)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (unidade, agua, gas, "AGUA", data, 1, agua),
        )
        conn.commit()
        return cur.lastrowid


# ---------------------------------------------------------------------------
# schema_version
# ---------------------------------------------------------------------------

class TestSchemaVersion:
    def test_tabela_criada(self):
        with Database.get_db() as conn:
            tabelas = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
        assert "schema_version" in tabelas

    def test_versao_registrada(self):
        with Database.get_db() as conn:
            v = conn.execute(
                "SELECT MAX(version) FROM schema_version"
            ).fetchone()[0]
        assert v is not None and v >= 1


# ---------------------------------------------------------------------------
# editar_leitura
# ---------------------------------------------------------------------------

class TestEditarLeitura:
    def test_edita_valores(self):
        lid = _inserir_leitura(agua=100.0, gas=50.0)
        ok = Database.editar_leitura(lid, 200.0, 75.5)
        assert ok is True

        with Database.get_db() as conn:
            row = conn.execute(
                "SELECT leitura_agua, leitura_gas FROM leituras WHERE id=?", (lid,)
            ).fetchone()
        assert row["leitura_agua"] == 200.0
        assert row["leitura_gas"] == 75.5

    def test_marca_nao_sincronizado(self):
        lid = _inserir_leitura()
        # A leitura foi inserida com sincronizado=1
        Database.editar_leitura(lid, 999.0, None)

        with Database.get_db() as conn:
            sinc = conn.execute(
                "SELECT sincronizado FROM leituras WHERE id=?", (lid,)
            ).fetchone()[0]
        assert sinc == 0

    def test_edita_para_none(self):
        lid = _inserir_leitura(agua=100.0, gas=50.0)
        ok = Database.editar_leitura(lid, None, None)
        assert ok is True

        with Database.get_db() as conn:
            row = conn.execute(
                "SELECT leitura_agua, leitura_gas FROM leituras WHERE id=?", (lid,)
            ).fetchone()
        assert row["leitura_agua"] is None
        assert row["leitura_gas"] is None

    def test_id_inexistente_retorna_false(self):
        ok = Database.editar_leitura(99999, 1.0, 1.0)
        assert ok is False


# ---------------------------------------------------------------------------
# deletar_leitura
# ---------------------------------------------------------------------------

class TestDeletarLeitura:
    def test_deleta_existente(self):
        lid = _inserir_leitura()
        ok = Database.deletar_leitura(lid)
        assert ok is True

        with Database.get_db() as conn:
            row = conn.execute(
                "SELECT id FROM leituras WHERE id=?", (lid,)
            ).fetchone()
        assert row is None

    def test_id_inexistente_retorna_false(self):
        ok = Database.deletar_leitura(99999)
        assert ok is False

    def test_deleta_apenas_alvo(self):
        lid1 = _inserir_leitura(unidade="101")
        lid2 = _inserir_leitura(unidade="102")
        Database.deletar_leitura(lid1)

        with Database.get_db() as conn:
            rows = conn.execute("SELECT id FROM leituras").fetchall()
        ids = [r[0] for r in rows]
        assert lid1 not in ids
        assert lid2 in ids


# ---------------------------------------------------------------------------
# buscar_leituras_filtradas
# ---------------------------------------------------------------------------

class TestBuscarLeiturasFiltradas:
    def setup_method(self):
        mes_atual = datetime.now().strftime("%Y-%m")
        _inserir_leitura(unidade="101", agua=100.0, mes=mes_atual)
        _inserir_leitura(unidade="102", agua=200.0, mes=mes_atual)
        _inserir_leitura(unidade="201", agua=300.0, mes=mes_atual)

    def test_sem_filtro_retorna_todos(self):
        rows = Database.buscar_leituras_filtradas()
        assert len(rows) == 3

    def test_filtro_unidade(self):
        rows = Database.buscar_leituras_filtradas(unidade="101")
        assert len(rows) == 1
        assert rows[0]["unidade_id"] == "101"

    def test_filtro_mes(self):
        mes = datetime.now().strftime("%Y-%m")
        rows = Database.buscar_leituras_filtradas(mes=mes)
        assert len(rows) == 3

    def test_filtro_mes_inexistente(self):
        rows = Database.buscar_leituras_filtradas(mes="1900-01")
        assert len(rows) == 0

    def test_filtro_texto_unidade(self):
        rows = Database.buscar_leituras_filtradas(texto="10")
        unidades = {r["unidade_id"] for r in rows}
        assert "101" in unidades
        assert "102" in unidades
        assert "201" not in unidades

    def test_filtro_combinado_unidade_e_mes(self):
        mes = datetime.now().strftime("%Y-%m")
        rows = Database.buscar_leituras_filtradas(unidade="201", mes=mes)
        assert len(rows) == 1
        assert rows[0]["unidade_id"] == "201"

    def test_retorna_campos_esperados(self):
        rows = Database.buscar_leituras_filtradas()
        campos = set(rows[0].keys())
        for campo in ("id", "unidade_id", "leitura_agua", "leitura_gas",
                      "tipo", "data_hora_coleta", "sincronizado"):
            assert campo in campos, f"Campo ausente: {campo}"

    def test_ordenado_mais_recente_primeiro(self):
        # Insere leitura de mês anterior
        mes_ant = "2020-01"
        _inserir_leitura(unidade="999", mes=mes_ant)
        rows = Database.buscar_leituras_filtradas()
        datas = [r["data_hora_coleta"] for r in rows]
        assert datas == sorted(datas, reverse=True)
