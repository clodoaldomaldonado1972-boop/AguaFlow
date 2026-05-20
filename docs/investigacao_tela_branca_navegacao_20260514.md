---
title: Investigação — Tela branca ao navegar entre rotas
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-14
---

## Resumo executivo

- Problema (X): `on_view_pop` retorna `None` porque `len(page.views) > 1` é sempre False com o padrão `clear()+append()` — quando o Flet tenta fazer pop do único View, o stack fica vazio e o cliente renderiza branco.
- Solução alvo (Y): Substituir a condição por `page.go("/menu")` incondicional; adicionar `scroll=ft.ScrollMode.ADAPTIVE` na Column do menu para garantir que o TextButton row não seja cortado em telas menores.
- Confiança: alta

## Contexto

- Sintoma: Tela branca ao navegar (botão voltar do sistema ou transição entre rotas); relato: "nenhum menu está entrando".
- Ambiente: Windows 11, Flet 0.84, Python, app desktop 450×850.
- Reprodução mínima: Login → /menu → clicar qualquer rota → pressionar botão voltar do sistema (ou Alt+Esquerda).

## Evidências

- `main.py:120-121`: `page.on_view_pop = lambda view: page.go("/menu") if len(page.views) > 1 else None` — com 1 view sempre, a condição nunca passa.
- `aguaflow_debug.log`: rotas `/historico`, `/qrcodes`, `/sobre` carregam sem erro; app é fechado logo depois sem navegar de volta — usuário não usa botão Voltar interno, usa o sistema.
- Nenhum `ERROR` no log para essas rotas.

## Causa raiz (hipótese consolidada)

`on_view_pop` sempre retorna `None` (condição `len > 1` nunca satisfeita). O Flet executa o pop padrão removendo o único View do stack, deixando `page.views = []`. Com stack vazio, o Flutter/Flet renderiza fundo branco.

## Escopo da correção (atômico)

- Incluir: `main.py` (on_view_pop); `views/menu_principal.py` (scroll na Column interna).
- Excluir explicitamente: Mudanças em views de sub-rotas, lógica de autenticação, sync, OCR.

## Plano de execução (ordem fixa)

1. `main.py`: substituir `on_view_pop` por `lambda view: page.go("/menu")` incondicional.
2. `views/menu_principal.py`: adicionar `scroll=ft.ScrollMode.ADAPTIVE` na Column interna com os botões, para garantir visibilidade em telas menores.

## Verificação

- Como validar: Login → /menu → nova rota → pressionar botão voltar sistema → deve retornar ao /menu sem branco.
- Regressões a checar: logout (page.go("/")), navegação por todas as rotas do menu.

## Convenções do projeto

- Camadas tocadas: main.py, views/
- Impacto em docs: sim — atualizar checklist_mvp.md

## Riscos e lacunas

- Se o usuário estiver na tela `/` (login) e pressionar voltar do sistema, `page.go("/menu")` ativará `validar_sessao` → redirecionará para `/` de volta (loop seguro com nova validação).
