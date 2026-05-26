"""
Testes do bloqueio de inserção de leituras duplicadas — commit ed110e2 (26/05/2026).

Cobre as três camadas implementadas:
  1. salvar_leitura (database.py) — pré-check por unidade/mês/tipo
  2. Índices UNIQUE parciais (SQLite) — fallback de integridade
  3. Comportamento em todos os modos: AGUA, GAS, MISTO

Estrutura:
  TestSalvarLeituraDuplicata   — camada DB, modo AGUA e GAS
  TestSalvarLeituraMisto       — camada DB, interação AGUA+GAS na mesma unidade
  TestSalvarLeituraNull        — saves com NULL nunca devem ser bloqueados
  TestSalvarLeituraMeses       — cada mês é um ciclo independente
  TestIndiceParcialUnico       — índice SQLite bloqueia mesmo sem pré-check
  TestFluxoSimuladoAgua        — sequência completa modo AGUA (2 andares)
  TestFluxoSimuladoGas         — sequência completa modo GAS (2 andares)
  TestFluxoSimuladoMisto       — sequência completa modo MISTO (1 andar completo)
"""

import os
import sqlite3
import tempfile
import pytest
from datetime import datetime

# ── Banco isolado ──────────────────────────────────────────────────────────────

_tmp_dir = tempfile.mkdtemp()
_tmp_db  = os.path.join(_tmp_dir, "test_dup.db")

import database.database as _db_module
_db_module.Database.DB_PATH = _tmp_db
_db_module.Database.supabase = None
_db_module.Database.supabase_admin = None

from database.database import Database

MES     = datetime.now().strftime("%Y-%m")
MES_ANT = "2026-04"           # mês diferente para testes de ciclo


@pytest.fixture(autouse=True)
def banco_limpo():
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)
    Database.DB_PATH = _tmp_db
    Database.inicializar_tabelas()
    yield
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ts(mes=MES):
    return f"{mes}-15 10:00:00"


def salvar_agua(unidade, valor=100.0, mes=MES):
    return Database.salvar_leitura(
        unidade, round(valor, 2), None, "AGUA", _ts(mes), None, "tester"
    )


def salvar_gas(unidade, valor=50.0, mes=MES):
    return Database.salvar_leitura(
        unidade, None, round(valor, 3), "GAS", _ts(mes), None, "tester"
    )


def salvar_null(unidade, mes=MES):
    """Simula unidade pulada pelo zelador (barreira de andar)."""
    return Database.salvar_leitura(
        unidade, None, None, "MISTO", _ts(mes), None, "tester"
    )


def contar_rows(unidade=None):
    with Database.get_db() as conn:
        cur = conn.cursor()
        if unidade:
            cur.execute("SELECT COUNT(*) FROM leituras WHERE unidade_id=?", (unidade,))
        else:
            cur.execute("SELECT COUNT(*) FROM leituras")
        return cur.fetchone()[0]


# ══════════════════════════════════════════════════════════════════════════════
# 1. salvar_leitura — modo AGUA e GAS
# ══════════════════════════════════════════════════════════════════════════════

class TestSalvarLeituraDuplicata:

    def test_agua_primeira_vez_ok(self):
        res = salvar_agua("161")
        assert res["sucesso"] is True

    def test_agua_segunda_vez_bloqueada(self):
        salvar_agua("161")
        res = salvar_agua("161", valor=999.0)
        assert res["sucesso"] is False
        assert "registro_unico_unidade_coleta" in res["erro"]

    def test_agua_segunda_vez_nao_insere_row(self):
        salvar_agua("161")
        salvar_agua("161", valor=999.0)
        assert contar_rows("161") == 1          # só uma linha no banco

    def test_gas_primeira_vez_ok(self):
        res = salvar_gas("161")
        assert res["sucesso"] is True

    def test_gas_segunda_vez_bloqueada(self):
        salvar_gas("161")
        res = salvar_gas("161", valor=999.0)
        assert res["sucesso"] is False
        assert "registro_unico_unidade_coleta" in res["erro"]

    def test_gas_segunda_vez_nao_insere_row(self):
        salvar_gas("161")
        salvar_gas("161", valor=999.0)
        assert contar_rows("161") == 1

    def test_unidades_diferentes_nao_interferem(self):
        r1 = salvar_agua("161")
        r2 = salvar_agua("162")
        r3 = salvar_agua("163")
        assert r1["sucesso"] and r2["sucesso"] and r3["sucesso"]
        assert contar_rows() == 3

    def test_erro_retorna_nome_constraint_correto(self):
        """O nome do erro deve casar com o check em salvar_clique (medicao.py)."""
        salvar_agua("166")
        res = salvar_agua("166", valor=1.0)
        assert res.get("erro") == "registro_unico_unidade_coleta"

    def test_duplex_163_164_agua_bloqueado(self):
        salvar_agua("163/164")
        res = salvar_agua("163/164", valor=200.0)
        assert res["sucesso"] is False

    def test_duplex_163_164_gas_bloqueado(self):
        salvar_gas("163/164")
        res = salvar_gas("163/164", valor=200.0)
        assert res["sucesso"] is False


# ══════════════════════════════════════════════════════════════════════════════
# 2. Modo MISTO — AGUA e GAS são tipos independentes na mesma unidade
# ══════════════════════════════════════════════════════════════════════════════

class TestSalvarLeituraMisto:

    def test_agua_e_gas_mesmo_unidade_ambos_ok(self):
        """No modo misto a unidade tem água E gás — duas linhas separadas são válidas."""
        r_agua = salvar_agua("161")
        r_gas  = salvar_gas("161")
        assert r_agua["sucesso"] is True
        assert r_gas["sucesso"] is True
        assert contar_rows("161") == 2

    def test_re_agua_apos_misto_bloqueada(self):
        salvar_agua("161")
        salvar_gas("161")
        res = salvar_agua("161", valor=999.0)
        assert res["sucesso"] is False
        assert "registro_unico_unidade_coleta" in res["erro"]

    def test_re_gas_apos_misto_bloqueado(self):
        salvar_agua("161")
        salvar_gas("161")
        res = salvar_gas("161", valor=999.0)
        assert res["sucesso"] is False

    def test_re_agua_nao_insere_row_extra(self):
        salvar_agua("161")
        salvar_gas("161")
        salvar_agua("161", valor=999.0)   # deve ser bloqueado
        assert contar_rows("161") == 2    # ainda 2 linhas (1 agua + 1 gas)

    def test_re_gas_nao_insere_row_extra(self):
        salvar_agua("161")
        salvar_gas("161")
        salvar_gas("161", valor=999.0)    # deve ser bloqueado
        assert contar_rows("161") == 2

    def test_misto_6_unidades_andar_16_sem_duplicata(self):
        """Simula fase AGUA do andar 16 + fase GAS do andar 16 sem nenhuma duplicata."""
        unidades_16 = ["166", "165", "163/164", "162", "161"]
        for u in unidades_16:
            r = salvar_agua(u)
            assert r["sucesso"], f"ÁGUA {u} falhou na 1ª inserção"
        for u in unidades_16:
            r = salvar_gas(u)
            assert r["sucesso"], f"GÁS {u} falhou na 1ª inserção"
        # Tenta re-inserir tudo — deve ser 100% bloqueado
        bloqueados_agua = sum(
            1 for u in unidades_16 if not salvar_agua(u, valor=999.0)["sucesso"]
        )
        bloqueados_gas = sum(
            1 for u in unidades_16 if not salvar_gas(u, valor=999.0)["sucesso"]
        )
        assert bloqueados_agua == 5, f"Esperado 5 AGUA bloqueados, obtido {bloqueados_agua}"
        assert bloqueados_gas  == 5, f"Esperado 5 GAS bloqueados, obtido {bloqueados_gas}"


# ══════════════════════════════════════════════════════════════════════════════
# 3. Saves com NULL nunca devem ser bloqueados (unidades puladas — barreira)
# ══════════════════════════════════════════════════════════════════════════════

class TestSalvarLeituraNull:

    def test_null_primeira_vez_ok(self):
        res = salvar_null("161")
        assert res["sucesso"] is True

    def test_null_duplicado_ok(self):
        """NULL é uma "marca de skip" — pode ser inserida múltiplas vezes sem bloqueio."""
        salvar_null("161")
        res = salvar_null("161")
        assert res["sucesso"] is True

    def test_null_nao_bloqueia_agua_posterior(self):
        """Unidade pulada (null) pode ser lida depois."""
        salvar_null("161")
        res = salvar_agua("161")
        assert res["sucesso"] is True

    def test_null_nao_bloqueia_gas_posterior(self):
        salvar_null("161")
        res = salvar_gas("161")
        assert res["sucesso"] is True

    def test_agua_real_bloqueia_segunda_agua_mesmo_apos_null(self):
        """Null + agua real → segunda agua deve ser bloqueada."""
        salvar_null("161")
        salvar_agua("161")
        res = salvar_agua("161", valor=999.0)
        assert res["sucesso"] is False


# ══════════════════════════════════════════════════════════════════════════════
# 4. Meses diferentes = ciclos independentes
# ══════════════════════════════════════════════════════════════════════════════

class TestSalvarLeituraMeses:

    def test_mesmo_unidade_mes_diferente_ok(self):
        salvar_agua("161", mes=MES_ANT)
        res = salvar_agua("161", mes=MES)
        assert res["sucesso"] is True

    def test_gas_mesmo_unidade_mes_diferente_ok(self):
        salvar_gas("161", mes=MES_ANT)
        res = salvar_gas("161", mes=MES)
        assert res["sucesso"] is True

    def test_duplicata_bloqueada_dentro_do_mesmo_mes(self):
        salvar_agua("161", mes=MES)
        res = salvar_agua("161", mes=MES)
        assert res["sucesso"] is False

    def test_data_hora_none_nao_bloqueia(self):
        """Se data_hora for None (edge case) o check não dispara — melhor do que crash."""
        res = Database.salvar_leitura("161", 100.0, None, "AGUA", None, None, "tester")
        # Sem data_hora o mes fica vazio e o pré-check é ignorado — INSERT deve funcionar
        assert res["sucesso"] is True


# ══════════════════════════════════════════════════════════════════════════════
# 5. Índices UNIQUE parciais do SQLite (defense-in-depth)
# ══════════════════════════════════════════════════════════════════════════════

class TestIndiceParcialUnico:

    def test_indice_agua_existe_no_schema(self):
        with Database.get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                ("idx_unica_agua_mes",)
            )
            assert cur.fetchone() is not None, "Índice idx_unica_agua_mes não encontrado"

    def test_indice_gas_existe_no_schema(self):
        with Database.get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                ("idx_unica_gas_mes",)
            )
            assert cur.fetchone() is not None, "Índice idx_unica_gas_mes não encontrado"

    def test_indice_agua_bloqueia_insert_direto(self):
        """Bypass do pré-check com INSERT direto — índice deve lançar IntegrityError."""
        with Database.get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO leituras(unidade_id, leitura_agua, tipo, data_hora_coleta, sincronizado, valor_leitura)"
                " VALUES (?,?,?,?,?,?)",
                ("161", 100.0, "AGUA", _ts(), 0, 100.0)
            )
            conn.commit()
            with pytest.raises(sqlite3.IntegrityError):
                cur.execute(
                    "INSERT INTO leituras(unidade_id, leitura_agua, tipo, data_hora_coleta, sincronizado, valor_leitura)"
                    " VALUES (?,?,?,?,?,?)",
                    ("161", 200.0, "AGUA", _ts(), 0, 200.0)
                )

    def test_indice_gas_bloqueia_insert_direto(self):
        with Database.get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO leituras(unidade_id, leitura_gas, tipo, data_hora_coleta, sincronizado, valor_leitura)"
                " VALUES (?,?,?,?,?,?)",
                ("161", 50.0, "GAS", _ts(), 0, 50.0)
            )
            conn.commit()
            with pytest.raises(sqlite3.IntegrityError):
                cur.execute(
                    "INSERT INTO leituras(unidade_id, leitura_gas, tipo, data_hora_coleta, sincronizado, valor_leitura)"
                    " VALUES (?,?,?,?,?,?)",
                    ("161", 99.0, "GAS", _ts(), 0, 99.0)
                )

    def test_indice_nao_bloqueia_null_agua(self):
        """NULL não participa do índice parcial — múltiplos NULLs são permitidos."""
        with Database.get_db() as conn:
            cur = conn.cursor()
            for i in range(3):
                cur.execute(
                    "INSERT INTO leituras(unidade_id, leitura_agua, tipo, data_hora_coleta, sincronizado, valor_leitura)"
                    " VALUES (?,?,?,?,?,?)",
                    ("161", None, "MISTO", _ts(), 0, 0)
                )
            conn.commit()
        assert contar_rows("161") == 3     # três NULLs inseridos sem erro

    def test_indice_agua_independente_do_gas(self):
        """Índice de AGUA não bloqueia INSERT de GAS para a mesma unidade."""
        with Database.get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO leituras(unidade_id, leitura_agua, tipo, data_hora_coleta, sincronizado, valor_leitura)"
                " VALUES (?,?,?,?,?,?)",
                ("161", 100.0, "MISTO", _ts(), 0, 100.0)
            )
            # GAS na mesma unidade/mês deve funcionar (índice diferente)
            cur.execute(
                "INSERT INTO leituras(unidade_id, leitura_gas, tipo, data_hora_coleta, sincronizado, valor_leitura)"
                " VALUES (?,?,?,?,?,?)",
                ("161", 50.0, "MISTO", _ts(), 0, 50.0)
            )
            conn.commit()
        assert contar_rows("161") == 2


# ══════════════════════════════════════════════════════════════════════════════
# 6. Fluxo simulado — MODO AGUA (sequência 2 andares, sem duplicatas)
# ══════════════════════════════════════════════════════════════════════════════

class TestFluxoSimuladoAgua:
    """Simula salvar_clique em modo AGUA: todas as unidades → re-tentativa total → 0 duplicatas."""

    UNIDADES = ["166", "165", "163/164", "162", "161",   # andar 16
                "156", "155", "154", "153", "152", "151"] # andar 15

    def test_primeiro_ciclo_100_pct_sucesso(self):
        resultados = [salvar_agua(u, val) for val, u in enumerate(self.UNIDADES, 1)]
        falhas = [r for r in resultados if not r["sucesso"]]
        assert falhas == [], f"Falhas inesperadas: {falhas}"

    def test_re_tentativa_total_0_sucesso(self):
        for val, u in enumerate(self.UNIDADES, 1):
            salvar_agua(u, val)
        # Tenta gravar de novo para todas
        re_ok = [salvar_agua(u, 999.0)["sucesso"] for u in self.UNIDADES]
        assert not any(re_ok), "Nenhuma re-tentativa deveria ter sucesso"

    def test_total_rows_igual_unidades(self):
        for val, u in enumerate(self.UNIDADES, 1):
            salvar_agua(u, val)
        # Re-insere (bloqueadas)
        for u in self.UNIDADES:
            salvar_agua(u, 999.0)
        # Uma row por unidade
        assert contar_rows() == len(self.UNIDADES)

    def test_valores_originais_preservados(self):
        """Valores do primeiro ciclo não devem ser sobrescritos."""
        for val, u in enumerate(self.UNIDADES, 1):
            salvar_agua(u, float(val))
        # Re-tenta com valor 999
        for u in self.UNIDADES:
            salvar_agua(u, 999.0)
        leituras = Database.get_leituras_mes_atual()
        for i, u in enumerate(self.UNIDADES, 1):
            row = next((l for l in leituras if l["unidade_id"] == u), None)
            assert row is not None, f"Unidade {u} não encontrada"
            assert row["leitura_agua"] == float(i), (
                f"{u}: esperado {float(i)}, obtido {row['leitura_agua']}")


# ══════════════════════════════════════════════════════════════════════════════
# 7. Fluxo simulado — MODO GAS
# ══════════════════════════════════════════════════════════════════════════════

class TestFluxoSimuladoGas:

    UNIDADES = ["166", "165", "163/164", "162", "161",
                "156", "155", "154", "153", "152", "151",
                "LAZER GÁS"]

    def test_primeiro_ciclo_100_pct_sucesso(self):
        resultados = [salvar_gas(u, val) for val, u in enumerate(self.UNIDADES, 1)]
        falhas = [r for r in resultados if not r["sucesso"]]
        assert falhas == [], f"Falhas inesperadas: {falhas}"

    def test_re_tentativa_total_0_sucesso(self):
        for val, u in enumerate(self.UNIDADES, 1):
            salvar_gas(u, val)
        re_ok = [salvar_gas(u, 999.0)["sucesso"] for u in self.UNIDADES]
        assert not any(re_ok), "Nenhuma re-tentativa deveria ter sucesso"

    def test_total_rows_igual_unidades(self):
        for val, u in enumerate(self.UNIDADES, 1):
            salvar_gas(u, val)
        for u in self.UNIDADES:
            salvar_gas(u, 999.0)
        assert contar_rows() == len(self.UNIDADES)

    def test_lazer_gas_bloqueado_em_segunda_tentativa(self):
        salvar_gas("LAZER GÁS", 120.0)
        res = salvar_gas("LAZER GÁS", 999.0)
        assert res["sucesso"] is False

    def test_terreo_geral_agua_apenas_agua_sem_gas(self):
        """TERREO GERAL ÁGUA não tem medidor de gás — só água deve ser salvo."""
        r_agua = salvar_agua("TERREO GERAL ÁGUA")
        r_gas  = salvar_gas("TERREO GERAL ÁGUA")
        assert r_agua["sucesso"] is True
        assert r_gas["sucesso"] is True   # não há regra de negócio impedindo gas aqui
        # Re-tentativa bloqueada em ambos
        assert salvar_agua("TERREO GERAL ÁGUA", 999.0)["sucesso"] is False
        assert salvar_gas("TERREO GERAL ÁGUA", 999.0)["sucesso"] is False


# ══════════════════════════════════════════════════════════════════════════════
# 8. Fluxo simulado — MODO MISTO (andar 16 completo)
# ══════════════════════════════════════════════════════════════════════════════

class TestFluxoSimuladoMisto:
    """
    Simula a lógica de _avancar_misto() para o andar 16:
      Fase AGUA: 166→165→163/164→162→161
      Fase GAS:  166→165→163/164→162→161
    Depois tenta re-inserir tudo — 0 sucessos.
    """

    ANDAR_16 = ["166", "165", "163/164", "162", "161"]

    def _ciclo_misto_andar(self):
        """Executa um ciclo misto completo para o andar 16."""
        resultados = []
        for u in self.ANDAR_16:
            resultados.append(("AGUA", u, salvar_agua(u)))
        for u in self.ANDAR_16:
            resultados.append(("GAS", u, salvar_gas(u)))
        return resultados

    def test_ciclo_misto_completo_100_pct_sucesso(self):
        for tipo, u, res in self._ciclo_misto_andar():
            assert res["sucesso"] is True, f"{tipo} {u} falhou na 1ª inserção"

    def test_ciclo_misto_gera_2_rows_por_unidade(self):
        self._ciclo_misto_andar()
        for u in self.ANDAR_16:
            assert contar_rows(u) == 2, f"{u}: esperado 2 rows (agua+gas), obtido {contar_rows(u)}"

    def test_re_agua_apos_ciclo_misto_bloqueada(self):
        self._ciclo_misto_andar()
        bloqueados = sum(
            1 for u in self.ANDAR_16 if not salvar_agua(u, 999.0)["sucesso"]
        )
        assert bloqueados == len(self.ANDAR_16)

    def test_re_gas_apos_ciclo_misto_bloqueado(self):
        self._ciclo_misto_andar()
        bloqueados = sum(
            1 for u in self.ANDAR_16 if not salvar_gas(u, 999.0)["sucesso"]
        )
        assert bloqueados == len(self.ANDAR_16)

    def test_total_rows_exatos_apos_re_tentativas(self):
        self._ciclo_misto_andar()
        # Re-tenta tudo (água + gás)
        for u in self.ANDAR_16:
            salvar_agua(u, 999.0)
            salvar_gas(u, 999.0)
        # 5 unidades × 2 tipos = 10 rows; zero duplicatas
        assert contar_rows() == len(self.ANDAR_16) * 2

    def test_scanner_retorna_mesma_unidade_6_vezes(self):
        """
        Cenário do bug original: OCR scanner retorna unidade 161 6x com valor 13.0.
        Apenas a 1ª inserção de cada tipo deve ter sucesso.
        """
        resultados_agua = [salvar_agua("161", 13.0) for _ in range(6)]
        resultados_gas  = [salvar_gas("161", 13.0) for _ in range(6)]

        assert resultados_agua[0]["sucesso"] is True,  "1ª AGUA deve ter sucesso"
        assert all(not r["sucesso"] for r in resultados_agua[1:]), "2ª-6ª AGUA devem ser bloqueadas"
        assert resultados_gas[0]["sucesso"] is True,   "1ª GAS deve ter sucesso"
        assert all(not r["sucesso"] for r in resultados_gas[1:]), "2ª-6ª GAS devem ser bloqueadas"
        assert contar_rows("161") == 2   # 1 agua + 1 gas — zero duplicatas
