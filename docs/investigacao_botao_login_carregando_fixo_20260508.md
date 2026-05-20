---
title: Investigação — Botão de login hardcoded com "CARREGANDO SISTEMA..." desde o primeiro render
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-08
---

## Resumo executivo

- Problema (X): O botão de login (`btn_entrar` em `views/auth.py:99-110`) é construído com `content=Row([ProgressRing, Text("CARREGANDO SISTEMA...")])` como conteúdo fixo permanente — exibido desde o primeiro paint da tela, nunca substituído por um label de ação como "ENTRAR".
- Solução alvo (Y): Definir o conteúdo inicial do botão como `ft.Text("ENTRAR", size=14)`; trocar para o Row de loading ao início de `realizar_login` e restaurar ao término com erro; navegação em caso de sucesso dispensa restauração.
- Confiança: alta

## Contexto

- Sintoma: Tela de login abre com botão mostrando spinner + "CARREGANDO SISTEMA..." desde o primeiro frame. O botão é clicável (disabled=False) e funciona, mas a UX comunica que o sistema ainda está carregando em vez de convidar o usuário a digitar as credenciais e entrar.
- Ambiente: Windows 11, Flet desktop, Python 3.14.4.
- Reprodução mínima: Iniciar o app → observar a tela de login → botão já exibe "CARREGANDO SISTEMA..." antes de qualquer interação.

## Evidências

- Trechos de log (literal) — Flet PATCH_CONTROL inicial da sessão 22:03:09:
  ```
  Text(_i=13, ..., value='CARREGANDO SISTEMA...', ...)
  ProgressRing(_i=12, ..., visible=True, ...)
  ElevatedButton(_i=15, ..., on_click=<realizar_login>, ...)
  ```
  Esses controles são enviados ao cliente no primeiro render, confirmando que o estado de loading é o inicial permanente.
- Arquivos inspecionados:
  - `aguaflow_debug.log` linhas 2605–2891 (sessão 22:03:09–22:03:49)
  - `views/auth.py:41-149` — lógica do botão e do `realizar_login`

## Causa raiz (hipótese consolidada)

Em `views/auth.py:51-52`:
```python
progress_ring_login = ft.ProgressRing(width=16, height=16, stroke_width=2, color="white")
text_loading_login = ft.Text("CARREGANDO SISTEMA...", size=14)
```
E em `views/auth.py:99-110`:
```python
btn_entrar = ft.ElevatedButton(
    content=ft.Row(
        [progress_ring_login, text_loading_login],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
        tight=True
    ),
    on_click=realizar_login,
    width=320,
    height=50,
    disabled=False
)
```
O Row de loading foi definido como conteúdo permanente do botão. A função `realizar_login` não altera `btn_entrar.content` antes nem depois da requisição — o botão jamais exibe um label de ação como "ENTRAR". O comentário `# disabled=False  # Mantenha False para o botão estar clicável e evitar loops` sugere que versões anteriores desabilitavam o botão durante o boot, e o conteúdo de loading foi preservado por descuido como estado padrão ao invés de estado transitório.

## Escopo da correção (atômico)

- Incluir:
  - `views/auth.py:51-52` — criar variáveis separadas para o content normal e o content de loading.
  - `views/auth.py:99-110` — definir `content` inicial do botão como `ft.Text("ENTRAR", size=14)`.
  - `views/auth.py:54` (início de `realizar_login`) — trocar content para Row de loading + `page.update()`.
  - `views/auth.py:89-96` (blocos `except`/erro) — restaurar content para `ft.Text("ENTRAR", size=14)` + `page.update()`.
- Excluir explicitamente: mudança na lógica de autenticação, alteração do heartbeat, outras views, schema Supabase, lógica de fallback offline.

## Plano de execução (ordem fixa)

1. **`views/auth.py:51-52`** — manter as variáveis auxiliares mas renomear para deixar claro o propósito:
   ```python
   _content_loading = ft.Row(
       [ft.ProgressRing(width=16, height=16, stroke_width=2, color="white"),
        ft.Text("AGUARDE...", size=14)],
       alignment=ft.MainAxisAlignment.CENTER, spacing=10, tight=True
   )
   _content_normal = ft.Text("ENTRAR", size=14)
   ```

2. **`views/auth.py:99-110`** — trocar `content` inicial:
   ```python
   btn_entrar = ft.ElevatedButton(
       content=_content_normal,
       on_click=realizar_login,
       width=320,
       height=50,
   )
   ```

3. **`views/auth.py:54`** — primeira linha de `realizar_login`, antes de qualquer await:
   ```python
   btn_entrar.content = _content_loading
   btn_entrar.disabled = True
   page.update()
   ```

4. **`views/auth.py:89-96`** — em cada ponto de saída por erro (lbl_erro setado), antes de `page.update()`:
   ```python
   btn_entrar.content = _content_normal
   btn_entrar.disabled = False
   ```
   (o `page.update()` que já existe em cada bloco propaga a restauração)

5. Reiniciar o app e confirmar: tela de login abre com botão "ENTRAR" → clique muda para loading → erro restaura "ENTRAR" → login bem-sucedido navega para /menu.

## Verificação

- Como validar que o problema sumiu: ao abrir o app, o botão da tela de login exibe "ENTRAR" (não ProgressRing). Ao clicar e aguardar, exibe spinner. Em caso de credenciais erradas, volta a exibir "ENTRAR".
- Regressões a checar:
  - Login online (Supabase) continua funcionando e redireciona para /menu.
  - Login offline (SQLite fallback) continua funcionando.
  - Mensagem de erro continua visível após falha de credenciais.
  - Sessão de heartbeat não é afetada (camada separada em main.py).

## Convenções do projeto

- Camadas tocadas: `views/` (auth.py — tela de login)
- Impacto em docs (`docs/`, AGENTS.md): não

## Riscos e lacunas

- Se `page.update()` lançar exceção dentro de `realizar_login` (transient Flet error), o botão pode ficar travado em loading. Risco baixo: o try/except externo já captura e exibe mensagem de erro — adicionar restauração do botão no `except Exception as ex` geral (auth.py:93) além dos blocos individuais.
- O label "AGUARDE..." é uma sugestão; pode ser mantido "CARREGANDO SISTEMA..." se preferido — o ponto crítico é que NÃO seja o label inicial.
