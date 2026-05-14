---
title: Investigação — AttributeError page.session_id e sync_log inexistente
status: executado
investigador: skill investigador
date: 2026-05-08
---

## Resumo executivo

- Problema (X): Dois bugs independentes: (1) `page.session_id` não existe no Flet — causa crash no `on_close` e exception não recuperada no `heartbeat`; (2) tabela `sync_log` nunca é criada no boot, causando erro a cada minuto no `processar_fila`.
- Solução alvo (Y): (1) Substituir `page.session_id` por `id(page)` (ou remover onde não agrega) em `main.py:96,107,113`; (2) chamar `await SyncService.init_sync_log_table()` em `inicializar_background()` antes de `processar_fila()` em `main.py:130`.
- Confiança: alta

## Contexto

- Sintoma: App crashava no fechamento com `SESSION_CRASHED`; log de erro `no such table: sync_log` a cada minuto.
- Ambiente: Windows 11, Flet desktop, Python, SQLite local.
- Reprodução mínima: (1) Abrir e fechar o app → crash no `on_close`; (2) Deixar rodando > 1 min com banco vazio → erro de sync_log no console.

## Evidências

- Trechos de log / erro (literal):
  ```
  2026-05-08 21:19:18 [ERROR] database.sync_service: Erro na limpeza de logs: no such table: sync_log
  2026-05-08 21:19:35 [ERROR] asyncio: Task exception was never retrieved
  2026-05-08 21:25:35 [ERROR] flet: Unhandled error in 'on_close' handler
    AttributeError: 'Page' object has no attribute 'session_id'. Did you mean: 'session'?
    File "C:\AguaFlow\main.py", line 96, in handle_close
      logger.info(f"🔌 Sessão {page.session_id} encerrada pelo cliente.")
  ```
- Arquivos já inspecionados: `main.py`, `database/sync_service.py`

## Causa raiz (hipótese consolidada)

**Bug A — `page.session_id` inexistente (3 ocorrências em `main.py`)**

O Flet não expõe `page.session_id`; o atributo correto é `page.session` (SessionStorage). O código usa `page.session_id` em três pontos:
- `main.py:96` — `handle_close` → crash fatal, SESSION_CRASHED enviado ao cliente.
- `main.py:107` — `heartbeat` → `AttributeError` capturado pelo `except`, mas…
- `main.py:113` — dentro do próprio `except`, tenta usar `page.session_id` novamente → segunda `AttributeError` não capturada → "Task exception was never retrieved" (o erro asyncio de 21:19:35, ~20s após boot).

**Bug B — tabela `sync_log` nunca criada**

`SyncService.init_sync_log_table()` existe e faz `CREATE TABLE IF NOT EXISTS sync_log`, mas não é chamada em `inicializar_background()` (`main.py:119-133`). Só é chamada em `test_full_workflow.py:44`. Resultado: `processar_fila()` chama `limpar_logs_antigos()` toda vez que não há pendências, mas a tabela não existe → erro a cada ciclo (~60s).

## Escopo da correção (atômico)

- Incluir:
  - `main.py:96` — substituir `page.session_id` por `id(page)`
  - `main.py:107` — remover o `if page.session_id:` (redundante; o `page.update()` já falha sozinho se desconectado)
  - `main.py:113` — substituir `page.session_id` por `id(page)` (ou string fixa)
  - `main.py:130` — adicionar `await SyncService.init_sync_log_table()` antes de `asyncio.create_task(SyncService.processar_fila())`
- Excluir explicitamente:
  - Não refatorar `SyncService` nem `inicializar_background()` além da linha de init.
  - Não alterar `test_full_workflow.py` (já chama init corretamente).
  - Não mudar schema da tabela `sync_log`.

## Plano de execução (ordem fixa)

1. **`main.py:96`** — alterar:
   ```python
   # de:
   logger.info(f"🔌 Sessão {page.session_id} encerrada pelo cliente.")
   # para:
   logger.info(f"🔌 Sessão {id(page)} encerrada pelo cliente.")
   ```

2. **`main.py:107`** — remover o `if page.session_id:` e dedent o bloco:
   ```python
   # de:
   if page.session_id:
       page.user_data["heartbeat"] = True
       page.update()
   # para:
   page.user_data["heartbeat"] = True
   page.update()
   ```

3. **`main.py:113`** — alterar:
   ```python
   # de:
   logger.debug(f"💓 Heartbeat falhou para {page.session_id} (provável desconexão).")
   # para:
   logger.debug(f"💓 Heartbeat falhou para sessão {id(page)} (provável desconexão).")
   ```

4. **`main.py:130`** — adicionar chamada `init_sync_log_table` antes do task:
   ```python
   # de:
   asyncio.create_task(SyncService.processar_fila())
   # para:
   await SyncService.init_sync_log_table()
   asyncio.create_task(SyncService.processar_fila())
   ```

## Verificação

- Como validar que o problema sumiu:
  - Rodar o app, fechar normalmente → sem SESSION_CRASHED no log.
  - Deixar rodando > 2 min → sem `no such table: sync_log` no log.
  - Sem `asyncio: Task exception was never retrieved` no log.
- Regressões a checar:
  - Fluxo de heartbeat continua funcionando (atualiza `user_data` sem erros).
  - `processar_fila()` ainda registra e limpa logs normalmente.

## Convenções do projeto

- Camadas tocadas: `main.py` (boot/eventos), `database/sync_service.py` (chamada via `await`)
- Impacto em docs (`docs/`, AGENTS.md): não

## Riscos e lacunas

- `page.user_data` pode não existir se a página for desconectada antes do heartbeat atualizar — mas o `except` no heartbeat já trata isso, e com a correção do log (passo 3) não haverá mais exception não recuperada.
- A tabela `sync_log` pode acumular dados indefinidamente se `limpar_logs_antigos()` não for chamada corretamente — mas isso já ocorria antes desta correção; o fix apenas garante que a tabela exista.
