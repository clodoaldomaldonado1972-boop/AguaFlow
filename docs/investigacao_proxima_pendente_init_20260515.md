---
title: Investigação — buscar_proxima_pendente silencia NameError na inicialização
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-15
---

## Resumo executivo

- Problema (X): `buscar_proxima_pendente()` é chamada em `montar_tela_medicao()` antes de `txt_unidade` ser definido, causando `NameError` silenciado por `except: pass`; resultado: o Dropdown sempre inicia na unidade `db_lista[0]` ('166') — jamais na próxima pendente real.
- Solução alvo (Y): Extrair a lógica de "primeira pendente" (busca desde índice 0) para uma função separada `buscar_primeira_pendente()` sem dependência de `txt_unidade`, e manter `buscar_proxima_pendente()` apenas para chamadas pós-inicialização (função `avancar()`).
- Confiança: alta

## Contexto

- Sintoma: O Dropdown da tela Medição sempre começa em '166' (primeira unidade) ao entrar na tela, independente de quantas unidades já foram lidas no mês. O usuário precisa navegar manualmente.
- Ambiente: Windows 11, Python 3.14.4, Flet, SQLite local.
- Reprodução mínima: Gravar leitura de pelo menos uma unidade → navegar ao Menu → voltar à Medição → o Dropdown está em '166' em vez da próxima pendente.

## Evidências

- Trechos de log / erro (literal): Nenhum erro visível — o `except: pass` (linha 50–51) engole o `NameError` silenciosamente. Log `aguaflow_debug.log` de 2026-05-15 20:34–20:36 não apresenta nenhuma exceção.
- Arquivos já inspecionados:
  - `views/medicao.py` linhas 30–65 — definição de `buscar_proxima_pendente()` e ponto de chamada
  - `aguaflow_debug.log` — toda a sessão analisada, zero ERRORs ou WARNINGs

## Causa raiz (hipótese consolidada)

Em `views/medicao.py`:

```python
# linha 30 — função definida
def buscar_proxima_pendente():
    try:
        ...
        unidade_atual = txt_unidade.value   # ← referencia txt_unidade
        ...
    except:           # ← bare except captura NameError
        pass
    return None

# linha 61 — chamada ANTES de txt_unidade existir
proxima_pendente = buscar_proxima_pendente()   # → sempre retorna None
initial_unit_value = proxima_pendente if proxima_pendente else db_lista[0]

# linha 73 — txt_unidade só é criado aqui
txt_unidade = ft.Dropdown(value=initial_unit_value, ...)
```

O `bare except: pass` foi introduzido para capturar erros de banco, mas acidentalmente mascara o `NameError` de `txt_unidade` não definido. O `initial_unit_value` cai sempre no fallback `db_lista[0]`.

## Escopo da correção (atômico)

- Incluir:
  1. Criar `buscar_primeira_pendente()` em `views/medicao.py` — lógica idêntica à `buscar_proxima_pendente()` mas com `idx_inicio = 0` (não depende de `txt_unidade`).
  2. Na linha 61, substituir `buscar_proxima_pendente()` por `buscar_primeira_pendente()`.
  3. Tornar o `except` em `buscar_proxima_pendente()` específico: `except (ValueError, AttributeError):` para não engolir outros erros silenciosamente.
- Excluir explicitamente:
  - Não alterar `buscar_proxima_pendente()` usada em `avancar()` — essa chamada é pós-inicialização e funciona corretamente.
  - Não alterar lógica de `last_read_unit_id` (continua como sobreposição de prioridade).

## Plano de execução (ordem fixa)

1. Em `views/medicao.py`, após a linha `state = {"modo": "AGUA", "lidas_no_hall": 0}` (linha 25), adicionar:

```python
def buscar_primeira_pendente():
    """Retorna a primeira unidade da lista que ainda não foi lida no mês atual."""
    try:
        leituras_mes = Database.get_leituras_mes_atual()
        if state["modo"] == "AGUA":
            lidos = {l['unidade_id'] for l in leituras_mes if l.get('leitura_agua') is not None}
        else:
            lidos = {l['unidade_id'] for l in leituras_mes if l.get('leitura_gas') is not None}
        for u in db_lista:
            if u not in lidos:
                return u
    except Exception:
        pass
    return None
```

2. Na linha 61, substituir:
   ```python
   proxima_pendente = buscar_proxima_pendente()
   ```
   por:
   ```python
   proxima_pendente = buscar_primeira_pendente()
   ```

3. Em `buscar_proxima_pendente()`, substituir `except:` por `except (ValueError, AttributeError, NameError):` para manter intenção defensiva sem engolir erros inesperados.

## Verificação

- Como validar que o problema sumiu: Gravar leitura da unidade '166' → navegar ao Menu → voltar à Medição → Dropdown deve iniciar em '165' (segunda unidade pendente).
- Regressões a checar:
  - `avancar()` ainda funciona (avança do dropdown atual para a próxima pendente).
  - `last_read_unit_id` ainda sobrepõe corretamente quando presente em `page.user_data`.
  - Tela inicia corretamente quando NENHUMA unidade foi lida (deve mostrar '166').
  - Tela inicia corretamente quando TODAS as unidades foram lidas (deve mostrar tela de "todas lidas").

## Convenções do projeto

- Camadas tocadas: `views/medicao.py` apenas
- Impacto em docs (`docs/`, AGENTS.md): não

## Riscos e lacunas

- `buscar_proxima_pendente()` interna ao `try` de `montar_tela_medicao` — se o `try` externo (linha 22) também capturar exceções, o comportamento pode mudar; verificar escopo do `try` externo antes de aplicar.
- A nova função `buscar_primeira_pendente()` faz uma query extra ao SQLite na inicialização da tela; impacto de performance é negligenciável dado o volume de dados.
