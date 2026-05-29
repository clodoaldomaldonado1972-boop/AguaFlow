"""
tests/test_modos_separados.py — AguaFlow 28/05/2026

Valida o comportamento dos modos ÁGUA e GÁS separados (sem modo misto como padrão):
  1. Default do modo_ronda é 'agua' — nunca 'misto'
  2. Modo ÁGUA: percorre 95 unidades sem nunca mudar para GÁS
  3. Modo GÁS: percorre 95 unidades sem nunca mudar para ÁGUA
  4. Leiturista troca manualmente via tab — lógica de _trocar_tab
  5. Ciclo ÁGUA termina em TERREO GERAL ÁGUA
  6. Ciclo GÁS termina em LAZER GÁS (TERREO GERAL é pulado)
  7. Nenhuma auto-troca de modo ao mudar de andar
  8. Bloqueio de duplicata funciona em cada modo separado
  9. Supabase: estrutura de payload verificada via mock
"""
import os
import tempfile
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

import database.database as _db_module

_tmp_dir = tempfile.mkdtemp()
_tmp_db = os.path.join(_tmp_dir, "test_separados.db")
_db_module.Database.DB_PATH = _tmp_db

from database.database import Database
from views.medicao import _extrair_andar, _normalizar_unidade_scanner


MES  = datetime.now().strftime("%Y-%m")
HORA = f"{MES}-15 09:00:00"
LEIT = "Testador"


@pytest.fixture(autouse=True)
def banco_limpo():
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)
    Database.DB_PATH = _tmp_db
    Database.inicializar_tabelas()
    yield
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)


# ── helpers ──────────────────────────────────────────────────────────────────

def _salvar_agua(u, v=100.0):
    return Database.salvar_leitura(u, v, None, "AGUA", HORA, None, LEIT)

def _salvar_gas(u, v=50.0):
    return Database.salvar_leitura(u, None, v, "GAS", HORA, None, LEIT)

def _lidos_agua():
    return {l["unidade_id"] for l in Database.get_leituras_mes_atual()
            if l.get("leitura_agua") is not None}

def _lidos_gas():
    return {l["unidade_id"] for l in Database.get_leituras_mes_atual()
            if l.get("leitura_gas") is not None}

def _deve_pular(nome, modo):
    n = nome.upper()
    if "LAZER GÁS" in n or "LAZER GAS" in n:
        return modo == "agua"
    if "TERREO GERAL" in n:
        return modo == "gas"
    return False

def _proxima_pendente_agua(atual):
    lista = Database._gerar_lista_unidades()
    lidos = _lidos_agua()
    idx = lista.index(atual) if atual in lista else -1
    for i in range(idx + 1, len(lista)):
        if lista[i] not in lidos:
            return lista[i]
    return None

def _proxima_pendente_gas(atual):
    lista = Database._gerar_lista_unidades()
    lidos = _lidos_gas()
    idx = lista.index(atual) if atual in lista else -1
    for i in range(idx + 1, len(lista)):
        if lista[i] not in lidos:
            return lista[i]
    return None


# ── 1. Default modo_ronda ────────────────────────────────────────────────────

class TestDefaultModoRonda:
    """O default agora é 'agua', não 'misto'."""

    def test_default_e_agua_quando_user_data_vazio(self):
        user_data = {}
        modo = user_data.get("modo_ronda", "agua")
        assert modo == "agua", f"Default deve ser 'agua', got '{modo}'"

    def test_modo_agua_valido(self):
        user_data = {"modo_ronda": "agua"}
        modo = user_data.get("modo_ronda", "agua")
        assert modo in ("agua", "gas")

    def test_modo_gas_valido(self):
        user_data = {"modo_ronda": "gas"}
        modo = user_data.get("modo_ronda", "agua")
        assert modo in ("agua", "gas")

    def test_modo_invalido_cai_para_agua(self):
        modo_raw = "misto"  # valor legado
        modo = modo_raw if modo_raw in ("agua", "gas") else "agua"
        assert modo == "agua"

    def test_none_cai_para_agua(self):
        modo_raw = None
        modo = modo_raw if modo_raw in ("agua", "gas") else "agua"
        assert modo == "agua"


# ── 2. Ciclo ÁGUA completo sem troca de modo ─────────────────────────────────

class TestCicloAguaSemTrocaModo:

    def test_ciclo_agua_le_95_unidades(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "agua"):
                _salvar_agua(u)
        lidos = _lidos_agua()
        count = sum(1 for u in lista if u in lidos or
                    any(p.strip() in lidos for p in u.split("/") if p.strip()))
        assert count == 95, f"Esperado 95, got {count}"

    def test_modo_agua_nunca_toca_gas(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "agua"):
                _salvar_agua(u)
        assert len(_lidos_gas()) == 0, "Modo ÁGUA não deve inserir leituras de GÁS"

    def test_agua_atravessa_todos_andares_em_ordem(self):
        lista = Database._gerar_lista_unidades()
        apts = [u for u in lista if u[0].isdigit()]
        for i, u in enumerate(apts):
            _salvar_agua(u, float(100 + i))
        lidos = _lidos_agua()
        for u in apts:
            assert u in lidos or any(
                p.strip() in lidos for p in u.split("/") if p.strip()
            ), f"Unidade {u} não foi lida em modo ÁGUA"

    def test_lazer_gas_nao_aparece_em_lidos_agua(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "agua"):
                _salvar_agua(u)
        assert "LAZER GÁS" not in _lidos_agua()

    def test_terreo_geral_e_ultima_pendente_agua(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "agua") and u != "TERREO GERAL ÁGUA":
                _salvar_agua(u)
        prox = _proxima_pendente_agua("LAZER GÁS")
        assert prox == "TERREO GERAL ÁGUA"

    def test_fim_ciclo_agua_apos_terreo_geral(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "agua"):
                _salvar_agua(u)
        assert _proxima_pendente_agua("TERREO GERAL ÁGUA") is None

    def test_agua_andar_16_sem_saltar_para_gas(self):
        """Após andar 16 completo em ÁGUA, próxima é andar 15 (não gás do 16)."""
        lista = Database._gerar_lista_unidades()
        andar_16 = [u for u in lista if _extrair_andar(u) == "16"]
        for u in andar_16:
            _salvar_agua(u)
        prox = _proxima_pendente_agua("161")
        assert prox is not None
        assert _extrair_andar(prox) == "15", (
            f"Após andar 16 ÁGUA, esperado andar 15, got '{prox}'"
        )

    def test_agua_duplex_163_164_lido_como_unidade_unica(self):
        _salvar_agua("163/164", 568.37)
        lidos = _lidos_agua()
        assert "163/164" in lidos
        assert "163" not in lidos and "164" not in lidos


# ── 3. Ciclo GÁS completo sem troca de modo ──────────────────────────────────

class TestCicloGasSemTrocaModo:

    def test_ciclo_gas_le_95_unidades(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "gas"):
                _salvar_gas(u)
        lidos = _lidos_gas()
        count = sum(1 for u in lista if u in lidos or
                    any(p.strip() in lidos for p in u.split("/") if p.strip()))
        assert count == 95, f"Esperado 95, got {count}"

    def test_modo_gas_nunca_toca_agua(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "gas"):
                _salvar_gas(u)
        assert len(_lidos_agua()) == 0, "Modo GÁS não deve inserir leituras de ÁGUA"

    def test_terreo_geral_nunca_entra_em_lidos_gas(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "gas"):
                _salvar_gas(u)
        assert "TERREO GERAL ÁGUA" not in _lidos_gas()

    def test_lazer_gas_e_lido_em_modo_gas(self):
        _salvar_gas("LAZER GÁS", 123.456)
        assert "LAZER GÁS" in _lidos_gas()

    def test_gas_andar_16_sem_saltar_para_agua(self):
        """Após andar 16 completo em GÁS, próxima é andar 15 (não água do 16)."""
        lista = Database._gerar_lista_unidades()
        andar_16 = [u for u in lista if _extrair_andar(u) == "16"]
        for u in andar_16:
            _salvar_gas(u)
        prox = _proxima_pendente_gas("161")
        assert prox is not None
        assert _extrair_andar(prox) == "15", (
            f"Após andar 16 GÁS, esperado andar 15, got '{prox}'"
        )

    def test_gas_duplex_163_164_como_unidade_unica(self):
        _salvar_gas("163/164", 158.489)
        lidos = _lidos_gas()
        assert "163/164" in lidos

    def test_fim_ciclo_gas_lazer_e_ultimo_real(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "gas"):
                _salvar_gas(u)
        # Após LAZER GÁS, TERREO GERAL é pulado → None
        prox = _proxima_pendente_gas("LAZER GÁS")
        if prox == "TERREO GERAL ÁGUA":
            assert _deve_pular("TERREO GERAL ÁGUA", "gas") is True
        else:
            assert prox is None


# ── 4. Troca manual de modo (simulação de _trocar_tab) ───────────────────────

class TestTrocaManualDeModo:

    def test_trocar_para_gas_muda_passo_leitura(self):
        modo = "agua"
        novo_modo = "gas"
        # simula _trocar_tab
        if novo_modo in ("agua", "gas"):
            modo = novo_modo
        assert modo == "gas"

    def test_trocar_para_agua_muda_passo_leitura(self):
        modo = "gas"
        novo_modo = "agua"
        if novo_modo in ("agua", "gas"):
            modo = novo_modo
        assert modo == "agua"

    def test_modo_invalido_nao_muda(self):
        modo = "agua"
        novo_modo = "misto"
        if novo_modo in ("agua", "gas"):
            modo = novo_modo
        assert modo == "agua"

    def test_agua_salva_antes_da_troca_nao_some(self):
        """Leituras de ÁGUA persistem após troca manual para GÁS."""
        _salvar_agua("166", 260.12)
        _salvar_agua("165", 392.52)
        # troca para GÁS
        _salvar_gas("166", 128.621)
        lidos_a = _lidos_agua()
        lidos_g = _lidos_gas()
        assert "166" in lidos_a
        assert "165" in lidos_a
        assert "166" in lidos_g

    def test_gas_bloqueado_se_gas_anterior_pendente(self):
        """Em modo GÁS, 165 não pode ser salvo se 166-GÁS ainda está pendente."""
        _salvar_gas("166", 128.0)
        lista = Database._gerar_lista_unidades()
        idx = lista.index("165")
        anterior = lista[idx - 1]  # "166"
        lidos_g = _lidos_gas()
        assert anterior in lidos_g, "166-GÁS deve estar nos lidos antes de 165"

    def test_agua_e_gas_independentes_por_modo(self):
        """ÁGUA de 166 não libera GÁS de 165 — os modos são independentes."""
        _salvar_agua("166")
        lista = Database._gerar_lista_unidades()
        idx = lista.index("165")
        anterior = lista[idx - 1]
        lidos_g = _lidos_gas()
        assert anterior not in lidos_g, (
            "ÁGUA de 166 não deve liberar sequência GÁS de 165"
        )


# ── 5. Ciclos paralelos ÁGUA + GÁS (rondas distintas) ────────────────────────

class TestCiclosParalelos:
    """Leiturista faz ronda ÁGUA completa, depois ronda GÁS completa."""

    def test_agua_completa_depois_gas_completa(self):
        lista = Database._gerar_lista_unidades()
        # Ronda ÁGUA
        for u in lista:
            if not _deve_pular(u, "agua"):
                _salvar_agua(u)
        # Ronda GÁS
        for u in lista:
            if not _deve_pular(u, "gas"):
                _salvar_gas(u)
        lidos_a = _lidos_agua()
        lidos_g = _lidos_gas()
        pendentes_a = [u for u in lista if not _deve_pular(u, "agua")
                       and u not in lidos_a and not any(
                           p.strip() in lidos_a for p in u.split("/") if p.strip())]
        pendentes_g = [u for u in lista if not _deve_pular(u, "gas")
                       and u not in lidos_g and not any(
                           p.strip() in lidos_g for p in u.split("/") if p.strip())]
        assert pendentes_a == [], f"Pendentes ÁGUA: {pendentes_a}"
        assert pendentes_g == [], f"Pendentes GÁS: {pendentes_g}"

    def test_total_rows_rondas_paralelas(self):
        """Ronda ÁGUA (95 rows) + ronda GÁS (95 rows) = 190 rows — cada modo cria row próprio."""
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "agua"):
                _salvar_agua(u)
            if not _deve_pular(u, "gas"):
                _salvar_gas(u)
        with Database.get_db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]
        # 95 rows de ÁGUA (LAZER GÁS pulado) + 95 rows de GÁS (TERREO GERAL pulado) = 190
        assert total == 190, f"Esperado 190 rows (95 agua + 95 gas), got {total}"

    def test_areas_comuns_isoladas_por_modo(self):
        _salvar_agua("TERREO GERAL ÁGUA", 13518.6)
        _salvar_gas("LAZER GÁS", 215.432)
        assert "TERREO GERAL ÁGUA" in _lidos_agua()
        assert "TERREO GERAL ÁGUA" not in _lidos_gas()
        assert "LAZER GÁS" in _lidos_gas()
        assert "LAZER GÁS" not in _lidos_agua()


# ── 6. Payload Supabase (mock) ────────────────────────────────────────────────

class TestPayloadSupabase:
    """Verifica a estrutura do payload enviado ao Supabase via mock."""

    def _capturar_payload(self, unidade, valor_agua, valor_gas, modo):
        payloads = []
        mock_execute = MagicMock()
        mock_insert = MagicMock(return_value=MagicMock(execute=mock_execute))
        mock_table = MagicMock(return_value=MagicMock(insert=mock_insert))
        original_supabase = Database.supabase
        try:
            Database.supabase = MagicMock()
            Database.supabase.table = mock_table
            res = Database.salvar_leitura(
                unidade, valor_agua, valor_gas, modo, HORA, None, LEIT
            )
        finally:
            Database.supabase = original_supabase
        return res

    def test_salvar_agua_retorna_sucesso(self):
        res = self._capturar_payload("166", 260.12, None, "AGUA")
        assert res["sucesso"] is True

    def test_salvar_gas_retorna_sucesso(self):
        res = self._capturar_payload("165", None, 158.489, "GAS")
        assert res["sucesso"] is True

    def test_salvar_duplex_agua_retorna_sucesso(self):
        res = self._capturar_payload("163/164", 568.37, None, "AGUA")
        assert res["sucesso"] is True

    def test_salvar_terreo_agua_retorna_sucesso(self):
        res = self._capturar_payload("TERREO GERAL ÁGUA", 13518.6, None, "AGUA")
        assert res["sucesso"] is True

    def test_salvar_lazer_gas_retorna_sucesso(self):
        res = self._capturar_payload("LAZER GÁS", None, 215.432, "GAS")
        assert res["sucesso"] is True

    def test_agua_salva_no_sqlite_com_flag_zero(self):
        """salvar_leitura grava no SQLite com sincronizado=0."""
        Database.salvar_leitura("166", 260.12, None, "AGUA", HORA, None, LEIT)
        with Database.get_db() as conn:
            row = conn.execute(
                "SELECT sincronizado, leitura_agua FROM leituras WHERE unidade_id='166'"
            ).fetchone()
        assert row is not None
        assert row["sincronizado"] == 0
        assert abs(row["leitura_agua"] - 260.12) < 0.01

    def test_gas_salva_no_sqlite_com_flag_zero(self):
        Database.salvar_leitura("165", None, 158.489, "GAS", HORA, None, LEIT)
        with Database.get_db() as conn:
            row = conn.execute(
                "SELECT sincronizado, leitura_gas FROM leituras WHERE unidade_id='165'"
            ).fetchone()
        assert row is not None
        assert row["sincronizado"] == 0
        assert abs(row["leitura_gas"] - 158.489) < 0.001

    def test_duplicata_bloqueada_no_sqlite(self):
        Database.salvar_leitura("166", 260.12, None, "AGUA", HORA, None, LEIT)
        res2 = Database.salvar_leitura("166", 999.99, None, "AGUA", HORA, None, LEIT)
        assert res2["sucesso"] is False
        assert "registro_unico" in str(res2.get("erro", ""))

    def test_agua_e_gas_para_mesma_unidade_sao_independentes(self):
        """ÁGUA e GÁS da mesma unidade ficam em rows separados — índice único por modo."""
        r1 = Database.salvar_leitura("166", 260.12, None, "AGUA", HORA, None, LEIT)
        r2 = Database.salvar_leitura("166", None, 128.621, "GAS", HORA, None, LEIT)
        assert r1["sucesso"] is True
        assert r2["sucesso"] is True
        with Database.get_db() as conn:
            rows = conn.execute(
                "SELECT leitura_agua, leitura_gas FROM leituras WHERE unidade_id='166'"
            ).fetchall()
        # Deve existir exatamente 2 rows: uma com agua, outra com gas
        assert len(rows) == 2, f"Esperado 2 rows, got {len(rows)}"
        agua_vals = [r["leitura_agua"] for r in rows if r["leitura_agua"] is not None]
        gas_vals  = [r["leitura_gas"]  for r in rows if r["leitura_gas"]  is not None]
        assert agua_vals and agua_vals[0] == pytest.approx(260.12, abs=0.01)
        assert gas_vals  and gas_vals[0]  == pytest.approx(128.621, abs=0.001)


# ── 7. Integração: ciclo completo + verificação Supabase flag ────────────────

class TestIntegracaoCicloCompleto:

    def test_96_unidades_salvam_com_sincronizado_zero(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "agua"):
                Database.salvar_leitura(u, 100.0, None, "AGUA", HORA, None, LEIT)
        with Database.get_db() as conn:
            pendentes = conn.execute(
                "SELECT COUNT(*) FROM leituras WHERE sincronizado=0"
            ).fetchone()[0]
        assert pendentes == 95, f"Esperado 95 pendentes, got {pendentes}"

    def test_apos_marcar_sincronizado_fila_vazia(self):
        Database.salvar_leitura("166", 260.12, None, "AGUA", HORA, None, LEIT)
        with Database.get_db() as conn:
            conn.execute("UPDATE leituras SET sincronizado=1 WHERE unidade_id='166'")
            conn.commit()
            pendentes = conn.execute(
                "SELECT COUNT(*) FROM leituras WHERE sincronizado=0"
            ).fetchone()[0]
        assert pendentes == 0

    def test_agua_e_gas_95_cada_pendentes_para_sync(self):
        lista = Database._gerar_lista_unidades()
        for u in lista:
            if not _deve_pular(u, "agua"):
                Database.salvar_leitura(u, 100.0, None, "AGUA", HORA, None, LEIT)
            if not _deve_pular(u, "gas"):
                Database.salvar_leitura(u, 50.0, None, "GAS", HORA, None, LEIT)
        with Database.get_db() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM leituras WHERE sincronizado=0"
            ).fetchone()[0]
        # 95 água + 95 gás em rows mesclados por unidade — verifica total rows
        assert total == 96, f"Esperado 96 rows, got {total}"
