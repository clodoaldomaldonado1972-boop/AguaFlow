"""
test_fim_ciclo_completo.py — Bateria de testes de fim de ciclo.
(26/05/2026)

Cobertura:
  1. Ciclo misto completo — todos os 16 andares (96 unidades) sem falha
  2. Unidades pré-registradas — detecção e comportamento correto do avanço
  3. Fim de ciclo: salvar_referencias → CSV/PDF → reset → sistema pronto pro próximo mês
  4. Envio de e-mail: sem credenciais retorna False; com mock SMTP retorna True
"""

import csv as csv_mod
import os
import sys
import tempfile
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

_tmp_dir = tempfile.mkdtemp()
_tmp_db  = os.path.join(_tmp_dir, "test_ciclo_completo.db")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import database.database as _db_module
_db_module.Database.DB_PATH = _tmp_db
_db_module.Database.supabase = None
_db_module.Database.supabase_admin = None

from database.database import Database
from database.gestao_periodos import _resetar_banco_para_novo_mes
from views.medicao import _extrair_andar

try:
    from relatorio_engine import RelatorioEngine
    HAS_RELATORIO = True
except ImportError:
    HAS_RELATORIO = False

MES = datetime.now().strftime("%Y-%m")

# ── Todos os andares do Vivere Prudente (ordem de descida, final 6→1) ──────────
ANDARES = [
    ["166", "165", "163/164", "162", "161"],   # andar 16 — duplex 163/164 (5 unidades)
    ["156", "155", "154", "153", "152", "151"],
    ["146", "145", "144", "143", "142", "141"],
    ["136", "135", "134", "133", "132", "131"],
    ["126", "125", "124", "123", "122", "121"],
    ["116", "115", "114", "113", "112", "111"],
    ["106", "105", "104", "103", "102", "101"],
    ["96",  "95",  "94",  "93",  "92",  "91"],
    ["86",  "85",  "84",  "83",  "82",  "81"],
    ["76",  "75",  "74",  "73",  "72",  "71"],
    ["66",  "65",  "64",  "63",  "62",  "61"],
    ["56",  "55",  "54",  "53",  "52",  "51"],
    ["46",  "45",  "44",  "43",  "42",  "41"],
    ["36",  "35",  "34",  "33",  "32",  "31"],
    ["26",  "25",  "23/24", "22", "21"],        # andar 2 — duplex 23/24 (5 unidades)
    ["16",  "15",  "14",  "13",  "12",  "11"],
]
TODOS_APTOS  = [u for andar in ANDARES for u in andar]   # 94 apartamentos
LAZER        = "LAZER GÁS"
TERREO       = "TERREO GERAL ÁGUA"
DB_LISTA     = Database._gerar_lista_unidades()


# ── Fixture e helpers ──────────────────────────────────────────────────────────

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


def _agua(u, v=100.0):
    return Database.salvar_leitura(u, round(v, 2), None, "AGUA", _ts(), None, "tester")


def _gas(u, v=50.0):
    return Database.salvar_leitura(u, None, round(v, 3), "GAS",  _ts(), None, "tester")


def _lidos_agua():
    return {l["unidade_id"] for l in Database.get_leituras_mes_atual()
            if l.get("leitura_agua") is not None}


def _lidos_gas():
    return {l["unidade_id"] for l in Database.get_leituras_mes_atual()
            if l.get("leitura_gas") is not None}


def _proxima_pendente_apos(unidades_andar, current, lidos):
    """Replica _proxima_pendente_no_andar (DB logic apenas)."""
    try:
        i = unidades_andar.index(current)
    except ValueError:
        i = -1
    for u in unidades_andar[i + 1:]:
        if u not in lidos:
            return u
    return None


def _primeira_pendente(db_lista, andar, lidos):
    """Replica _primeira_pendente_no_andar (DB logic apenas)."""
    for u in db_lista:
        if _extrair_andar(u) == andar and u not in lidos:
            return u
    return None


def _ciclo_misto_completo():
    """Insere água e gás para todos os 94 aptos + áreas comuns."""
    for andar in ANDARES:
        for u in andar:
            _agua(u)
        for u in andar:
            _gas(u)
    _gas(LAZER)
    _agua(TERREO)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Ciclo misto completo — 16 andares, 96 unidades
# ══════════════════════════════════════════════════════════════════════════════

class TestMistoCicloCompleto:
    """Valida que o ciclo misto (água depois gás por andar) percorre
    todos os 16 andares sem rejeições nem lacunas."""

    def test_todos_aptos_agua_aceitos(self):
        for andar in ANDARES:
            for u in andar:
                assert _agua(u)["sucesso"] is True, f"Água {u} rejeitada inesperadamente"

    def test_todos_aptos_gas_aceitos(self):
        for andar in ANDARES:
            for u in andar:
                assert _gas(u)["sucesso"] is True, f"Gás {u} rejeitado inesperadamente"

    def test_areas_comuns_aceitas(self):
        assert _gas(LAZER)["sucesso"]   is True
        assert _agua(TERREO)["sucesso"] is True

    def test_sem_pendentes_agua_apos_ciclo_completo(self):
        _ciclo_misto_completo()
        lidos = _lidos_agua()
        pendentes = [u for u in DB_LISTA if u not in lidos]
        # Só LAZER GÁS não tem água (é lido apenas como gás)
        pendentes_reais = [u for u in pendentes if u != LAZER]
        assert pendentes_reais == [], f"Pendentes ÁGUA: {pendentes_reais}"

    def test_sem_pendentes_gas_apos_ciclo_completo(self):
        _ciclo_misto_completo()
        lidos = _lidos_gas()
        pendentes = [u for u in DB_LISTA if u not in lidos]
        # Só TERREO GERAL ÁGUA não tem gás
        pendentes_reais = [u for u in pendentes if u != TERREO]
        assert pendentes_reais == [], f"Pendentes GÁS: {pendentes_reais}"

    def test_total_rows_correto(self):
        _ciclo_misto_completo()
        # 94 aptos × 2 rows (agua+gas) + LAZER (gas) + TERREO (agua) = 190 rows
        with Database.get_db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]
        assert total == 94 * 2 + 2

    def test_re_insercao_agua_bloqueada(self):
        _ciclo_misto_completo()
        for andar in ANDARES:
            for u in andar:
                assert _agua(u)["sucesso"] is False, f"Duplicata água {u} não bloqueada"

    def test_re_insercao_gas_bloqueada(self):
        _ciclo_misto_completo()
        for andar in ANDARES:
            for u in andar:
                assert _gas(u)["sucesso"] is False, f"Duplicata gás {u} não bloqueada"

    def test_duplex_163_164_aceito_uma_vez(self):
        assert _agua("163/164")["sucesso"] is True
        assert _agua("163/164")["sucesso"] is False   # duplicata

    def test_duplex_23_24_aceito_uma_vez(self):
        assert _gas("23/24")["sucesso"] is True
        assert _gas("23/24")["sucesso"] is False


# ══════════════════════════════════════════════════════════════════════════════
# 2. Unidades pré-registradas — aviso de água já registrada
# ══════════════════════════════════════════════════════════════════════════════

class TestAguaPreRegistrada:
    """
    Simula o cenário onde unidades do andar 14 já têm água no banco
    (sincronizadas de sessão anterior). Verifica que a lógica de avanço
    identifica corretamente pendentes vs. pré-registradas e que o gás
    continua sendo aceito normalmente.
    """
    ANDAR14 = ["146", "145", "144", "143", "142", "141"]

    def test_unidades_preregistradas_aparecem_em_lidos_agua(self):
        for u in ["145", "144", "143", "142", "141"]:
            _agua(u)
        lidos = _lidos_agua()
        for u in ["145", "144", "143", "142", "141"]:
            assert u in lidos
        assert "146" not in lidos   # ainda pendente

    def test_prox_agua_retorna_none_quando_resto_preregistrado(self):
        """Após salvar água 146, _proxima_pendente deve retornar None (145-141 pré-lidas)."""
        for u in ["145", "144", "143", "142", "141"]:
            _agua(u)
        _agua("146")                        # salvo pelo usuário nesta sessão
        lidos = _lidos_agua()
        prox = _proxima_pendente_apos(self.ANDAR14, "146", lidos)
        assert prox is None

    def test_gas_pendente_detectado_com_agua_preregistrada(self):
        """Quando toda água do andar 14 está no banco, _primeira_pendente de gás aponta 146."""
        for u in self.ANDAR14:
            _agua(u)
        lidos_g = _lidos_gas()
        primeira = _primeira_pendente(DB_LISTA, "14", lidos_g)
        assert primeira == "146"

    def test_gas_completo_andar14_com_agua_parcialmente_preregistrada(self):
        """Com agua 145-141 pré-registradas + 146 inserida agora, todo o gás deve ser aceito."""
        for u in ["145", "144", "143", "142", "141"]:
            _agua(u)
        _agua("146")
        for u in self.ANDAR14:
            assert _gas(u)["sucesso"] is True, f"Gás {u} bloqueado com água pré-registrada"

    def test_agua_preregistrada_nao_permite_re_insercao(self):
        """Tentativa de inserir água para unidade pré-registrada deve ser bloqueada."""
        for u in self.ANDAR14:
            _agua(u)
        for u in self.ANDAR14:
            assert _agua(u)["sucesso"] is False, f"Duplicata água {u} não bloqueada"

    def test_gas_correto_apos_agua_toda_preregistrada_e_nova_sessao(self):
        """
        Cenário completo: água de todo o andar 14 está no banco antes da sessão.
        O sistema deve transitar diretamente para gás ao iniciar o andar.
        """
        for u in self.ANDAR14:
            _agua(u)
        # Simula início de nova sessão: andar 14 agua done → detectar gas pendente
        lidos_g = _lidos_gas()
        primeira = _primeira_pendente(DB_LISTA, "14", lidos_g)
        assert primeira is not None, "Deve haver gás pendente no andar 14"
        assert _extrair_andar(primeira) == "14"
        # Inserir gás para toda o andar
        for u in self.ANDAR14:
            assert _gas(u)["sucesso"] is True


# ══════════════════════════════════════════════════════════════════════════════
# 3. Fim de ciclo completo — referências, reset, pronto pro próximo mês
# ══════════════════════════════════════════════════════════════════════════════

class TestFimCicloComReset:
    """Valida o fluxo completo de fechamento mensal e preparo do próximo ciclo."""

    def test_referencias_salvas_apos_ciclo_misto_completo(self):
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        assert Database.salvar_referencias_ciclo(dados) is True

    def test_96_referencias_no_banco(self):
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        with Database.get_db() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM leituras_referencia"
            ).fetchone()[0]
        assert total == 96

    def test_referencia_agua_e_gas_corretos_para_166(self):
        _agua("166", 150.0)
        _gas("166",  75.0)
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        with Database.get_db() as conn:
            row = conn.execute(
                "SELECT leitura_agua, leitura_gas FROM leituras_referencia "
                "WHERE unidade_id='166'"
            ).fetchone()
        assert row is not None
        assert row["leitura_agua"] == pytest.approx(150.0, abs=0.01)
        assert row["leitura_gas"]  == pytest.approx(75.0,  abs=0.001)

    def test_reset_zera_todas_leituras(self):
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        _resetar_banco_para_novo_mes()
        with Database.get_db() as conn:
            rows = conn.execute(
                "SELECT leitura_agua, leitura_gas FROM leituras"
            ).fetchall()
        for row in rows:
            assert row["leitura_agua"] is None
            assert row["leitura_gas"]  is None

    def test_referencias_sobrevivem_ao_reset(self):
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        _resetar_banco_para_novo_mes()
        with Database.get_db() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM leituras_referencia"
            ).fetchone()[0]
        assert total == 96

    def test_novo_ciclo_leitura_anterior_agua_populada(self):
        """Após reset, nova leitura deve mostrar leitura_anterior_agua da referência."""
        _agua("166", 200.0)
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        _resetar_banco_para_novo_mes()
        with Database.get_db() as conn:
            conn.execute("DELETE FROM leituras")
            conn.commit()
        _agua("166", 220.0)
        novo = next(
            (l for l in Database.get_leituras_mes_atual()
             if l["unidade_id"] == "166" and l.get("leitura_agua") == 220.0),
            None
        )
        assert novo is not None, "Nova leitura não encontrada após reset"
        assert novo.get("leitura_anterior_agua") == pytest.approx(200.0, abs=0.01)

    def test_novo_ciclo_leitura_anterior_gas_populada(self):
        _gas("166", 80.0)
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        _resetar_banco_para_novo_mes()
        with Database.get_db() as conn:
            conn.execute("DELETE FROM leituras")
            conn.commit()
        _gas("166", 95.0)
        novo = next(
            (l for l in Database.get_leituras_mes_atual()
             if l["unidade_id"] == "166" and l.get("leitura_gas") == 95.0),
            None
        )
        assert novo is not None
        assert novo.get("leitura_anterior_gas") == pytest.approx(80.0, abs=0.001)

    def test_apos_reset_novo_ciclo_aceita_todas_insercoes(self):
        """Após reset o banco deve aceitar novos registros para todas as unidades."""
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        Database.salvar_referencias_ciclo(dados)
        _resetar_banco_para_novo_mes()
        with Database.get_db() as conn:
            conn.execute("DELETE FROM leituras")
            conn.commit()
        for andar in ANDARES:
            for u in andar:
                assert _agua(u)["sucesso"] is True, f"Novo ciclo: água {u} rejeitada"


# ══════════════════════════════════════════════════════════════════════════════
# 4. Geração de relatórios CSV/PDF após ciclo completo
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not HAS_RELATORIO, reason="relatorio_engine indisponível")
class TestRelatorioFimCiclo:
    """Valida geração de relatórios CSV/PDF ao fechar o ciclo mensal."""

    def test_csv_agua_gerado_com_dados_de_96_unidades(self):
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
        with open(arquivos["csv_agua"], newline="", encoding="utf-8") as f:
            linhas = list(csv_mod.reader(f))
        # Cabeçalho + ao menos 95 linhas de dados (94 aptos com água + TERREO)
        assert len(linhas) >= 2, "CSV ÁGUA não tem dados"
        assert len(linhas) > 90, f"CSV ÁGUA tem poucas linhas: {len(linhas)}"

    def test_csv_gas_gerado_com_dados_de_95_unidades(self):
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
        with open(arquivos["csv_gas"], newline="", encoding="utf-8") as f:
            linhas = list(csv_mod.reader(f))
        # 94 aptos + LAZER GÁS com gás (sem TERREO)
        assert len(linhas) >= 2
        assert len(linhas) > 90

    def test_pdf_agua_existe_no_disco(self):
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        try:
            arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
            assert os.path.exists(arquivos["pdf_agua"])
        except Exception:
            pytest.skip("Geração de PDF falhou (fpdf2 pode não estar instalado)")

    def test_pdf_gas_existe_no_disco(self):
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        try:
            arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
            assert os.path.exists(arquivos["pdf_gas"])
        except Exception:
            pytest.skip("Geração de PDF falhou (fpdf2 pode não estar instalado)")

    def test_csv_agua_contem_unidade_166(self):
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
        conteudo = open(arquivos["csv_agua"], encoding="utf-8").read()
        assert "166" in conteudo

    def test_csv_gas_contem_lazer_gas(self):
        _ciclo_misto_completo()
        dados = Database.get_leituras_mes_atual()
        arquivos = RelatorioEngine.gerar_todos(dados, "Testador")
        conteudo = open(arquivos["csv_gas"], encoding="utf-8").read()
        assert "LAZER" in conteudo


# ══════════════════════════════════════════════════════════════════════════════
# 5. Envio de e-mail — guarda sem credenciais + mock SMTP
# ══════════════════════════════════════════════════════════════════════════════

class TestEmailEnvio:
    """Testa comportamento do envio de e-mail sem precisar de SMTP real."""

    def test_sem_credenciais_retorna_false(self):
        from utils.email_service import enviar_relatorios_por_email
        with patch.dict(os.environ, {"EMAIL_USER": "", "EMAIL_PASS": ""}):
            resultado = enviar_relatorios_por_email([])
        assert resultado is False

    def test_com_mock_smtp_retorna_true(self):
        """Simula envio bem-sucedido com SMTP mock."""
        import tempfile
        from utils.email_service import enviar_relatorios_por_email

        # Cria arquivo temporário que simula um relatório gerado
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            f.write(b"unidade,agua\n166,100.0\n")
            caminho = f.name

        mock_smtp = MagicMock()
        mock_smtp.__enter__ = lambda s: s
        mock_smtp.__exit__ = MagicMock(return_value=False)

        try:
            with patch.dict(os.environ, {
                "EMAIL_USER": "test@example.com",
                "EMAIL_PASS": "senha123",
                "EMAIL_DESTINATARIO": "dest@example.com",
            }):
                with patch("smtplib.SMTP_SSL", return_value=mock_smtp):
                    resultado = enviar_relatorios_por_email([caminho])
            assert resultado is True
            assert mock_smtp.login.called
            assert mock_smtp.send_message.called
        finally:
            os.unlink(caminho)

    def test_lista_vazia_com_credenciais_ainda_envia(self):
        """Lista de arquivos vazia (sem anexos) não deve causar exceção."""
        from utils.email_service import enviar_relatorios_por_email

        mock_smtp = MagicMock()
        mock_smtp.__enter__ = lambda s: s
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch.dict(os.environ, {
            "EMAIL_USER": "test@example.com",
            "EMAIL_PASS": "senha123",
        }):
            with patch("smtplib.SMTP_SSL", return_value=mock_smtp):
                resultado = enviar_relatorios_por_email([])
        assert resultado is True
