---
title: Investigação — page.open() inexistente no Flet 0.82.2
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-20
---

## Resumo executivo

- Problema (X): `page.open()` é chamado em 51 pontos de 10 arquivos, mas o método não existe no Flet 0.82.2 — resulta em `AttributeError` silencioso que aborta a ação do usuário sem feedback visual.
- Solução alvo (Y): Substituir mecanicamente `page.open(` → `page.show_dialog(` e `self.page.open(` → `self.page.show_dialog(` nos 10 arquivos afetados; nenhuma outra mudança.
- Confiança: alta

## Contexto

- Sintoma: Ao salvar uma leitura na tela `/medicao` (unidade 121), quando o sistema tenta abrir o diálogo "Hall Concluído — Gás?", a callback do `Future` lança `AttributeError` e aborta silenciosamente. O usuário não vê o diálogo e fica preso sem avançar ou receber feedback.
- Ambiente: Windows 11, Flet 0.82.2 (`.venv`), Python 3.14, desktop.
- Reprodução mínima: Entrar em `/medicao`, atingir o fim de um hall (última unidade de um andar) e clicar em **Salvar** → erro ocorre em `abrir_dialogo_gas()`.

## Evidências

- Trechos de log (literal):
  ```
  2026-05-20 08:52:39,409 [ERROR] concurrent.futures: exception calling callback for <Future ... raised AttributeError>
  File "C:\AguaFlow\views\medicao.py", line 279, in abrir_dialogo_gas
      page.open(ft.AlertDialog(
      ^^^^^^^^^
  AttributeError: 'Page' object has no attribute 'open'
  ```
  Mesmo erro repetido em 08:52:47, 08:52:59, 08:53:28, 08:53:47, 08:53:53 — 6 ocorrências no log, sempre no mesmo ponto.
- Arquivos já inspecionados: `views/medicao.py` (linhas 279, 298, 303, 318, 333 e 191), `aguaflow_debug.log` (completo, 3555 linhas).
- Confirmação da API correta: `ft.Page.show_dialog` existe e aceita `DialogControl` (AlertDialog e SnackBar herdam `DialogControl` no 0.82.2). Assinatura: `page.show_dialog(dialog: DialogControl) -> None` — adiciona ao stack interno e chama `_dialogs.update()` sem necessitar de `page.update()` extra.
- 51 ocorrências de `page.open(` em 10 arquivos; 0 ocorrências de `page.show_dialog(` — migração anterior (`8a505b7`) introduziu `page.open()` assumindo erroneamente ser a API do Flet 0.82 (a API correta é `page.show_dialog()`).

## Causa raiz (hipótese consolidada)

O commit `8a505b7` ("migra API de dialogs/snackbar para Flet 0.82") migrou o padrão antigo (`page.dialog = ...; page.update()`) para `page.open()`, que era a API do Flet 0.21–0.24. No Flet 0.82 (arquitetura nova, `flet.controls.*`), o método foi renomeado para `page.show_dialog()`. O `page.open` simplesmente não existe no objeto `Page` desta versão.

## Escopo da correção (atômico)

- Incluir: substituição de `page.open(` → `page.show_dialog(` e `self.page.open(` → `self.page.show_dialog(` nos 10 arquivos listados abaixo. Apenas essa string — nada mais.
- Excluir explicitamente: alterar `page.update()` chamadas vizinhas (são inofensivas e podem servir a outros controles na mesma função), refatorar lógica de dialogs, tocar em `page.close()` ou `page.pop_dialog()` (não ocorrem no repo), alterar testes ou AGENTS.md.

## Plano de execução (ordem fixa)

1. Em cada arquivo abaixo, executar substituição global de `page.open(` → `page.show_dialog(` (replace_all):
   - `views/medicao.py` — 7 ocorrências
   - `views/configuracoes.py` — 12 ocorrências
   - `views/gerenciamento_usuarios.py` — 12 ocorrências
   - `views/historico.py` — 9 ocorrências (inclui `page.close(` se existir — verificar)
   - `views/menu_principal.py` — 4 ocorrências
   - `views/ajuda_view.py` — 2 ocorrências
   - `views/relatorio_view.py` — 1 ocorrência
   - `utils/audio_utils.py` — 1 ocorrência (`page.open(` passado como argumento de função)
   - `views/components/scanner_component.py` — 1 ocorrência (usa `self.page.open(` → `self.page.show_dialog(`)
   - `views/sincronizacao.py` — 2 ocorrências (usa `self.page.open(` → `self.page.show_dialog(`)
2. Confirmar com grep que `page.open(` e `self.page.open(` chegaram a zero no projeto.
3. Rodar a aplicação, navegar até `/medicao`, concluir um hall e confirmar que o diálogo "Hall Concluído — Gás?" aparece corretamente.

## Verificação

- Como validar que o problema sumiu: iniciar app (`python main.py`), fazer login, ir para `/medicao`, atingir última unidade de um andar → diálogo "Hall Concluído — Gás?" deve abrir. SnackBars de validação (valor vazio, unidade anterior não lida) também devem aparecer normalmente.
- Regressões a checar: todas as telas que exibem SnackBar ou AlertDialog — `/configuracoes`, `/gerenciamento_usuarios`, `/historico`, `/menu_principal`, `/ajuda`, `/relatorio`, scanner QR. O comportamento externo de cada diálogo não muda; apenas o método de abertura.

## Convenções do projeto

- Camadas tocadas: views, utils (audio_utils), views/components
- Impacto em docs (`docs/`, AGENTS.md): não — é fix de API puro, sem mudança de contratos ou estrutura de camadas.

## Riscos e lacunas

- `page.update()` chamadas imediatamente após `page.show_dialog()` são redundantes mas inofensivas — não remover para reduzir diff e risco de regressão.
- Se algum `AlertDialog` tiver `on_dismiss` customizado, certificar que o `show_dialog` não conflita (a função envolve o `on_dismiss` em um wrapper interno — comportamento documentado, compatível).
- Verificar `views/historico.py` — 9 ocorrências é o maior número depois de `configuracoes` e `gerenciamento_usuarios`; ler o arquivo antes de aplicar para confirmar que não há padrão diferente (ex.: `page.open(None)` ou variável intermediária).
