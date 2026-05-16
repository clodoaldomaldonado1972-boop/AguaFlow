"""
Script de Teste Completo — AguaFlow MVP
Insere leituras simuladas para todas as 98 unidades, gera relatórios e testa envio de email.
Execução: python teste_completo.py
"""

import sys
import os
import sqlite3
import random
from datetime import datetime

# Garante que o projeto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import Database
from relatorio_engine import RelatorioEngine

PASS = "[OK]"
FAIL = "[FALHA]"
WARN = "[AVISO]"

resultados = []


def log(status, titulo, detalhe=""):
    simbolo = PASS if status else FAIL
    msg = f"{simbolo} {titulo}"
    if detalhe:
        msg += f"\n     {detalhe}"
    print(msg)
    resultados.append((status, titulo, detalhe))


# ─────────────────────────────────────────────────────────────────────────────
# 0. INICIALIZAÇÃO
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  AGUAFLOW -- TESTE COMPLETO DE CICLO DE LEITURAS")
print("=" * 60 + "\n")

Database.inicializar_tabelas()
log(True, "Banco SQLite inicializado")

# Limpa leituras do mês atual para o teste ser reproduzível
mes_atual = datetime.now().strftime('%Y-%m')
with Database.get_db() as conn:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leituras WHERE data_hora_coleta LIKE ?", (f"{mes_atual}%",))
    conn.commit()
    removidas = cursor.rowcount
log(True, f"Limpeza de leituras do mês ({mes_atual})", f"{removidas} registros removidos")


# ─────────────────────────────────────────────────────────────────────────────
# 1. GERAR LISTA DE UNIDADES
# ─────────────────────────────────────────────────────────────────────────────
print("\n-- ETAPA 1: Lista de Unidades --")
unidades = Database._gerar_lista_unidades()
total = len(unidades)

duplex_ok = "163/164" in unidades and "23/24" in unidades
nao_divididos = "163" not in unidades and "164" not in unidades and "23" not in unidades and "24" not in unidades

log(total == 96, f"Total de unidades geradas: {total}", "Esperado: 96 (16x6 - 4 individuais + 2 duplex + 2 areas comuns)")
log(duplex_ok, "Unidades duplex presentes como string única", "'163/164' e '23/24' na lista")
log(nao_divididos, "Duplex NÃO aparecem separados", "163, 164, 23, 24 ausentes da lista")

print(f"\n  Primeiras 10 unidades: {unidades[:10]}")
print(f"  Duplex na lista: {[u for u in unidades if '/' in u]}")
print(f"  Áreas comuns: {unidades[-2:]}")


# ─────────────────────────────────────────────────────────────────────────────
# 2. INSERIR LEITURAS SIMULADAS — FLUXO POR HALL (água → gás → próximo hall)
# ─────────────────────────────────────────────────────────────────────────────
print("\n-- ETAPA 2: Inserção de Leituras (Água + Gás por Hall) --")

# Áreas comuns que só têm agua ou só têm gas
SEM_GAS = {"TERREO GERAL ÁGUA"}
SEM_AGUA = {"LAZER GÁS"}

random.seed(42)
erros_insercao = []
data_base = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def valor_agua():
    return round(random.uniform(150.0, 490.0), 2)

def valor_gas():
    return round(random.uniform(3.0, 18.0), 3)

# Inserção ÁGUA para todas as unidades
print("  Inserindo leituras de ÁGUA...")
for i, u in enumerate(unidades):
    if u in SEM_AGUA:
        continue
    ts = datetime.now().strftime(f'%Y-%m-%d %H:%M:{i:02d}') if i < 60 else data_base
    v_agua = valor_agua()
    res = Database.salvar_leitura(u, v_agua, None, "AGUA", ts, None, "Zelador-Teste")
    if not res["sucesso"]:
        erros_insercao.append(f"AGUA-{u}: {res.get('erro')}")

log(len(erros_insercao) == 0, f"Leituras de ÁGUA inseridas", f"{len(unidades) - len(SEM_AGUA)} unidades")

# Inserção GÁS para todas as unidades (exceto áreas sem gás)
print("  Inserindo leituras de GÁS...")
erros_gas = []
for i, u in enumerate(unidades):
    if u in SEM_GAS:
        continue
    ts = datetime.now().strftime(f'%Y-%m-%d %H:%M:{i:02d}') if i < 60 else data_base
    v_gas = valor_gas()
    res = Database.salvar_leitura(u, None, v_gas, "GAS", ts, None, "Zelador-Teste")
    if not res["sucesso"]:
        erros_gas.append(f"GAS-{u}: {res.get('erro')}")

log(len(erros_gas) == 0, f"Leituras de GÁS inseridas", f"{len(unidades) - len(SEM_GAS)} unidades")

if erros_insercao or erros_gas:
    for e in erros_insercao + erros_gas:
        print(f"  {FAIL} {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 3. VERIFICAR BANCO DE DADOS
# ─────────────────────────────────────────────────────────────────────────────
print("\n-- ETAPA 3: Verificação do Banco de Dados --")

leituras = Database.get_leituras_mes_atual()
total_registros = len(leituras)

# Unidades duplex: devem aparecer como "163/164", NÃO como "163" ou "164" separados
unidades_no_banco = {l['unidade_id'] for l in leituras}
duplex_salvo_correto = "163/164" in unidades_no_banco and "23/24" in unidades_no_banco
duplex_nao_dividido = "163" not in unidades_no_banco and "164" not in unidades_no_banco

agua_count = sum(1 for l in leituras if l.get('leitura_agua') is not None)
gas_count = sum(1 for l in leituras if l.get('leitura_gas') is not None)

log(total_registros > 0, f"Total de registros no banco: {total_registros}")
log(duplex_salvo_correto, "Duplex salvo corretamente como '163/164' e '23/24'")
log(duplex_nao_dividido, "Duplex NÃO dividido em registros separados no banco")
log(agua_count > 0, f"Registros com leitura_agua: {agua_count}")
log(gas_count > 0, f"Registros com leitura_gas: {gas_count}")

# Mostra amostra das duplex no banco
duplex_registros = [l for l in leituras if '/' in l.get('unidade_id', '')]
print(f"\n  Registros duplex no banco: {len(duplex_registros)}")
for r in duplex_registros[:4]:
    print(f"    unidade_id={r['unidade_id']}  agua={r.get('leitura_agua')}  gas={r.get('leitura_gas')}  tipo={r.get('tipo', '')}")


# ─────────────────────────────────────────────────────────────────────────────
# 4 e 5. GERAÇÃO DE TODOS OS RELATÓRIOS (PDF agua, PDF gas, CSV agua, CSV gas)
# ─────────────────────────────────────────────────────────────────────────────
print("\n-- ETAPA 4+5: Geração de Relatórios (4 arquivos) --")
arquivos = {}
try:
    arquivos = RelatorioEngine.gerar_todos(leituras, leiturista="Zelador-Teste")

    for chave, caminho in arquivos.items():
        existe = os.path.exists(caminho) and os.path.getsize(caminho) > 100
        size_kb = os.path.getsize(caminho) // 1024 if existe else 0
        log(existe, f"Arquivo {chave}: {os.path.basename(caminho)}", f"{size_kb} KB | {caminho}")

    # Verifica ordenacao no CSV de agua
    csv_agua = arquivos.get("csv_agua")
    if csv_agua and os.path.exists(csv_agua):
        with open(csv_agua, encoding='utf-8-sig') as f:
            linhas = f.readlines()
        print(f"\n  CSV agua: {len(linhas)-1} unidades")
        print(f"  Linha 2 (menor unidade): {linhas[1].strip() if len(linhas) > 1 else 'vazio'}")
        print(f"  Linha -1 (maior unidade): {linhas[-1].strip() if len(linhas) > 1 else 'vazio'}")

    # Verifica leiturista no CSV
    if csv_agua and os.path.exists(csv_agua):
        with open(csv_agua, encoding='utf-8-sig') as f:
            conteudo = f.read()
        tem_leiturista = "Zelador-Teste" in conteudo
        log(tem_leiturista, "Leiturista presente no CSV", "'Zelador-Teste' encontrado")

except Exception as ex:
    log(False, "Falha ao gerar relatorios", str(ex))


# ─────────────────────────────────────────────────────────────────────────────
# 6. ENVIO DE EMAIL
# ─────────────────────────────────────────────────────────────────────────────
print("\n-- ETAPA 6: Envio de Email (4 anexos) --")
if arquivos:
    try:
        sucesso_email, msg_email = RelatorioEngine.enviar_relatorios_por_email(arquivos)
        log(sucesso_email, "Email enviado com sucesso (4 anexos)", msg_email)
    except Exception as ex:
        log(False, "Falha no envio de email", str(ex))
else:
    log(False, "Email nao enviado", "Arquivos nao gerados")


# ─────────────────────────────────────────────────────────────────────────────
# 7. RESUMO FINAL
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  RESUMO DO TESTE")
print("=" * 60)

passou = sum(1 for r in resultados if r[0])
falhou = sum(1 for r in resultados if not r[0])

for ok, titulo, detalhe in resultados:
    simbolo = PASS if ok else FAIL
    print(f"  {simbolo} {titulo}")

print(f"\n  Total: {len(resultados)} checks | {PASS} {passou} aprovados | {FAIL} {falhou} falhos")

if falhou == 0:
    print("\n  *** TODOS OS TESTES PASSARAM -- MVP PRONTO PARA USO! ***")
else:
    print(f"\n  ATENCAO: {falhou} ITEM(NS) PRECISAM DE ATENCAO")

print()
