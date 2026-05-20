---
title: Investigação — ft.alignment.center inválido bloqueia tela de login
status: executado
investigador: skill investigador
date: 2026-05-14
---

## Resumo executivo

- Problema (X): A tela de login (`/`) falha ao renderizar com o erro `module 'flet.controls.alignment' has no attribute 'center'`. O app abre com tela vermelha de erro e o usuário não consegue fazer login.
- Solução alvo (Y): Substituir `alignment=ft.alignment.center` por `alignment=ft.alignment.Alignment(0, 0)` no `ft.Container` do logo em `views/auth.py`.
- Confiança: alta

## Contexto

- Sintoma: App abre e exibe `Erro Crítico: module 'flet.controls.alignment' has no attribute 'center'` em texto vermelho. Nenhuma interação é possível.
- Ambiente: Windows 11, Flet 0.84.0, Python 3.14
- Reprodução mínima: Iniciar o app — a tela de login já falha no primeiro render.

## Evidências

- Log literal (08:10:37):
  ```
  value="Erro Crítico: module 'flet.controls.alignment' has no attribute 'center'"
  ```
- Arquivo: `views/auth.py` — `ft.Container(..., alignment=ft.alignment.center)`
- Verificação Python: `dir(ft.alignment)` não contém `center`; a forma correta é `ft.alignment.Alignment(x=0, y=0)`.

## Causa raiz

No Flet 0.84.0 o módulo `flet.controls.alignment` não expõe aliases como `.center`, `.top_left`, etc. A API correta para alinhar ao centro é `ft.alignment.Alignment(0, 0)` (x=0, y=0).

## Escopo da correção (atômico)

- Incluir: `views/auth.py` — uma linha, `alignment=ft.alignment.center` → `alignment=ft.alignment.Alignment(0, 0)`
- Excluir explicitamente: qualquer outro arquivo, lógica de login, layout geral.

## Plano de execução (ordem fixa)

1. `views/auth.py` — substituir `alignment=ft.alignment.center` por `alignment=ft.alignment.Alignment(0, 0)`.

## Verificação

- App abre e exibe a tela de login com o ícone water_drop no círculo azul.
- Nenhum `[ERROR]` no log ao iniciar.

## Convenções do projeto

- Camadas tocadas: `views/auth.py`
- Impacto em docs: não

## Riscos e lacunas

- N/A — correção trivial e atômica.
