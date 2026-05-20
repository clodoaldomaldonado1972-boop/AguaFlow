---
title: Investigação — Revisão do log 2026-05-14 (botão fixo + heartbeat pre-login)
status: executado
investigador: skill investigador
date: 2026-05-14
---

## Resumo executivo

- Problema (X): Dois bugs independentes confirmados no log de 2026-05-14 07:07: (1) botão de login ainda renderiza com spinner "CARREGANDO SISTEMA..." no primeiro frame; (2) heartbeat lança `TypeError` silencioso antes de qualquer login porque `page.user_data` é `None` por padrão.
- Solução alvo (Y): (1) Aplicar o plano atômico de `docs/investigacao_botao_login_carregando_fixo_20260508.md` em `views/auth.py:99-110`; (2) adicionar `page.user_data = {}` em `main.py` antes de `asyncio.create_task(heartbeat())`.
- Confiança: alta

## Contexto

- Sintoma 1: Tela de login abre com o botão exibindo ProgressRing + "CARREGANDO SISTEMA..." desde o primeiro render — antes de qualquer interação do usuário.
- Sintoma 2: Exatamente 20s após o boot (antes de qualquer login), o log registra `💓 Heartbeat: erro transitório na sessão …, aguardando para tentar novamente.` O heartbeat continua (fix de `continue` aplicado), mas a causa raiz do erro não foi endereçada.
- Ambiente: Windows 11, Flet desktop, Python 3.14.4, Supabase online, usuário `clodoaldomaldonado112@gmail.com`.
- Reprodução mínima: (1) Abrir o app → botão já exibe spinner. (2) Aguardar 20s sem fazer login → mensagem de erro transitório no log.

## Evidências

- Trechos de log (literal):
  ```
  2026-05-14 07:07:06,056 [DEBUG] flet_transport: send_message: ClientMessage(action=PATCH_CONTROL …
    ProgressRing(_i=12, …, visible=True, …)
    Text(_i=13, …, value='CARREGANDO SISTEMA...', …)
    ElevatedButton(_i=15, …, on_click=<realizar_login>, …)
  ```
  Confirmação do bug 1: conteúdo de loading enviado ao cliente no primeiro PATCH_CONTROL (07:07:06,056), antes de qualquer clique.

  ```
  2026-05-14 07:07:26,071 [DEBUG] __main__: 💓 Heartbeat: erro transitório na sessão 1818300149984, aguardando para tentar novamente.
  ```
  Confirmação do bug 2: heartbeat falhou às 07:07:26 (start = 07:07:06, delta = 20s — primeiro tick). Nenhum login ocorreu ainda, `page.user_data` ainda era `None`.

- Arquivos já inspecionados:
  - `aguaflow_debug.log` — linhas 1–289 (sessão completa 07:07:02–07:08:02)
  - `views/auth.py:49-110` — `btn_entrar` criado com `content=ft.Row([progress_ring_login, text_loading_login])` — fix ainda não aplicado
  - `main.py:101-115` — `page.user_data["heartbeat"] = True` sem inicialização prévia de `page.user_data`
  - `docs/investigacao_botao_login_carregando_fixo_20260508.md` — spec existente, status `pronto_para_execução`
  - `docs/investigacao_session_id_sync_log_20260508.md` — status `executado`
  - `docs/investigacao_heartbeat_nome_login_20260508.md` — status `executado`
  - `docs/investigacao_nome_vazio_menu_fallback_20260508.md` — status `executado`
  - `docs/investigacao_login_blank_page_20260508.md` — status `pronto_para_execução` (ícones `ft.icons.*` removidos nas views; verificado via grep — nenhuma ocorrência ativa restante)

## Causa raiz (hipótese consolidada)

### Bug 1 — Botão de login fixo em loading (views/auth.py:99-110)
O `ElevatedButton` `btn_entrar` é criado com `content=ft.Row([progress_ring_login, text_loading_login])` como conteúdo permanente. A função `realizar_login` nunca altera `btn_entrar.content`, então o botão jamais exibe um label de ação como "ENTRAR". Spec de correção detalhada já existe em `docs/investigacao_botao_login_carregando_fixo_20260508.md` — não executada ainda.

### Bug 2 — page.user_data None antes do login (main.py:107)
O Flet inicializa `page.user_data` como `None`. O heartbeat executa `page.user_data["heartbeat"] = True` sem verificar nem inicializar o atributo. O primeiro tick (20s após o boot) sempre ocorre antes do login, então `None["heartbeat"]` lança `TypeError`. O bloco `except Exception` captura e `continue` mantém o loop vivo — comportamento correto, mas o erro é evitável. Após o login, `page.user_data` é um dict e o acesso funciona.

## Escopo da correção (atômico)

- Incluir:
  - `views/auth.py:49-52, 99-110` — aplicar exatamente o plano da spec `investigacao_botao_login_carregando_fixo_20260508.md` (conteúdo inicial "ENTRAR", troca para loading no clique, restauração no erro).
  - `main.py` — adicionar `page.user_data = {}` imediatamente antes da linha `asyncio.create_task(heartbeat())`.
- Excluir explicitamente: refatoração do heartbeat, alteração da lógica de autenticação Supabase, mudança de schema, outras views, lógica offline.

## Plano de execução (ordem fixa)

### Parte A — Botão de login (views/auth.py)

1. **`views/auth.py:49-52`** — substituir as variáveis auxiliares por dois objetos nomeados:
   ```python
   _content_loading = ft.Row(
       [ft.ProgressRing(width=16, height=16, stroke_width=2, color="white"),
        ft.Text("AGUARDE...", size=14)],
       alignment=ft.MainAxisAlignment.CENTER, spacing=10, tight=True
   )
   _content_normal = ft.Text("ENTRAR", size=14)
   ```

2. **`views/auth.py:99-110`** — trocar `content` inicial do `btn_entrar`:
   ```python
   btn_entrar = ft.ElevatedButton(
       content=_content_normal,
       on_click=realizar_login,
       width=320,
       height=50,
   )
   ```

3. **`views/auth.py`** — primeira linha de `realizar_login` (antes de qualquer await):
   ```python
   btn_entrar.content = _content_loading
   btn_entrar.disabled = True
   page.update()
   ```

4. **`views/auth.py`** — em cada ponto de saída por erro (`lbl_erro.value = ...`), antes do `page.update()` já existente:
   ```python
   btn_entrar.content = _content_normal
   btn_entrar.disabled = False
   ```
   (inclui o bloco `except Exception as ex:` externo em auth.py:93)

### Parte B — Inicialização de page.user_data (main.py)

5. **`main.py`** — localizar a linha `asyncio.create_task(heartbeat())` e adicionar imediatamente antes:
   ```python
   page.user_data = {}
   asyncio.create_task(heartbeat())
   ```

## Verificação

- Como validar que o problema sumiu:
  - **Bug 1**: ao abrir o app, o botão exibe "ENTRAR". Ao clicar, exibe spinner + "AGUARDE...". Em caso de credenciais erradas, volta a "ENTRAR". Login bem-sucedido navega para /menu.
  - **Bug 2**: no log, a mensagem `💓 Heartbeat: erro transitório na sessão…` não deve mais aparecer antes do login — o heartbeat passa a escrever em `{}` sem exceção desde o primeiro tick.
- Regressões a checar:
  - Login online (Supabase HTTP 200) continua redirecionando para /menu.
  - Login offline (SQLite fallback) continua populando `user_data` corretamente.
  - Mensagem de erro visível após falha de credenciais.
  - Logout limpa `page.user_data = {}` — o campo já é dict antes, não muda comportamento.
  - Heartbeat continua rodando normalmente após o login.

## Convenções do projeto

- Camadas tocadas: `views/` (auth.py), `main.py`
- Impacto em docs (`docs/`, AGENTS.md): não

## Riscos e lacunas

- O label "AGUARDE..." pode ser substituído por "CARREGANDO..." se preferido — o ponto crítico é NÃO ser o label inicial.
- `page.user_data = {}` no boot sobrescreve qualquer dado que eventualmente já estivesse lá; como é o primeiro statement após a criação da página, não há risco de perda.
- O campo `full_name` ainda não está preenchido no Supabase para este usuário — a saudação continuará exibindo `"Clodoaldomaldonado112"` (fallback do email). Isso é comportamento documentado e aceitável; preencher `full_name` no painel Supabase é ação do operador, fora do escopo de código.
