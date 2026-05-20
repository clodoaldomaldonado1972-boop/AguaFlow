---
title: Investigação — Login redireciona para página em branco
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-08
---

## Resumo executivo

- Problema (X): Ao fazer login com sucesso no Supabase, o usuário é redirecionado para `/menu` mas vê uma página escura sem conteúdo (erro em branco) e o app trava.
- Solução alvo (Y): Substituir **todos** os usos de `ft.icons.ATRIBUTO` por strings de ícone Material (ex: `"logout"`) em todas as views, pois `flet.controls.material.icons` não possui esses atributos na versão instalada.
- Confiança: **alta** — causa confirmada pelo log de produção com stack trace explícito.

## Contexto

- Sintoma: Login realizado com sucesso (HTTP 200 do Supabase). Rota `/menu` acionada. Página aparece sem AppBar, sem botões — apenas fundo escuro. App encerra conexão ~5 segundos depois.
- Ambiente: Windows 11, app desktop Flet, Python 3.14.4, supabase-py 2.29.0.
- Reprodução mínima: Abrir o app → digitar credenciais válidas → clicar no botão de login → observar página sem conteúdo no lugar do menu.

## Evidências

- Trecho de log literal (aguaflow_debug.log, sessão 2026-05-06 21:14):
  ```
  [DEBUG] flet_controls: Trigger event Page.on_route_change route='/menu'
  [INFO]  __main__: 🔄 Carregando view: Menu Principal
  [DEBUG] flet_transport: send_message: PATCH_CONTROL
    controls='/menu',
    route=[Text(value="Erro ao carregar menu principal: module
      'flet.controls.material.icons' has no attribute 'LOGOUT'", color='red')]
  [DEBUG] flet_controls: Receive loop exiting.   ← app encerra 5s depois
  ```
- Arquivos inspecionados:
  - `views/menu_principal.py` — `ft.icons.LOGOUT` era usado no `IconButton` de logout; **já corrigido** no commit 362af88 (`"power_settings_new"`).
  - `views/autenticacao.py:67` — `ft.icons.PERSON_ADD` (rota `/registro`) — **ainda presente**.
  - `views/recuperar_senha_email.py:9,48` — `ft.icons.EMAIL`, `ft.icons.MARK_EMAIL_READ` — **ainda presentes**.
  - `views/sobre_view.py:26` — `ft.icons.INFO_OUTLINE` — **ainda presente**.
  - `database/sync_service.py` — erro secundário: `no such table: sync_log` (não bloqueia o login).

## Causa raiz (hipótese consolidada)

A versão do Flet instalada (`flet.controls.material.icons`) não exporta os atributos de ícone como constantes de módulo (`ft.icons.LOGOUT`, `ft.icons.PERSON_ADD`, etc.). Ao montar a view `/menu`, `montar_menu` tentava usar `ft.icons.LOGOUT`, lançando `AttributeError`. O bloco `except Exception as e` em `montar_menu` capturou o erro e retornou `ft.View("/menu", [ft.Text("Erro ao carregar...", color="red")])` — uma view sem AppBar nem controles de navegação. Isso parece "página em branco" para o usuário. O loop de Flet encerrou ~5 s depois (desconexão do WebSocket).

O commit 362af88 já corrigiu o ícone de logout em `menu_principal.py`. Restam quatro ocorrências idênticas em outras views que causarão o mesmo sintoma se o usuário navegar para `/registro`, `/esqueci_senha`/`/recuperar-email` ou `/sobre`.

## Escopo da correção (atômico)

- **Incluir**: substituir os 4 usos restantes de `ft.icons.*` por strings equivalentes (Material Symbols snake_case) nas views listadas abaixo.
- **Excluir explicitamente**: não tocar em `menu_principal.py` (já corrigido), não alterar lógica de autenticação, não criar nova camada de abstração para ícones.

| Arquivo | Linha | Atributo atual | String substituta |
|---|---|---|---|
| `views/autenticacao.py` | 67 | `ft.icons.PERSON_ADD` | `"person_add"` |
| `views/recuperar_senha_email.py` | 9 | `ft.icons.EMAIL` | `"email"` |
| `views/recuperar_senha_email.py` | 48 | `ft.icons.MARK_EMAIL_READ` | `"mark_email_read"` |
| `views/sobre_view.py` | 26 | `ft.icons.INFO_OUTLINE` | `"info_outline"` |

## Plano de execução (ordem fixa)

1. Em `views/autenticacao.py:67`, trocar `ft.Icon(ft.icons.PERSON_ADD, ...)` por `ft.Icon("person_add", ...)`.
2. Em `views/recuperar_senha_email.py:9`, trocar `ft.icons.EMAIL` por `"email"` no argumento `st.campo_estilo(...)`.
3. Em `views/recuperar_senha_email.py:48`, trocar `ft.Icon(ft.icons.MARK_EMAIL_READ, ...)` por `ft.Icon("mark_email_read", ...)`.
4. Em `views/sobre_view.py:26`, trocar `ft.Icon(ft.icons.INFO_OUTLINE, ...)` por `ft.Icon("info_outline", ...)`.
5. (Opcional, baixa prioridade) Criar tabela `sync_log` no `Database.inicializar_tabelas()` ou remover a chamada de limpeza em `sync_service.py` para eliminar o erro de log `no such table: sync_log`.

## Verificação

- Como validar que o problema sumiu: iniciar o app → fazer login → o menu deve aparecer com AppBar, botões e ícone de logout visíveis; navegar para `/registro` e `/sobre` e confirmar que não há erro vermelho.
- Regressões a checar: logout, navegação de volta ao menu após cada sub-tela corrigida.

## Convenções do projeto

- Camadas tocadas: `views/` apenas.
- Impacto em docs (`docs/`, AGENTS.md): não — correção puramente de ícone, sem mudança de interface ou contrato público.

## Riscos e lacunas

- Incógnita: nem todos os ícones Material Symbols têm correspondência 1-to-1 em string snake_case com a versão exata do Flet instalada. Se algum ícone não for encontrado, o Flet renderiza um ícone de fallback em vez de lançar exceção — o risco é apenas visual, não um crash.
- O erro `no such table: sync_log` ocorre no boot e é não-bloqueante; está fora do escopo principal desta spec.
