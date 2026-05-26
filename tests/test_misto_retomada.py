"""
Testes de regressão — modo MISTO: persistência de estado e sequência multi-andar.
(26/05/2026)

Bug corrigido: em _avancar_misto(), _persistir_estado() era chamado antes de
_atualizar_campos_unidade(), gravando modo="AGUA" no client_storage mesmo quando
passo_leitura_atual já havia sido setado para "gas".
Efeito observado: ao voltar do menu, o app restaurava modo=AGUA e pulava todo
o gás do andar corrente.

Fix: _persistir_estado() agora deriva o modo de passo_leitura_atual diretamente.

Testes cobrem (camada DB):
  1. Ciclo misto andar 16 — agua→gas sem pular nenhum
  2. Sequência multi-andar: gás andar 7 → gás andar 6 (unidade 71 → 66)
  3. Retomada simulada: gas pendente após "saída do menu" não perde dados
  4. Modo AGUA completo — apenas leituras de água
  5. Modo GAS completo  — apenas leituras de gás
  6. Misto 2 andares    — andar 16 + andar 15 completos
  7. Barreira null não bloqueia gas do próximo andar
"""
import os
import sys
import tempfile
import pytest
from datetime import datetime

_tmp_dir = tempfile.mkdtemp()
_tmp_db  = os.path.join(_tmp_dir, "test_misto.db")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import database.database as _db_module
_db_module.Database.DB_PATH = _tmp_db
_db_module.Database.supabase = None
_db_module.Database.supabase_admin = None

from database.database import Database

MES = datetime.now().strftime("%Y-%m")

ANDAR_16 = ["166", "165", "163/164", "162", "161"]
ANDAR_15 = ["156", "155", "154", "153", "152", "151"]
ANDAR_7  = ["76",  "75",  "74",  "73",  "72",  "71"]
ANDAR_6  = ["66",  "65",  "64",  "63",  "62",  "61"]


@pytest.fixture(autouse=True)
def banco_limpo():
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)
    Database.DB_PATH = _tmp_db
    Database.inicializar_tabelas()
    yield
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)


def _ts():
    return f"{MES}-15 10:00:00"


def _agua(unidade, valor=100.0):
    return Database.salvar_leitura(
        unidade, round(valor, 2), None, "AGUA", _ts(), None, "tester")


def _gas(unidade, valor=10.0):
    return Database.salvar_leitura(
        unidade, None, round(valor, 3), "GAS", _ts(), None, "tester")


def _null(unidade):
    """Simula 'Salvar como Nulo' da barreira de andar."""
    return Database.salvar_leitura(
        unidade, None, None, "MISTO", _ts(), None, "tester")


def _contar(unidade=None, tipo=None):
    with Database.get_db() as conn:
        if unidade and tipo == "agua":
            return conn.execute(
                "SELECT COUNT(*) FROM leituras WHERE unidade_id=? AND leitura_agua IS NOT NULL",
                (unidade,)).fetchone()[0]
        if unidade and tipo == "gas":
            return conn.execute(
                "SELECT COUNT(*) FROM leituras WHERE unidade_id=? AND leitura_gas IS NOT NULL",
                (unidade,)).fetchone()[0]
        if unidade:
            return conn.execute(
                "SELECT COUNT(*) FROM leituras WHERE unidade_id=?",
                (unidade,)).fetchone()[0]
        return conn.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]


# ══════════════════════════════════════════════════════════════════════════════
# 1. Modo AGUA — ciclo completo andar 16
# ══════════════════════════════════════════════════════════════════════════════

class TestModoAgua:

    def test_agua_andar16_todas_ok(self):
        for u in ANDAR_16:
            assert _agua(u)["sucesso"] is True, f"Água {u} falhou"

    def test_agua_andar16_bloqueio_re_insert(self):
        for u in ANDAR_16:
            _agua(u)
        for u in ANDAR_16:
            assert _agua(u)["sucesso"] is False, f"Duplicata de água {u} não foi bloqueada"

    def test_agua_andar16_total_rows(self):
        for u in ANDAR_16:
            _agua(u)
        assert _contar() == len(ANDAR_16)

    def test_agua_nao_bloqueia_gas_mesmo_unidade(self):
        """Inserção de água não deve bloquear gás da mesma unidade."""
        _agua("166")
        assert _gas("166")["sucesso"] is True

    def test_agua_dois_andares_sem_interferencia(self):
        for u in ANDAR_16 + ANDAR_15:
            assert _agua(u)["sucesso"] is True
        assert _contar() == len(ANDAR_16) + len(ANDAR_15)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Modo GAS — ciclo completo andar 16
# ══════════════════════════════════════════════════════════════════════════════

class TestModoGas:

    def test_gas_andar16_todas_ok(self):
        for u in ANDAR_16:
            assert _gas(u)["sucesso"] is True, f"Gás {u} falhou"

    def test_gas_andar16_bloqueio_re_insert(self):
        for u in ANDAR_16:
            _gas(u)
        for u in ANDAR_16:
            assert _gas(u)["sucesso"] is False

    def test_gas_andar16_total_rows(self):
        for u in ANDAR_16:
            _gas(u)
        assert _contar() == len(ANDAR_16)

    def test_gas_nao_bloqueia_agua_mesmo_unidade(self):
        _gas("161")
        assert _agua("161")["sucesso"] is True

    def test_gas_dois_andares_sem_interferencia(self):
        for u in ANDAR_16 + ANDAR_15:
            assert _gas(u)["sucesso"] is True
        assert _contar() == len(ANDAR_16) + len(ANDAR_15)


# ══════════════════════════════════════════════════════════════════════════════
# 3. Modo MISTO — andar 16 completo
# ══════════════════════════════════════════════════════════════════════════════

class TestMistoAndar16:

    def _ciclo(self, andar=ANDAR_16):
        for u in andar:
            _agua(u)
        for u in andar:
            _gas(u)

    def test_ciclo_misto_100_pct_sucesso(self):
        for u in ANDAR_16:
            assert _agua(u)["sucesso"] is True
            assert _gas(u)["sucesso"] is True

    def test_ciclo_misto_gera_2_rows_por_unidade(self):
        self._ciclo()
        for u in ANDAR_16:
            assert _contar(u) == 2, f"{u}: esperado 2 rows"

    def test_ciclo_misto_re_agua_bloqueada(self):
        self._ciclo()
        for u in ANDAR_16:
            assert _agua(u)["sucesso"] is False

    def test_ciclo_misto_re_gas_bloqueado(self):
        self._ciclo()
        for u in ANDAR_16:
            assert _gas(u)["sucesso"] is False

    def test_ciclo_misto_total_rows(self):
        self._ciclo()
        assert _contar() == len(ANDAR_16) * 2


# ══════════════════════════════════════════════════════════════════════════════
# 4. Modo MISTO — sequência andar 7 → andar 6 (regressão do bug)
# ══════════════════════════════════════════════════════════════════════════════

class TestMistoSequenciaAndar7Para6:
    """
    Reproduz o cenário relatado: modo misto, gás do andar 7 concluído,
    tentativa de inserir gás do andar 6 (unidade 66) deve ser aceita.

    O bug de persistência fazia o app restaurar modo=AGUA ao voltar do menu,
    pulando todo o gás do andar 6. Este teste verifica a camada DB: após
    o gás do andar 7 estar no banco, o gás do andar 6 deve ser aceito.
    """

    def _setup_andares_16_a_7(self):
        """Insere água e gás de todos os andares 16 a 7 (simula progresso misto)."""
        andares = [
            ["166", "165", "163/164", "162", "161"],
            ["156", "155", "154", "153", "152", "151"],
            ["146", "145", "144", "143", "142", "141"],
            ["136", "135", "134", "133", "132", "131"],
            ["126", "125", "124", "123", "122", "121"],
            ["116", "115", "114", "113", "112", "111"],
            ["106", "105", "104", "103", "102", "101"],
            ["96",  "95",  "94",  "93",  "92",  "91"],
            ["86",  "85",  "84",  "83",  "82",  "81"],
            ANDAR_7,
        ]
        for andar in andares:
            for u in andar:
                _agua(u)
            for u in andar:
                _gas(u)

    def test_gas_71_aceito(self):
        """Gás do último apartamento do andar 7 deve ser inserido com sucesso."""
        for u in ANDAR_7:
            _agua(u)
        for u in ANDAR_7[:-1]:   # 76→72
            _gas(u)
        assert _gas("71")["sucesso"] is True

    def test_gas_66_aceito_apos_gas_71(self):
        """Gás de 66 (1º do andar 6) deve ser aceito quando gás de 71 já existe."""
        for u in ANDAR_6:
            _agua(u)
        for u in ANDAR_7:
            _gas(u)
        assert _gas("66")["sucesso"] is True

    def test_gas_andar6_completo_apos_andar7(self):
        """Todo o gás do andar 6 deve ser inserido após o gás do andar 7."""
        for u in ANDAR_6:
            _agua(u)
        for u in ANDAR_7:
            _gas(u)
        for u in ANDAR_6:
            assert _gas(u)["sucesso"] is True, f"Gás {u} bloqueado inesperadamente"

    def test_gas_andar6_re_insert_bloqueado(self):
        """Após inserir gás do andar 6, re-inserção deve ser bloqueada."""
        for u in ANDAR_6:
            _agua(u)
        for u in ANDAR_7:
            _gas(u)
        for u in ANDAR_6:
            _gas(u)
        for u in ANDAR_6:
            assert _gas(u)["sucesso"] is False

    def test_ciclo_completo_andares_16_a_6(self):
        """Simula _avancar_misto() de andares 16 a 6 — 0 falhas no 1º ciclo."""
        self._setup_andares_16_a_7()
        for u in ANDAR_6:
            _agua(u)
        for u in ANDAR_6:
            assert _gas(u)["sucesso"] is True, f"Gás {u} falhou inesperadamente"

    def test_total_rows_andares_16_a_7_mais_6_agua(self):
        """Verifica contagem exata de rows após ciclo parcial."""
        self._setup_andares_16_a_7()
        for u in ANDAR_6:
            _agua(u)
        # Andar 16 tem 5 unidades (duplex 163/164); andares 15-7 têm 6 cada.
        # (5 + 9×6) unidades × 2 rows cada + ANDAR_6 × 1 row (só água)
        esperado = (len(ANDAR_16) + 9 * 6) * 2 + len(ANDAR_6)  # = 118 + 6 = 124
        assert _contar() == esperado


# ══════════════════════════════════════════════════════════════════════════════
# 5. Retomada simulada — estado após saída e retorno ao menu
# ══════════════════════════════════════════════════════════════════════════════

class TestRetomadaEstado:
    """
    Simula o fluxo de 'sair do menu e voltar' durante o modo misto:
    dados já inseridos no banco permanecem corretos e a retomada
    do gás pendente não perde nem duplica nenhuma leitura.
    """

    def test_agua_andar6_persiste_apos_interrupcao(self):
        """Água do andar 6 inserida antes da 'saída' deve permanecer."""
        for u in ANDAR_6:
            _agua(u)
        # Simula 'reinicialização' consultando o banco de novo
        leituras = Database.get_leituras_mes_atual()
        lidos_agua = {l['unidade_id'] for l in leituras if l.get('leitura_agua') is not None}
        for u in ANDAR_6:
            assert u in lidos_agua, f"{u} perdeu a leitura de água"

    def test_gas_pendente_aceito_apos_retomada(self):
        """Gas do andar 6 ainda pendente deve ser aceito na retomada."""
        for u in ANDAR_7:
            _agua(u)
            _gas(u)
        for u in ANDAR_6:
            _agua(u)
        # Simula re-entrada: _persistir_estado restaura corretamente modo=GAS
        # O DB ainda aceita o gás (não há lock nem expiração)
        for u in ANDAR_6:
            assert _gas(u)["sucesso"] is True

    def test_gas_ja_inserido_bloqueado_na_retomada(self):
        """Gas parcialmente inserido antes da saída não gera duplicata na retomada."""
        for u in ANDAR_7:
            _agua(u)
            _gas(u)
        for u in ANDAR_6:
            _agua(u)
        # Insere apenas 3 primeiros antes de 'sair'
        for u in ANDAR_6[:3]:
            _gas(u)
        # 'Retoma' e tenta inserir tudo de novo — os 3 já feitos devem ser bloqueados
        resultados = [_gas(u) for u in ANDAR_6]
        assert resultados[0]["sucesso"] is False   # 66 já estava feito
        assert resultados[1]["sucesso"] is False   # 65
        assert resultados[2]["sucesso"] is False   # 64
        assert resultados[3]["sucesso"] is True    # 63 ainda pendente
        assert resultados[4]["sucesso"] is True    # 62
        assert resultados[5]["sucesso"] is True    # 61

    def test_rows_corretos_apos_retomada_parcial(self):
        """Contagem de rows bate exatamente com o esperado após retomada parcial."""
        for u in ANDAR_7:
            _agua(u)
            _gas(u)
        for u in ANDAR_6:
            _agua(u)
        for u in ANDAR_6[:3]:
            _gas(u)
        # Retoma e completa
        for u in ANDAR_6[3:]:
            _gas(u)
        # Andar 7: 6 × 2 rows; Andar 6: 6 agua + 6 gas = 12 rows
        esperado = 6 * 2 + 6 + 6
        assert _contar() == esperado


# ══════════════════════════════════════════════════════════════════════════════
# 6. Barreira null — não deve bloquear gás do próximo andar
# ══════════════════════════════════════════════════════════════════════════════

class TestBarreiraNullNaoBloqueiaProximoAndar:
    """
    Quando o leiturista usa 'Seguir (Salvar como Nulo)', unidades recebem
    leitura_gas = NULL. O gás do PRÓXIMO andar deve continuar sendo aceito.
    """

    def test_null_gas_nao_bloqueia_gas_real_mesma_unidade(self):
        """NULL salvo via barreira não bloqueia inserção real posterior."""
        assert _null("71")["sucesso"] is True
        assert _gas("71", 10.0)["sucesso"] is True

    def test_null_gas_andar7_aceita_gas_andar6(self):
        """Unidades do andar 7 com null não impedem gás do andar 6."""
        for u in ANDAR_7:
            _null(u)   # barreira salvou todos como null
        for u in ANDAR_6:
            assert _gas(u)["sucesso"] is True, f"Gás {u} bloqueado por null do andar 7"

    def test_null_nao_duplica_row_real(self):
        """NULL + real = 2 rows para mesma unidade (null nunca bloqueia real)."""
        _null("71")
        _gas("71", 10.0)
        assert _contar("71") == 2

    def test_null_andar6_agua_bloqueia_segunda_agua(self):
        """Barreira de água (null) não impede bloqueio de duplicata posterior."""
        _null("66")         # null agua E gas
        _agua("66", 100.0)  # real → OK
        res = _agua("66", 200.0)  # duplicata → bloqueada
        assert res["sucesso"] is False
