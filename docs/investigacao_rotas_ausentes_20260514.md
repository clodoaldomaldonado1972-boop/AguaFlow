---
title: Investigação — Rotas /dashboard_saude e /recuperar-email ausentes no route_change
status: executado
investigador: skill investigador
date: 2026-05-14
---

## Resumo executivo

- Problema (X): Dois destinos de navegação existentes no app (`/dashboard_saude` e `/recuperar-email`) não estão registrados no `route_change` de `main.py`. Ao navegar para eles, o handler cai no `else: page.go("/")` e o usuário é redirecionado silenciosamente para a tela de login — aparência de "tela em branco" ou "sessão perdida".
- Solução alvo (Y): Adicionar dois `elif` em `main.py:route_change` — um para `/dashboard_saude` chamando `montar_tela_saude(page, ao_voltar=lambda: page.go("/menu"))` e outro para `/recuperar-email` chamando `criar_tela_recuperacao(page)`.
- Confiança: alta

## Contexto

- Sintoma 1: Usuário admin clica "Dashboard de Saúde" no menu → tela muda inesperadamente para login em vez de abrir o dashboard. Nenhuma mensagem de erro visível.
- Sintoma 2: Usuário clica "Enviar Instruções" na tela "Esqueci minha senha" → tela volta para login em vez de abrir a tela de recuperação de senha por e-mail.
- Ambiente: Windows 11, Flet desktop, Python 3.14.4.
- Reprodução mínima: (1) Logar como admin → menu → clicar "Dashboard de Saúde" → observar redirect para login. (2) Tela de login → "Esqueci minha senha" → "Enviar Instruções" → observar redirect para login.

## Evidências

- Log `aguaflow_debug.log` 2026-05-14: nenhuma navegação para `/dashboard_saude` ou `/recuperar-email` registrada nas sessões presentes. O bug não apareceu neste log porque o usuário não clicou nesses botões — mas o código confirma o problema.
- `main.py:39–72` (route_change) — rotas registradas:
  ```
  /   /registro   /esqueci_senha   /menu   /medicao   /scanner
  /sincronizar   /relatorios   /usuarios   /configuracoes   /sobre
  ```
  Ausentes: `/dashboard_saude`, `/recuperar-email`.
- `views/menu_principal.py:107` — botão admin navega para `/dashboard_saude`:
  ```python
  ft.ElevatedButton("Dashboard de Saúde", ..., on_click=lambda _: page.go("/dashboard_saude"), ...)
  ```
- `views/auth.py:30` — botão da tela esqueci_senha navega para `/recuperar-email`:
  ```python
  on_click=lambda _: page.go("/recuperar-email")
  ```
- `main.py:78–81` — `else` do route_change:
  ```python
  else:
      page.go("/")
      logger.warning(f"⚠️ Rota não encontrada: {page.route}. Redirecionando para /.")
  ```
- `views/dashboard_saude.py:14` — assinatura da função: `montar_tela_saude(page, ao_voltar)` — requer callback de retorno.
- `views/recuperar_senha_email.py:8` — assinatura: `criar_tela_recuperacao(page)` — sem parâmetros extras.

## Causa raiz (hipótese consolidada)

As duas rotas foram implementadas nas suas views mas nunca adicionadas ao router em `main.py`. O `route_change` cobre apenas as rotas do MVP original; `/dashboard_saude` e `/recuperar-email` foram criados depois sem o correspondente registro. Quando o Flet dispara o `on_route_change` para essas rotas, `nova_view` permanece `None`, ativando o `else: page.go("/")`. Como `page.views.clear()` não foi chamado antes, o estado de views pode oscilar — mas o resultado visível é o usuário voltando para a tela de login sem explicação.

## Escopo da correção (atômico)

- Incluir:
  - `main.py` — dois `elif` adicionados na função `route_change`, imediatamente antes do bloco `elif page.route == "/sobre":` (mantendo a ordem lógica).
- Excluir explicitamente: alteração nas views `dashboard_saude.py` e `recuperar_senha_email.py`, refatoração do route_change, mudança na assinatura das funções, outras rotas.

## Plano de execução (ordem fixa)

1. **`main.py`** — Localizar o bloco:
   ```python
   elif page.route == "/configuracoes":
       from views.configuracoes import montar_tela_configs
       nova_view = montar_tela_configs(page)
   elif page.route == "/sobre":
   ```
   Inserir entre `/configuracoes` e `/sobre`:
   ```python
   elif page.route == "/dashboard_saude":
       from views.dashboard_saude import montar_tela_saude
       nova_view = montar_tela_saude(page, ao_voltar=lambda: page.go("/menu"))
   elif page.route == "/recuperar-email":
       from views.recuperar_senha_email import criar_tela_recuperacao
       nova_view = criar_tela_recuperacao(page)
   ```

## Verificação

- Como validar que o problema sumiu:
  - Login como admin → menu → clicar "Dashboard de Saúde" → tela do dashboard abre (não redireciona para login).
  - Tela login → "Esqueci minha senha" → preencher e-mail → "Enviar Instruções" → tela de recuperação abre ou exibe status de envio.
  - No log: não deve aparecer `⚠️ Rota não encontrada: /dashboard_saude` nem `/recuperar-email`.
- Regressões a checar:
  - Todas as outras rotas continuam funcionando normalmente.
  - `ao_voltar` callback do dashboard_saude retorna para o menu corretamente.
  - `validar_sessao` dentro de `montar_tela_saude` protege a rota contra acesso sem login.

## Convenções do projeto

- Camadas tocadas: `main.py` (roteamento) — apenas.
- Impacto em docs (`docs/`, AGENTS.md): não

## Riscos e lacunas

- `montar_tela_saude(page, ao_voltar)` usa um callback `ao_voltar` — o lambda `lambda: page.go("/menu")` é a forma correta de fornecer esse callback no contexto do router.
- Se `criar_tela_recuperacao(page)` tiver qualquer `ft.icons.*` residual, pode gerar erro visual (não crítico — o grep já confirmou que nenhum `ft.icons.*` está ativo nas views).
- `/dashboard_saude` tem `validar_sessao` interno — se chamado sem sessão válida, redireciona para login corretamente (comportamento esperado).
