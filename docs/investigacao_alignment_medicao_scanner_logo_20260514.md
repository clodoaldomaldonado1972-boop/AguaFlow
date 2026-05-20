---
title: Investigação — ft.alignment.center em medicao/scanner + logo círculo branco
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-14
---

## Resumo executivo

- Problema (X): Três falhas independentes confirmadas em log e relato visual: (1) rota `/medicao` falha com `AttributeError: module 'flet.controls.alignment' has no attribute 'center'` em `medicao.py:375`; (2) mesma falha em `scanner_view.py:191` para a rota `/scanner`; (3) logo na tela de login exibe círculo branco em vez de gota d'água azul — o `ft.Container` com `bgcolor` e `border_radius` sem `clip_behavior` não recorta o fundo corretamente no Flet 0.84.0.
- Solução alvo (Y): (1+2) Substituir `ft.alignment.center` por `ft.alignment.Alignment(0, 0)` nos dois arquivos. (3) Adicionar `clip_behavior=ft.ClipBehavior.ANTI_ALIAS` ao Container do logo em `auth.py`.
- Confiança: alta

## Contexto

- Sintoma 1: Clicar em "Medição" no menu abre tela vermelha de erro.
- Sintoma 2: Clicar em "Scanner" deve causar o mesmo erro (não testado mas confirmado no código).
- Sintoma 3: Logo na tela de login aparece como círculo branco sem a gota d'água azul.
- Ambiente: Windows 11, Flet 0.84.0, Python 3.14
- Reprodução: iniciar app → login → clicar "Medição".

## Evidências

Log literal (08:14:39):
```
[DEBUG] Rota acessada: /medicao
[ERROR] module 'flet.controls.alignment' has no attribute 'center'
value="Erro ao carregar tela de medição: module 'flet.controls.alignment' has no attribute 'center'"
```

Código confirmado:
- `views/medicao.py:375`: `alignment=ft.alignment.center`
- `views/scanner_view.py:191`: `alignment=ft.alignment.center,`
- `views/auth.py:133`: `alignment=ft.alignment.Alignment(0, 0)` — correto, mas falta `clip_behavior`

## Causa raiz

No Flet 0.84.0, `ft.alignment` não expõe aliases como `.center`, `.top_left` etc.
A API correta é `ft.alignment.Alignment(x, y)` onde `(0, 0)` = centro.

Para o logo: `ft.Container` com `border_radius` sem `clip_behavior=ft.ClipBehavior.ANTI_ALIAS`
não recorta o conteúdo nem o bgcolor ao círculo — o fundo padrão (branco/transparente)
fica visível em vez do `bgcolor` configurado.

## Escopo da correção (atômico)

- Incluir:
  - `views/medicao.py:375` — `ft.alignment.center` → `ft.alignment.Alignment(0, 0)`
  - `views/scanner_view.py:191` — `ft.alignment.center` → `ft.alignment.Alignment(0, 0)`
  - `views/auth.py` (Container do logo) — adicionar `clip_behavior=ft.ClipBehavior.ANTI_ALIAS`
- Excluir explicitamente: lógica de negócio, outras views, main.py, database.

## Plano de execução (ordem fixa)

1. `views/medicao.py:375` — substituir `alignment=ft.alignment.center` por `alignment=ft.alignment.Alignment(0, 0)`
2. `views/scanner_view.py:191` — substituir `alignment=ft.alignment.center,` por `alignment=ft.alignment.Alignment(0, 0),`
3. `views/auth.py` — no `ft.Container` do logo, adicionar linha `clip_behavior=ft.ClipBehavior.ANTI_ALIAS,`

## Verificação

- Login → clicar "Medição" → tela de medição abre sem erro vermelho.
- Login → clicar "Scanner" → tela do scanner abre sem erro.
- Tela de login exibe gota d'água branca em círculo azul escuro (#1565C0).
- Nenhum `[ERROR]` no log ao acessar /medicao ou /scanner.

## Convenções do projeto

- Camadas tocadas: `views/` — medicao.py, scanner_view.py, auth.py
- Impacto em docs: não

## Riscos e lacunas

- N/A — substituições pontuais de API, sem impacto em lógica.
