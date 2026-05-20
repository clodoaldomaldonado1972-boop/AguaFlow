---
title: Investigação — Tela em branco em /medicao após fix do AppBar
status: corrigido
investigador: skill investigador
date: 2026-05-14
---

## Resumo executivo

- Problema (X): Após mover o AppBar para `appbar=` e adicionar `scroll=ft.ScrollMode.ADAPTIVE` ao Column interno do `/medicao`, o conteúdo do formulário ficava invisível (tela em branco) — apenas o AppBar aparecia.
- Solução alvo (Y): Remover `expand=True` do Column em `views/medicao.py`. Com `scroll` e `expand=True` juntos num Column filho de View.appbar, o Flet 0.84.0 produz layout com altura=0 para o body.
- Confiança: alta

## Contexto

- Sintoma: Usuário vai a /medicao, vê AppBar mas formulário em branco; minimiza após ~13s sem clicar voltar.
- Ambiente: Windows 11, Flet 0.84.0, desktop 1264×681.
- Reprodução mínima: Login → /medicao → conteúdo invisível → não há como gravar nem voltar.

## Evidências

- Log sessão 6 (antes do fix): `AppBar(164).did_mount()` na linha 2601 — ANTES do `Column(169)` (linha 2604). Indica AppBar em `controls[]` (primeiro elemento monta primeiro).
- Log sessão 7 (após fix): `Column(169).did_mount()` na linha 3056 — ANTES do `AppBar(164)` (linha 3167). Indica AppBar em `appbar=` (monta separadamente, depois dos controls). Fix de posição confirmado.
- Usuário minimizou /medicao em ~13s sem clicar nenhum controle → screen was blank, not interactive.
- Todos os controles montaram (Column 169, Container, Stack, Dropdown, TextField×2, Buttons) → conteúdo existe no DOM mas não renderiza visualmente.

## Causa raiz (hipótese consolidada)

`ft.Column(expand=True, scroll=ft.ScrollMode.ADAPTIVE)` como único filho de `ft.View(appbar=...)`:
- `expand=True` pede ao Flutter para envolver o Column em `Expanded()`
- `Expanded` requer um parent `Flex` (Column/Row)
- O body do Scaffold (usado internamente por `appbar=`) pode não fornecer o contexto Flex necessário em Flet 0.84.0
- Resultado: Column com height=0, conteúdo invisível

Na configuração anterior (AppBar em controls[], scroll na View), `expand=True` no Column interno ficava dentro de um `SingleChildScrollView` onde `Expanded` também seria inválido — mas como o Column era o SEGUNDO item num controls-Column, ele ficava dentro de um Flex pai e funcionava.

## Escopo da correção (atômico)

- Incluir: remover `expand=True` de `views/medicao.py` linha 392 do Column com scroll.
- Excluir explicitamente: outros arquivos, lógica de negócio, OCR, styles.

## Plano de execução (ordem fixa)

1. `views/medicao.py` — remover `expand=True` do Column principal. ✅ FEITO

## Verificação

- Como validar: Login → /medicao → formulário visível (Dropdown + TextFields + botão GRAVAR) → clicar ← → retorna ao /menu.
- Regressões a checar: Scroll do formulário ainda funciona quando conteúdo for longo.

## Convenções do projeto

- Camadas tocadas: views/
- Impacto em docs: não

## Riscos e lacunas

- Outros views que têm `expand=True` + `scroll` (como `dashboard_saude.py`) não foram reportados como quebrados; podem funcionar porque têm mais controles no Column ou o layout se resolve de outra forma.
