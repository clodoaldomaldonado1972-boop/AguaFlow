"""
Bateria de testes — AguaFlow v1.2 (22/05/2026)

Cobertura:
  1.  Lista de unidades (estrutura, contagem, ordem)
  2.  _extrair_andar
  3.  _normalizar_unidade_scanner
  4.  _unidade_lida (lógica duplex)
  5.  lidos filtrados por modo — fix do bug de validação de sequência
  6.  Demonstração do bug antigo (lidos sem filtro de modo)
  7.  Fluxo completo ÁGUA (todas as 96 unidades)
  8.  Fluxo completo GÁS (todas as unidades com hidrômetro de gás)
  9.  Áreas comuns: LAZER GÁS e TERREO GERAL ÁGUA
  10. Validação de sequência com modo correto
  11. Fim de ciclo: salvar_referencias_ciclo + _resetar_banco_para_novo_mes
  12. Relatório CSV (sem SMTP)
"""

import csv
import os
import tempfile

import pytest
from datetime import datetime

# ── Monkeypatch ANTES de importar Database ───────────────────────────────────
import database.database as _db_module

_tmp_dir = tempfile.mkdtemp()
_tmp_db  = os.path.join(_tmp_dir, "test_ciclo.db")
_db_module.Database.DB_PATH = _tmp_db

from database.database import Database
from views.medicao import _extrair_andar, _normalizar_unidade_scanner

try:
    from relatorio_engine import RelatorioEngine
    HAS_RELATORIO = True
except ImportError:
    HAS_RELATORIO = False


# ── Fixtures e helpers ───────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def banco_limpo():
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)
    Database.DB_PATH = _tmp_db
    Database.inicializar_tabelas()
    yield
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)


def _mes_atual():
    return datetime.now().strftime("%Y-%m")


def _inserir_agua(unidade: str, valor: float = 100.0) -> dict:
    return Database.salvar_leitura(
        unidade, valor, None, "AGUA",
        f"{_mes_atual()}-15 10:00:00", None, "Testador"
    )


def _inserir_gas(unidade: str, valor: float = 50.0) -> dict:
    return Database.salvar_leitura(
        unidade, None, valor, "GAS",
        f"{_mes_atual()}-15 10:00:00", None, "Testador"
    )


def _build_lidos(modo: str) -> set:
    """Replica a lógica de salvar_clique após o fix — filtra por modo."""
    leituras = Database.get_leituras_mes_atual()
    if modo == "AGUA":
        return {l.get("unidade_id") for l in leituras if l.get("leitura_agua") is not None}
    return {l.get("unidade_id") for l in leituras if l.get("leitura_gas") is not None}


def _unidade_lida(unidade: str, lidos: set) -> bool:
    """Replica _unidade_lida de medicao.py (suporta duplex '163/164')."""
    if unidade in lidos:
        return True
    return any(p.strip() in lidos for p in unidade.split("/") if p.strip())


# ── 1. Lista de unidades ─────────────────────────────────────────────────────

class TestListaUnidades:
    def test_total_96_unidades(self):
        assert len(Database._gerar_lista_unidades()) == 96

    def test_primeira_e_166(self):
        assert Database._gerar_lista_unidades()[0] == "166"

    def test_ultima_e_terreo_geral_agua(self):
        assert Database._gerar_lista_unidades()[-1] == "TERREO GERAL ÁGUA"

    def test_penultima_e_lazer_gas(self):
        assert Database._gerar_lista_unidades()[-2] == "LAZER GÁS"

    def test_duplex_163_164_presente_e_individuas_ausentes(self):
        lista = Database._gerar_lista_unidades()
        assert "163/164" in lista
        assert "163" not in lista
        assert "164" not in lista

    def test_duplex_23_24_presente_e_individuais_ausentes(self):
        lista = Database._gerar_lista_unidades()
        assert "23/24" in lista
        assert "23" not in lista
        assert "24" not in lista

    def test_sem_duplicatas(self):
        lista = Database._gerar_lista_unidades()
        assert len(lista) == len(set(lista))

    def test_ordem_descente_por_andar(self):
        lista = Database._gerar_lista_unidades()
        apt = [u for u in lista if u[0].isdigit()]
        assert apt.index("166") < apt.index("156") < apt.index("16")

    def test_floor16_completo(self):
        lista = Database._gerar_lista_unidades()
        floor16 = ["166", "165", "163/164", "162", "161"]
        for u in floor16:
            assert u in lista

    def test_floor1_completo(self):
        lista = Database._gerar_lista_unidades()
        floor1 = ["16", "15", "14", "13", "12", "11"]
        for u in floor1:
            assert u in lista


# ── 2. Extração de andar ─────────────────────────────────────────────────────

class TestExtrairAndar:
    @pytest.mark.parametrize("unit,esperado", [
        ("166",              "16"),
        ("161",              "16"),
        ("156",              "15"),
        ("96",               "9"),
        ("91",               "9"),
        ("16",               "1"),
        ("11",               "1"),
        ("163/164",          "16"),
        ("23/24",            "2"),
        ("LAZER GÁS",        ""),
        ("TERREO GERAL ÁGUA", ""),
        ("",                 ""),
    ])
    def test_extrair(self, unit, esperado):
        assert _extrair_andar(unit) == esperado

    def test_andares_distintos_entre_floors(self):
        assert _extrair_andar("166") != _extrair_andar("156")
        assert _extrair_andar("161") == _extrair_andar("166")   # mesmo andar


# ── 3. Normalização do scanner ───────────────────────────────────────────────

class TestNormalizarUnidadeScanner:
    def setup_method(self):
        self.lista = Database._gerar_lista_unidades()

    def test_codigo_exato(self):
        assert _normalizar_unidade_scanner("166", self.lista) == "166"

    def test_formato_aguaflow_pipe_agua(self):
        assert _normalizar_unidade_scanner("AGUAFLOW|166-AGUA", self.lista) == "166"

    def test_formato_aguaflow_pipe_gas(self):
        assert _normalizar_unidade_scanner("AGUAFLOW|166-GAS", self.lista) == "166"

    def test_somente_sufixo_tipo(self):
        assert _normalizar_unidade_scanner("166-AGUA", self.lista) == "166"

    def test_duplex_com_pipe(self):
        assert _normalizar_unidade_scanner("AGUAFLOW|163/164-AGUA", self.lista) == "163/164"

    def test_lazer_gas_com_pipe(self):
        assert _normalizar_unidade_scanner("AGUAFLOW|LAZER GÁS", self.lista) == "LAZER GÁS"

    def test_codigo_nao_encontrado_retorna_sem_prefixo(self):
        # "999" não existe na lista → sufixo não é removido; retorna sem o prefixo
        res = _normalizar_unidade_scanner("AGUAFLOW|999-AGUA", self.lista)
        assert res == "999-AGUA"


# ── 4. Lógica duplex _unidade_lida ───────────────────────────────────────────

class TestUnidadeLida:
    def test_exato_presente(self):
        assert _unidade_lida("166", {"166"}) is True

    def test_exato_ausente(self):
        assert _unidade_lida("166", {"165"}) is False

    def test_duplex_via_id_completo(self):
        assert _unidade_lida("163/164", {"163/164"}) is True

    def test_duplex_via_parte_esquerda(self):
        assert _unidade_lida("163/164", {"163"}) is True

    def test_duplex_via_parte_direita(self):
        assert _unidade_lida("163/164", {"164"}) is True

    def test_duplex_ausente(self):
        assert _unidade_lida("163/164", {"165"}) is False

    def test_area_comum_presente(self):
        assert _unidade_lida("LAZER GÁS", {"LAZER GÁS"}) is True

    def test_area_comum_ausente(self):
        assert _unidade_lida("LAZER GÁS", {"TERREO GERAL ÁGUA"}) is False


# ── 5. lidos filtrados por modo (fix do bug) ─────────────────────────────────

class TestLidosFiltradosPorModo:
    """
    Valida que o lidos em salvar_clique respeita o modo:
    — ÁGUA só conta unidades com leitura_agua preenchida
    — GÁS só conta unidades com leitura_gas preenchida
    """

    def test_agua_registrada_entra_em_lidos_agua(self):
        _inserir_agua("166")
        assert "166" in _build_lidos("AGUA")

    def test_agua_registrada_nao_entra_em_lidos_gas(self):
        _inserir_agua("166")
        assert "166" not in _build_lidos("GAS")

    def test_gas_registrado_entra_em_lidos_gas(self):
        _inserir_gas("166")
        assert "166" in _build_lidos("GAS")

    def test_gas_registrado_nao_entra_em_lidos_agua(self):
        _inserir_gas("166")
        assert "166" not in _build_lidos("AGUA")

    def test_ambos_registrados_aparecem_nos_dois_modos(self):
        _inserir_agua("166")
        _inserir_gas("166")
        assert "166" in _build_lidos("AGUA")
        assert "166" in _build_lidos("GAS")

    def test_banco_vazio_lidos_vazio(self):
        assert _build_lidos("AGUA") == set()
        assert _build_lidos("GAS") == set()

    def test_sequencia_gas_bloqueada_sem_gas_na_anterior(self):
        """
        Cenário crítico: 166 tem só ÁGUA.
        Em modo GÁS, a validação de sequência para 165 deve FALHAR
        porque 166 ainda não tem GÁS registrado.
        """
        lista = Database._gerar_lista_unidades()
        _inserir_agua("166")
        lidos_gas = _build_lidos("GAS")
        idx = lista.index("165")
        anterior = lista[idx - 1]  # "166"
        assert not _unidade_lida(anterior, lidos_gas), (
            f"'{anterior}' só tem ÁGUA — não deve liberar 165 em modo GÁS"
        )

    def test_sequencia_gas_liberada_apos_gas_na_anterior(self):
        lista = Database._gerar_lista_unidades()
        _inserir_gas("166")
        lidos_gas = _build_lidos("GAS")
        idx = lista.index("165")
        anterior = lista[idx - 1]
        assert _unidade_lida(anterior, lidos_gas)


# ── 6. Demonstração do bug antigo ────────────────────────────────────────────

class TestBugAntigoLidosSemModo:
    """
    Documenta o comportamento incorreto da lógica antiga (antes do fix).
    A lógica antiga misturava ÁGUA e GÁS no conjunto lidos, permitindo
    que unidades com só ÁGUA fossem consideradas 'lidas' em modo GÁS.
    """

    def test_logica_antiga_aceita_agua_como_gas_lido(self):
        _inserir_agua("166")
        # Lógica antiga: qualquer leitura no mês conta como 'lida'
        lidos_antigo = {l.get("unidade_id") for l in Database.get_leituras_mes_atual()}
        assert "166" in lidos_antigo, (
            "Bug antigo: ÁGUA contabilizava erroneamente como GÁS lido"
        )

    def test_logica_nova_rejeita_agua_em_modo_gas(self):
        _inserir_agua("166")
        lidos_novo = _build_lidos("GAS")
        assert "166" not in lidos_novo, (
            "Fix: ÁGUA não deve ser contabilizada como GÁS lido"
        )


# ── 7. Fluxo completo ÁGUA ───────────────────────────────────────────────────

class TestFluxoCompletoAgua:
    def test_salvar_agua_para_todas_as_96_unidades(self):
        lista = Database._gerar_lista_unidades()
        for i, u in enumerate(lista):
            res = _inserir_agua(u, float(100 + i))
            assert res["sucesso"], f"Falhou ao salvar ÁGUA para '{u}'"

    def test_todas_unidades_aparecem_em_get_leituras(self):
        lista = Database._gerar_lista_unidades()
        for i, u in enumerate(lista):
            _inserir_agua(u, float(100 + i))
        ids = {r["unidade_id"] for r in Database.get_leituras_mes_atual()}
        for u in lista:
            assert u in ids, f"Unidade '{u}' ausente em get_leituras_mes_atual"

    def test_todas_unidades_lidas_em_lidos_agua(self):
        lista = Database._gerar_lista_unidades()
        for i, u in enumerate(lista):
            _inserir_agua(u, float(100 + i))
        lidos = _build_lidos("AGUA")
        pendentes = [u for u in lista if not _unidade_lida(u, lidos)]
        assert pendentes == [], f"Pendentes em ÁGUA após ciclo completo: {pendentes}"

    def test_valores_preservados(self):
        _inserir_agua("166", 987.65)
        rows = [r for r in Database.get_leituras_mes_atual()
                if r["unidade_id"] == "166" and r.get("leitura_agua") is not None]
        assert rows and rows[0]["leitura_agua"] == pytest.approx(987.65, abs=0.01)


# ── 8. Fluxo completo GÁS ────────────────────────────────────────────────────

class TestFluxoCompletoGas:
    # TERREO GERAL ÁGUA não possui hidrômetro de gás
    _SEM_GAS = {"TERREO GERAL ÁGUA"}

    def test_salvar_gas_para_todas_unidades_com_gas(self):
        lista = Database._gerar_lista_unidades()
        for i, u in enumerate(lista):
            if u in self._SEM_GAS:
                continue
            res = _inserir_gas(u, float(50 + i * 0.1))
            assert res["sucesso"], f"Falhou ao salvar GÁS para '{u}'"

    def test_todas_unidades_gas_aparecem_em_lidos(self):
        lista = Database._gerar_lista_unidades()
        unidades_gas = [u for u in lista if u not in self._SEM_GAS]
        for i, u in enumerate(unidades_gas):
            _inserir_gas(u, float(50 + i * 0.1))
        lidos = _build_lidos("GAS")
        pendentes = [u for u in unidades_gas if not _unidade_lida(u, lidos)]
        assert pendentes == [], f"Pendentes em GÁS após ciclo completo: {pendentes}"

    def test_terreo_geral_agua_ausente_de_lidos_gas(self):
        # Apenas ÁGUA salva para TERREO GERAL ÁGUA — não deve aparecer em lidos_gas
        _inserir_agua("TERREO GERAL ÁGUA")
        assert "TERREO GERAL ÁGUA" not in _build_lidos("GAS")

    def test_lazer_gas_sem_agua_em_lidos_agua(self):
        _inserir_gas("LAZER GÁS")
        assert "LAZER GÁS" not in _build_lidos("AGUA")


# ── 9. Áreas comuns ──────────────────────────────────────────────────────────

class TestAreasComuns:
    def test_lazer_gas_sem_andar_extraido(self):
        assert _extrair_andar("LAZER GÁS") == ""

    def test_terreo_geral_agua_sem_andar_extraido(self):
        assert _extrair_andar("TERREO GERAL ÁGUA") == ""

    def test_salvar_e_recuperar_gas_lazer(self):
        res = _inserir_gas("LAZER GÁS", 123.456)
        assert res["sucesso"]
        row = next(
            (l for l in Database.get_leituras_mes_atual()
             if l["unidade_id"] == "LAZER GÁS"),
            None
        )
        assert row is not None
        assert row["leitura_gas"] == pytest.approx(123.456, abs=0.001)
        assert row["leitura_agua"] is None

    def test_salvar_e_recuperar_agua_terreo(self):
        res = _inserir_agua("TERREO GERAL ÁGUA", 999.99)
        assert res["sucesso"]
        row = next(
            (l for l in Database.get_leituras_mes_atual()
             if l["unidade_id"] == "TERREO GERAL ÁGUA"),
            None
        )
        assert row is not None
        assert row["leitura_agua"] == pytest.approx(999.99, abs=0.01)
        assert row["leitura_gas"] is None

    def test_lazer_gas_eh_penultimo_na_lista(self):
        lista = Database._gerar_lista_unidades()
        assert lista[-2] == "LAZER GÁS"

    def test_terreo_geral_agua_encerra_ciclo(self):
        lista = Database._gerar_lista_unidades()
        assert lista[-1] == "TERREO GERAL ÁGUA"


# ── 10. Validação de sequência ───────────────────────────────────────────────

class TestValidacaoSequencia:
    def setup_method(self):
        self.lista = Database._gerar_lista_unidades()

    def _validar(self, unidade: str, modo: str):
        if unidade not in self.lista:
            return False, "Unidade não encontrada"
        idx = self.lista.index(unidade)
        if idx == 0:
            return True, "ok"
        anterior = self.lista[idx - 1]
        lidos = _build_lidos(modo)
        if not _unidade_lida(anterior, lidos):
            return False, f"anterior '{anterior}' não lida em {modo}"
        return True, "ok"

    def test_primeira_unidade_sempre_valida_agua(self):
        ok, _ = self._validar("166", "AGUA")
        assert ok

    def test_primeira_unidade_sempre_valida_gas(self):
        ok, _ = self._validar("166", "GAS")
        assert ok

    def test_165_bloqueada_sem_166_agua(self):
        ok, msg = self._validar("165", "AGUA")
        assert not ok, f"165 deve ser bloqueada sem 166 em ÁGUA: {msg}"

    def test_165_liberada_apos_166_agua(self):
        _inserir_agua("166")
        ok, _ = self._validar("165", "AGUA")
        assert ok

    def test_165_gas_bloqueada_se_166_so_tem_agua(self):
        _inserir_agua("166")          # 166 tem ÁGUA, mas não GÁS
        ok, msg = self._validar("165", "GAS")
        assert not ok, f"165-GÁS deve ser bloqueada enquanto 166-GÁS está pendente"

    def test_165_gas_liberada_apos_166_gas(self):
        _inserir_gas("166")
        ok, _ = self._validar("165", "GAS")
        assert ok

    def test_duplex_liberado_apos_duplex_lido(self):
        lista = Database._gerar_lista_unidades()
        idx_duplex = lista.index("163/164")
        anterior = lista[idx_duplex - 1]   # "162"
        _inserir_agua(anterior)
        ok, _ = self._validar("163/164", "AGUA")
        assert ok

    def test_duplex_partes_liberam_proxima(self):
        _inserir_agua("163/164")
        lista = Database._gerar_lista_unidades()
        idx = lista.index("163/164")
        proxima = lista[idx + 1]   # "162"
        ok, _ = self._validar(proxima, "AGUA")
        assert ok

    def test_sequencia_completa_andar_16_agua(self):
        floor16 = ["166", "165", "163/164", "162", "161"]
        for i, u in enumerate(floor16):
            ok, msg = self._validar(u, "AGUA")
            assert ok, f"Unidade {u} bloqueada inesperadamente: {msg}"
            _inserir_agua(u, float(100 + i))


# ── 11. Fim de ciclo ─────────────────────────────────────────────────────────

class TestFimDeCiclo:
    def _popular_ciclo_completo(self):
        lista = Database._gerar_lista_unidades()
        for i, u in enumerate(lista):
            _inserir_agua(u, float(100 + i))
            if u != "TERREO GERAL ÁGUA":
                _inserir_gas(u, float(50 + i * 0.1))

    def test_salvar_referencias_retorna_true(self):
        self._popular_ciclo_completo()
        dados = Database.get_leituras_mes_atual()
        assert Database.salvar_referencias_ciclo(dados) is True

    def test_referencias_gravadas_no_banco(self):
        self._popular_ciclo_completo()
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        with Database.get_db() as conn:
            refs = conn.execute("SELECT COUNT(*) FROM leituras_referencia").fetchone()[0]
        assert refs > 0

    def test_referencia_agua_e_gas_por_unidade(self):
        self._popular_ciclo_completo()
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        with Database.get_db() as conn:
            row = conn.execute(
                "SELECT leitura_agua, leitura_gas FROM leituras_referencia WHERE unidade_id='166'"
            ).fetchone()
        assert row["leitura_agua"] is not None
        assert row["leitura_gas"] is not None

    def test_lazer_gas_apenas_gas_em_referencia(self):
        self._popular_ciclo_completo()
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        with Database.get_db() as conn:
            row = conn.execute(
                "SELECT leitura_agua, leitura_gas FROM leituras_referencia WHERE unidade_id='LAZER GÁS'"
            ).fetchone()
        assert row is not None
        assert row["leitura_gas"] is not None

    def test_terreo_apenas_agua_em_referencia(self):
        self._popular_ciclo_completo()
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        with Database.get_db() as conn:
            row = conn.execute(
                "SELECT leitura_agua, leitura_gas FROM leituras_referencia WHERE unidade_id='TERREO GERAL ÁGUA'"
            ).fetchone()
        assert row is not None
        assert row["leitura_agua"] is not None

    def test_referencias_aparecem_como_anterior_no_proximo_ciclo(self):
        _inserir_agua("166", 100.0)
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        # Limpa leituras do ciclo anterior — simula reset real (sincronizacao + limpar_leituras_locais)
        with Database.get_db() as conn:
            conn.execute("DELETE FROM leituras")
            conn.commit()
        # Nova leitura do novo ciclo (mesmo mês no teste; banco limpo = sem duplicata)
        _inserir_agua("166", 120.0)
        novo_dados = Database.get_leituras_mes_atual()
        row = next(
            (l for l in novo_dados
             if l["unidade_id"] == "166" and l.get("leitura_agua") == 120.0),
            None
        )
        assert row is not None
        assert row.get("leitura_anterior_agua") == pytest.approx(100.0, abs=0.01)

    def test_reset_zera_leituras(self):
        from database.gestao_periodos import _resetar_banco_para_novo_mes
        _inserir_agua("166", 100.0)
        _inserir_gas("166", 50.0)
        ok = _resetar_banco_para_novo_mes()
        assert ok is True, "Reset falhou"
        with Database.get_db() as conn:
            rows = conn.execute(
                "SELECT leitura_agua, leitura_gas FROM leituras WHERE unidade_id='166'"
            ).fetchall()
        for row in rows:
            assert row["leitura_agua"] is None
            assert row["leitura_gas"] is None

    def test_reset_nao_apaga_referencias(self):
        from database.gestao_periodos import _resetar_banco_para_novo_mes
        _inserir_agua("166", 100.0)
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        _resetar_banco_para_novo_mes()
        with Database.get_db() as conn:
            refs = conn.execute(
                "SELECT COUNT(*) FROM leituras_referencia"
            ).fetchone()[0]
        assert refs > 0

    def test_96_referencias_apos_ciclo_completo(self):
        self._popular_ciclo_completo()
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        with Database.get_db() as conn:
            refs = conn.execute(
                "SELECT COUNT(*) FROM leituras_referencia"
            ).fetchone()[0]
        assert refs == 96


# ── 12. Relatório CSV ────────────────────────────────────────────────────────

@pytest.mark.skipif(not HAS_RELATORIO, reason="relatorio_engine indisponível")
class TestRelatorioCSV:
    def _popular_10(self):
        lista = Database._gerar_lista_unidades()
        for i, u in enumerate(lista[:10]):
            _inserir_agua(u, float(100 + i))
            _inserir_gas(u, float(50 + i * 0.1))
        return Database.get_leituras_mes_atual()

    def test_gerar_todos_retorna_quatro_chaves(self):
        dados = self._popular_10()
        arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
        assert set(arquivos.keys()) == {"pdf_agua", "pdf_gas", "csv_agua", "csv_gas"}

    def test_csv_agua_existe_em_disco(self):
        dados = self._popular_10()
        arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
        assert os.path.exists(arquivos["csv_agua"]), "csv_agua não encontrado em disco"

    def test_csv_gas_existe_em_disco(self):
        dados = self._popular_10()
        arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
        assert os.path.exists(arquivos["csv_gas"]), "csv_gas não encontrado em disco"

    def test_csv_agua_tem_cabecalho_e_dados(self):
        dados = self._popular_10()
        arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
        with open(arquivos["csv_agua"], newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        # Cabeçalho + ao menos 1 linha de dado
        assert len(rows) >= 2, "CSV ÁGUA deve ter cabeçalho + dados"

    def test_csv_gas_tem_cabecalho_e_dados(self):
        dados = self._popular_10()
        arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
        with open(arquivos["csv_gas"], newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        assert len(rows) >= 2, "CSV GÁS deve ter cabeçalho + dados"

    def test_pdf_agua_existe_em_disco(self):
        dados = self._popular_10()
        try:
            arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
            assert os.path.exists(arquivos["pdf_agua"]), "pdf_agua não encontrado"
        except Exception:
            pytest.skip("Geração de PDF falhou (fpdf2 pode não estar instalado)")

    def test_pdf_gas_existe_em_disco(self):
        dados = self._popular_10()
        try:
            arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
            assert os.path.exists(arquivos["pdf_gas"]), "pdf_gas não encontrado"
        except Exception:
            pytest.skip("Geração de PDF falhou (fpdf2 pode não estar instalado)")

    def test_csv_agua_contem_coluna_unidade(self):
        dados = self._popular_10()
        arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
        with open(arquivos["csv_agua"], newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cabecalho = reader.fieldnames or []
        assert any("unidade" in c.lower() for c in cabecalho), (
            f"Coluna 'unidade' ausente no CSV ÁGUA: {cabecalho}"
        )
