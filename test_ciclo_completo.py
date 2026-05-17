"""
Teste automatizado do ciclo completo do AguaFlow:
  1. Inicializa banco
  2. Insere leituras de agua e gas para TODAS as unidades
  3. Gera backup ZIP
  4. Gera PDF agua, PDF gas, CSV agua, CSV gas
  5. Envia relatorios por e-mail
  6. Salva referencias para proximo ciclo

Executar: python test_ciclo_completo.py
"""

import os
import sys
import random
import logging
from datetime import datetime

# Garante que o diretorio raiz do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger_config import setup_logging
setup_logging()
logger = logging.getLogger("TesteCicloCompleto")

from database.database import Database
from utils.backup import BackupManager
from relatorio_engine import RelatorioEngine

# ── Configuracao do teste ──────────────────────────────────────────────────────
LEITURISTA_TESTE = "Automatico (Teste)"
SEED = 42
random.seed(SEED)

LINHA = "=" * 65


def _resultado(ok, msg):
    status = "[ OK ]" if ok else "[ERRO]"
    print(f"  {status} {msg}")
    return ok


# ── 1. INICIALIZA BANCO ────────────────────────────────────────────────────────
def passo_inicializar():
    print(f"\n{LINHA}")
    print("  PASSO 1: Inicializar banco de dados SQLite")
    print(LINHA)
    try:
        Database.inicializar_tabelas()
        return _resultado(True, "Tabelas criadas/verificadas com sucesso.")
    except Exception as e:
        return _resultado(False, f"Falha: {e}")


# ── 2. INSERIR LEITURAS ────────────────────────────────────────────────────────
def passo_inserir_leituras():
    print(f"\n{LINHA}")
    print("  PASSO 2: Inserir leituras de AGUA e GAS para todas as unidades")
    print(LINHA)

    unidades = Database._gerar_lista_unidades()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sucessos = 0
    falhas = []

    # Busca referencias anteriores para simular leituras crescentes
    refs = {}
    try:
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT unidade_id, leitura_agua, leitura_gas FROM leituras_referencia")
            for row in cursor.fetchall():
                refs[row[0]] = {"agua": row[1] or 0.0, "gas": row[2] or 0.0}
    except Exception:
        pass

    for unidade in unidades:
        ref_agua = refs.get(unidade, {}).get("agua", 0.0)
        ref_gas  = refs.get(unidade, {}).get("gas",  0.0)

        # Simula consumo mensal realista
        consumo_agua = round(random.uniform(3.5, 18.0), 3)
        consumo_gas  = round(random.uniform(0.5,  6.0), 3)

        agua = round(ref_agua + consumo_agua, 3)
        gas  = round(ref_gas  + consumo_gas,  3)

        # Unidades exclusivas: LAZER GAS so tem gas; TERREO GERAL AGUA so tem agua
        if unidade == "LAZER GAS":
            agua = None
        elif unidade == "TERREO GERAL AGUA":
            gas = None

        resultado = Database.salvar_leitura(
            unidade=unidade,
            valor_agua=agua,
            valor_gas=gas,
            modo="Automatico",
            data_hora=agora,
            leiturista=LEITURISTA_TESTE,
        )

        if resultado.get("sucesso"):
            sucessos += 1
        else:
            falhas.append(unidade)

    total = len(unidades)
    ok = len(falhas) == 0
    _resultado(ok, f"{sucessos}/{total} unidades inseridas.")
    if falhas:
        _resultado(False, f"Falhas: {falhas}")
    return ok, unidades


# ── 3. BACKUP ──────────────────────────────────────────────────────────────────
def passo_backup():
    print(f"\n{LINHA}")
    print("  PASSO 3: Gerar backup ZIP (banco + relatorios existentes)")
    print(LINHA)
    try:
        ok = BackupManager.executar_backup_seguranca()
        info = BackupManager.inspecionar_ultimo_backup()
        if ok and info:
            _resultado(True, f"ZIP: {os.path.basename(info['arquivo'])} ({info['tamanho_kb']} KB)")
            _resultado(True, f"Conteudo: {info['conteudo']}")
        else:
            _resultado(ok, "Backup executado (sem relatorios pre-existentes ainda).")
        return ok
    except Exception as e:
        return _resultado(False, f"Falha: {e}")


# ── 4. GERAR RELATORIOS ────────────────────────────────────────────────────────
def passo_gerar_relatorios():
    print(f"\n{LINHA}")
    print("  PASSO 4: Gerar PDF agua, PDF gas, CSV agua, CSV gas")
    print(LINHA)
    try:
        dados = Database.get_leituras_mes_atual()
        if not dados:
            return _resultado(False, "Nenhuma leitura encontrada para o mes atual."), None

        _resultado(True, f"{len(dados)} leituras carregadas do banco.")

        arquivos = RelatorioEngine.gerar_todos(dados, leiturista=LEITURISTA_TESTE)

        todos_ok = True
        for chave, caminho in arquivos.items():
            existe = caminho and os.path.exists(caminho)
            tamanho = os.path.getsize(caminho) // 1024 if existe else 0
            _resultado(existe, f"{chave}: {os.path.basename(caminho) if caminho else 'N/A'} ({tamanho} KB)")
            if not existe:
                todos_ok = False

        return todos_ok, arquivos
    except Exception as e:
        logger.exception("Erro na geracao de relatorios")
        return _resultado(False, f"Excecao: {e}"), None


# ── 5. ENVIAR E-MAIL ───────────────────────────────────────────────────────────
def passo_enviar_email(arquivos):
    print(f"\n{LINHA}")
    print("  PASSO 5: Enviar relatorios por e-mail")
    print(LINHA)
    try:
        ok, msg = RelatorioEngine.enviar_relatorios_por_email(arquivos)
        _resultado(ok, msg)
        return ok
    except Exception as e:
        return _resultado(False, f"Excecao: {e}")


# ── 6. SALVAR REFERENCIAS ──────────────────────────────────────────────────────
def passo_salvar_referencias():
    print(f"\n{LINHA}")
    print("  PASSO 6: Salvar referencias do ciclo para o proximo mes")
    print(LINHA)
    try:
        dados = Database.get_leituras_mes_atual()
        ok = Database.salvar_referencias_ciclo(dados)
        _resultado(ok, f"{len(dados)} referencias salvas.")
        return ok
    except Exception as e:
        return _resultado(False, f"Falha: {e}")


# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'#' * 65}")
    print("  AGUAFLOW — TESTE AUTOMATICO DE CICLO COMPLETO")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'#' * 65}")

    resultados = {}

    resultados["1_init"]       = passo_inicializar()
    ok_leit, _unidades         = passo_inserir_leituras()
    resultados["2_leituras"]   = ok_leit
    resultados["3_backup"]     = passo_backup()
    ok_rel, arquivos           = passo_gerar_relatorios()
    resultados["4_relatorios"] = ok_rel

    if ok_rel and arquivos:
        resultados["5_email"]  = passo_enviar_email(arquivos)
    else:
        resultados["5_email"]  = False
        print(f"\n  [SKIP] Envio de e-mail ignorado (geracao de relatorios falhou).")

    resultados["6_referencias"] = passo_salvar_referencias()

    # ── RESUMO FINAL ──────────────────────────────────────────────────────────
    print(f"\n{'#' * 65}")
    print("  RESUMO FINAL")
    print(f"{'#' * 65}")
    total = len(resultados)
    passou = sum(1 for v in resultados.values() if v)
    for passo, ok in resultados.items():
        status = "[ OK ]" if ok else "[ERRO]"
        print(f"  {status} {passo}")
    print(f"\n  Resultado: {passou}/{total} passos OK")
    print(f"{'#' * 65}\n")

    return 0 if passou == total else 1


if __name__ == "__main__":
    sys.exit(main())
