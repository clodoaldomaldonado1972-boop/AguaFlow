---
title: Investigação — Login não navega para /menu após autenticação
status: executado
investigador: skill investigador
date: 2026-05-16
---

## Resumo executivo

- Problema (X): Login autentica com sucesso no Supabase (HTTP 200) mas a tela não muda — `push_route("/menu")` cria uma coroutine que nunca é executada.
- Solução alvo (Y): Substituir todas as chamadas `page.push_route(route)` sem `await` por `await page.push_route(route)` em funções async e por `page.go(route)` em lambdas e funções síncronas. Adicionalmente: mover o HTTP síncrono do SyncService para `asyncio.to_thread`.
- Confiança: alta

## Contexto

- Sintoma: Usuário faz login (botão "ENTRAR"), app fica parado na tela de login. Nenhuma mensagem de erro exibida em algumas sessões.
- Ambiente: Windows 11, Python 3.14, Flet 0.82.2, supabase-py 2.29.0, gotrue 2.9.1.
- Reprodução mínima: Abrir o app → digitar credenciais → clicar ENTRAR → tela não muda.

## Evidências

- Log `aguaflow_debug.log` linha 24249: `HTTP Request: POST …/auth/v1/token?grant_type=password "HTTP/2 200 OK"` — autenticação OK.
- Nenhum `send_message: push_route` foi registrado depois desse ponto na sessão 22:27.
- Em sessão anterior (20:16), o login funcionou: linha 233 mostra `push_route: /menu` sendo enviado.
- Diferença entre sessões: em 20:16 o código usava `page.go("/menu")`; em 22:27 já usava `page.push_route("/menu")` (resultado da refatoração global de `page.go` → `page.push_route`).
- `inspect.iscoroutinefunction(ft.Page.push_route)` → `True`.
- Chamada sem `await` cria coroutine que é descartada imediatamente pelo GC.
- Arquivos inspecionados: `views/auth.py`, `main.py`, `database/sync_service.py`, `views/medicao.py`, `views/scanner_view.py`, `utils/auth_utils.py`, `.venv/Lib/site-packages/flet/controls/page.py`.

## Causa raiz (hipótese consolidada)

**Bug 1 (principal — navegação silenciosa):** A refatoração global de `page.go()` → `page.push_route()` gerou chamadas sem `await` em todo o codebase. Em Python, chamar uma `async def` sem `await` apenas cria um objeto coroutine sem executar o corpo. A navegação toda foi silenciada.

**Bug 2 (secundário — UI congelada):** `SyncService._upload_individual` chama `supabase.table().insert().execute()` de forma síncrona dentro de uma `async def`, bloqueando o event loop enquanto cada request HTTP de sincronização ocorre (~200ms × 192 leituras = ~40s de UI congelada na primeira execução após um ciclo completo).

**Bug 3 (terciário — swallow silencioso):** O `except Exception: logger.info(...)` original no login mascarava qualquer exceção pós-autenticação, incluindo `AttributeError` em `user_metadata.get()` se o metadata fosse `None`.

## Escopo da correção (atômico)

- Incluir:
  1. `views/auth.py` — `await page.push_route(...)` nas 2 chamadas em `realizar_login`; `asyncio.to_thread` para o login HTTP; `user_metadata or {}`; logging com `exc_info=True`.
  2. `main.py` — `await page.push_route("/")` no fallback de rota desconhecida; lambdas → `page.go()`.
  3. `utils/auth_utils.py` — 2 chamadas sync → `page.go()`.
  4. `views/autenticacao.py`, `views/medicao.py`, `views/scanner_view.py` — `await page.push_route(route)`.
  5. Todas as lambdas em todos os 14 arquivos afetados → `page.go(route)`.
  6. `database/sync_service.py` — `_upload_individual` wraps o insert em `asyncio.to_thread`.
- Excluir explicitamente: refatoração do sync service além do `to_thread`; mudanças em lógica de negócio; views de relatório/histórico/dashboard.

## Plano de execução (ordem fixa)

1. Corrigir `views/auth.py`: `asyncio.to_thread`, `await push_route`, `user_metadata or {}`, log com `exc_info`.
2. Corrigir `main.py`: `await push_route` no fallback; lambdas → `page.go()`.
3. Corrigir funções async em `autenticacao.py`, `medicao.py`, `scanner_view.py`: adicionar `await`.
4. Corrigir funções sync: `auth_utils.py`, `menu_principal.py`, `configuracoes.py` → `page.go()`.
5. Converter todas as lambdas de todos os arquivos: `page.push_route(` → `page.go(`.
6. Corrigir `sync_service._upload_individual`: wrap em `asyncio.to_thread`.
7. Testar: iniciar app, logar, navegar para /menu, ir para /medicao, scanner, relatórios.

## Verificação

- Como validar que o problema sumiu: iniciar app → logar → tela do menu aparece imediatamente; botões de navegação funcionam; UI não congela durante sync.
- Regressões a checar: logout, navegação por todos os botões do menu, scanner (scanner_view.py:249 usa `await`), criar conta (autenticacao.py:50).

## Convenções do projeto

- Camadas tocadas: views | database | utils | main.py
- Impacto em docs: não — checklist_mvp.md não precisa de atualização para este fix técnico.

## Riscos e lacunas

- `page.go()` é deprecated no Flet 0.82 mas funciona (cria task internamente). Será necessária nova passagem quando o Flet remover `go()`.
- Se alguma lambda estiver em contexto onde o event loop não está ativo (improvável no Flet), `page.go()` pode falhar. Monitorar logs.
- O `asyncio.to_thread` no sync service usa o thread pool do event loop; com 192 requests paralelos pode saturar o pool — mas como o SyncService processa sequencialmente (for loop), na prática apenas 1 thread extra é usado por vez.
