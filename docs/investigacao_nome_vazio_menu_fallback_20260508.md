---
title: Investigação — Nome vazio no menu após fix de auth (fallback não ativado)
status: executado
investigador: skill investigador
date: 2026-05-08
---

## Resumo executivo

- Problema (X): Após aplicação do fix registrado em `investigacao_heartbeat_nome_login_20260508.md`, o menu ainda exibe `"Olá, !"` quando o usuário logado não tem `full_name` preenchido no Supabase.
- Solução alvo (Y): Substituir `user_data.get("nome", fallback)` por `user_data.get("nome") or fallback` em `views/menu_principal.py:20` para tratar string vazia como falsy.
- Confiança: alta

## Contexto

- Sintoma: AppBar do menu exibe `value='Olá, !'` (nome vazio) após login online bem-sucedido com HTTP/2 200 OK às 21:52:53.
- Ambiente: Windows 11, Flet desktop, Python 3.14.4, Supabase online, usuário `clodoaldomaldonado112@gmail.com`.
- Reprodução mínima: Logar com usuário que não tem `full_name` cadastrado no `user_metadata` do Supabase → abrir menu → saudação exibe `"Olá, !"`.

## Evidências

- Trechos de log (literal):
  ```
  2026-05-08 21:52:53,111 [INFO] httpx: HTTP Request: POST .../auth/v1/token?grant_type=password "HTTP/2 200 OK"
  2026-05-08 21:52:53,130 [DEBUG] __main__: 🛣️ Rota acessada: /menu
  2026-05-08 21:52:53,132 [INFO]  __main__: 🔄 Carregando view: Menu Principal
  Text(_i=30, ..., value='Olá, !', ...)   ← linha 2577 do log
  Text(_i=31, ..., value='clodoaldomaldonado112@gmail.com', ...)
  ```
- Arquivos já inspecionados:
  - `aguaflow_debug.log` linhas 2482–2604 (sessão 21:52:28–21:53:07)
  - `views/auth.py:62-75` — fix anterior aplicado: `full_name` lido e `"nome"` gravado em `page.user_data`
  - `views/menu_principal.py:17-24` — fallback com `.get()` não protege contra string vazia
  - `main.py:100-115` — heartbeat com `continue` aplicado corretamente

## Causa raiz (hipótese consolidada)

O fix anterior em `auth.py` grava `page.user_data = {"email": email, "role": role, "nome": full_name}`, onde `full_name = auth_response.user.user_metadata.get("full_name", "")`. Para usuários sem `full_name` no Supabase, `full_name = ""`.

Em `menu_principal.py:20`:
```python
user_name = user_data.get("nome", user_email.split('@')[0].capitalize())
```
`dict.get(key, default)` só usa o `default` quando a chave está **ausente**. Como `"nome"` existe (com valor `""`), retorna `""`. A interpolação `f"Olá, {user_name}!"` gera `"Olá, !"`.

## Escopo da correção (atômico)

- Incluir: `views/menu_principal.py:20` — trocar `.get("nome", fallback)` por `.get("nome") or fallback`.
- Excluir explicitamente: alteração de schema Supabase, preenchimento retroativo de `full_name`, modificação de `auth.py`, alteração de outras views ou do heartbeat.

## Plano de execução (ordem fixa)

1. **`views/menu_principal.py:19-20`** — substituir:
   ```python
   # antes
   user_name = user_data.get(
       "nome", user_email.split('@')[0].capitalize())
   ```
   por:
   ```python
   # depois
   user_name = user_data.get("nome") or user_email.split('@')[0].capitalize()
   ```
2. Salvar e reiniciar o app.
3. Fazer login online com o mesmo usuário e verificar que o AppBar exibe `"Olá, Clodoaldomaldonado112!"` (fallback do email) ou o nome real se `full_name` estiver preenchido no Supabase.

## Verificação

- Como validar que o problema sumiu: AppBar do menu não exibe mais `"Olá, !"` — exibe nome real ou fallback baseado no email, nunca string vazia.
- Regressões a checar:
  - Login offline (SQLite) continua populando `nome` corretamente (não é tocado).
  - Usuários com `full_name` preenchido no Supabase continuam vendo o nome real.
  - `validar_sessao` e demais views não são afetadas.

## Convenções do projeto

- Camadas tocadas: `views/` (menu_principal.py)
- Impacto em docs (`docs/`, AGENTS.md): não

## Riscos e lacunas

- Nenhum usuário perderá dados; a mudança é puramente visual.
- O fallback `email.split('@')[0].capitalize()` gera `"Clodoaldomaldonado112"` — funcional mas não ideal. Se o `full_name` estiver em branco no Supabase, o correto seria preencher esse campo no painel do Supabase; isso está fora deste escopo.
- Se futuramente `user_data` não tiver a chave `"email"`, `user_email` seria `"Usuário Desconhecido"` e o split geraria `"Usuário desconhecido"` — comportamento aceitável.
