---
title: Investigação — Heartbeat encerra permanentemente + nome ausente no login online
status: executado
investigador: skill investigador
date: 2026-05-08
---

## Resumo executivo

- Problema (X): Dois bugs distintos revelados no log de 21:39:06 — (1) o heartbeat quebra permanentemente após o primeiro erro transitório; (2) o login online via Supabase não popula `nome` em `user_data`, exibindo email bruto como saudação.
- Solução alvo (Y): (1) Substituir `break` por `continue` (com `asyncio.sleep` curto) no handler de heartbeat; (2) ler `user_metadata.get("full_name")` na resposta Supabase e incluir `"nome"` em `page.user_data`.
- Confiança: alta

## Contexto

- Sintoma 1: Log linha 2128 — `💓 Heartbeat falhou para sessão 1762066378976 (provável desconexão).` registrado às 21:39:26,495, exatamente 20s após o boot. Sessão continuou funcional; login foi bem-sucedido 8s depois (21:39:34). Heartbeat morreu permanentemente sem necessidade.
- Sintoma 2: AppBar do menu (linha 2301) exibe `Olá, Clodoaldomaldonado112!` — parte local do e-mail capitalizada — porque `user_data["nome"]` estava ausente após login online.
- Ambiente: Windows 11, Flet desktop, Python 3.14.4, Supabase online.
- Reprodução mínima: Iniciar app → fazer login online → abrir menu: saudação usa email bruto. Para o heartbeat: qualquer sessão com duração > 20s sofre a falha (basta o primeiro `page.update()` do heartbeat lançar exceção durante boot/carga).

## Evidências

- Trechos de log relevantes:
  ```
  2026-05-08 21:39:06,485  [INFO]  __main__: ⚙️ Iniciando boot do banco de dados e sincronia...
  2026-05-08 21:39:26,495  [DEBUG] __main__: 💓 Heartbeat falhou para sessão 1762066378976 (provável desconexão).
  2026-05-08 21:39:34,289  [DEBUG] flet_transport: _on_message: ClientAction.CONTROL_EVENT {'target': 15, 'name': 'click', ...}
  2026-05-08 21:39:36,107  [INFO]  httpx: HTTP Request: POST .../auth/v1/token?grant_type=password "HTTP/2 200 OK"
  2026-05-08 21:39:36,127  [DEBUG] __main__: 🛣️ Rota acessada: /menu
  Text value='Olá, Clodoaldomaldonado112!'  (linha 2301 do log)
  ```
- Arquivos inspecionados: `main.py:101-114`, `views/auth.py:59-94`, `views/menu_principal.py:6-24`, `aguaflow_debug.log:2046-2324`.

## Causa raiz (hipótese consolidada)

### Bug 1 — Heartbeat (main.py:101-114)
O loop `heartbeat()` usa `break` no bloco `except`, terminando a corrotina ao primeiro erro. O primeiro tick acontece 20s após o boot (ainda durante a inicialização assíncrona do banco/sync), quando `page.update()` pode falhar por contenção ou estado inconsistente transitório. A corrotina morre e nunca mais roda — a sessão perde o keep-alive para o resto da sua vida.

### Bug 2 — Nome ausente no login online (views/auth.py:69)
O path de login online popula `page.user_data` apenas com `{"email": email, "role": role}` — `"nome"` não é lido de `auth_response.user.user_metadata`. O path offline (SQLite) lê `nome` corretamente do banco local. Logo, qualquer usuário que faça login online verá o email bruto no lugar do nome.

## Escopo da correção (atômico)

- Incluir:
  - `main.py:109-112`: substituir `break` por `continue` com `await asyncio.sleep(5)` antes para evitar busy-loop em falha persistente.
  - `views/auth.py:67-69`: ler `full_name = auth_response.user.user_metadata.get("full_name", "")` e incluir `"nome": full_name` em `page.user_data`.
- Excluir explicitamente: refatoração do sistema de heartbeat, mudança de provider de autenticação, alteração do schema Supabase, modificação de outras views.

## Plano de execução (ordem fixa)

1. **`main.py:109-112`** — No bloco `except` do heartbeat, trocar `break` por `continue` com sleep curto:
   ```python
   except Exception:
       logger.debug(
           f"💓 Heartbeat: erro transitório na sessão {id(page)}, aguardando para tentar novamente.")
       await asyncio.sleep(5)
       continue
   ```
2. **`views/auth.py:67-69`** — Após obter `role`, ler também `full_name` e incluir em `user_data`:
   ```python
   role = auth_response.user.user_metadata.get("role", "user")
   full_name = auth_response.user.user_metadata.get("full_name", "")
   page.user_data = {"email": email, "role": role, "nome": full_name}
   ```
3. Testar: iniciar app → login online → verificar saudação no menu. Deixar sessão aberta > 25s e confirmar que não aparecem mais logs de heartbeat morto.

## Verificação

- Como validar que o problema sumiu:
  - **Heartbeat**: no log, após 21:39:26, devem aparecer entradas de heartbeat a cada ~20s sem o texto "Heartbeat falhou" sendo seguido de silêncio — deve continuar tentando.
  - **Nome**: AppBar exibe nome real (ex. "Clodoaldo Maldonado") se cadastrado no Supabase, ou string vazia/fallback aceitável se `full_name` não estiver preenchido.
- Regressões a checar: login offline continua populando `nome` via SQLite (não é tocado); logout limpa `user_data` corretamente; `validar_sessao` em outras views não é afetada.

## Convenções do projeto

- Camadas tocadas: `main.py` (heartbeat), `views/` (auth.py — login)
- Impacto em docs (`docs/`, AGENTS.md): não

## Riscos e lacunas

- O campo `full_name` pode não estar preenchido no Supabase para usuários existentes (cadastrados antes da alteração ou sem `full_name` em `user_metadata`). Nesse caso o fallback `email.split('@')[0].capitalize()` em `menu_principal.py:20` ainda será usado — comportamento aceitável, sem crash.
- Se o heartbeat continuar falhando indefinidamente (ex.: sessão realmente morta), o loop vai rodar em ciclos de 20+5s indefinidamente. Isso é seguro pois `page.update()` lançará exceção continuamente — não há risco de consumo excessivo. Uma melhoria futura (fora deste escopo) seria adicionar contador de falhas consecutivas para encerrar após N tentativas.
