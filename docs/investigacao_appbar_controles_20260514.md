---
title: Investigação — AppBar em controls[] causa botão ← inacessível
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-14
---

## Resumo executivo

- Problema (X): `ft.AppBar` colocado em `controls=[]` do `ft.View` (em vez de `appbar=`) rola junto com o conteúdo quando a View tem `scroll=`. Em `/medicao`, que tem `scroll=ft.ScrollMode.ADAPTIVE` no nível da View, o AppBar desaparece da tela quando o usuário rola o formulário — tornando o botão ← completamente inacessível.
- Solução alvo (Y): Mover `ft.AppBar` de `controls=[]` para o parâmetro `appbar=` em todos os 11 views afetados. Para `/medicao`, remover `scroll` da View e adicioná-lo à Column interna.
- Confiança: alta

## Contexto

- Sintoma: "Botão voltar não funciona em nenhuma tela, todas em branco." Usuário fecha o app após cada visita a /medicao sem conseguir navegar de volta.
- Ambiente: Windows 11, Flet 0.84.0, app desktop 1280×720.
- Reprodução mínima: Login → /medicao → rolar o formulário para baixo → tentar clicar ← → botão não está mais na tela visível.

## Evidências

- `aguaflow_debug.log`: em 6 sessões consecutivas o usuário acessa `/` → `/menu` → `/medicao` e fecha o app. Nunca aparece `Rota acessada: /menu` APÓS `/medicao` — confirma que o usuário não consegue voltar.
- `views/medicao.py` linha 361: `ft.View(route="/medicao", scroll=ft.ScrollMode.ADAPTIVE, controls=[ft.AppBar(...), ft.Column(...)])` — scroll na View faz o AppBar rolar junto com o conteúdo.
- Padrão idêntico (AppBar em controls[]) em outros 10 arquivos, confirmado por inspeção direta.

## Causa raiz (hipótese consolidada)

Quando `ft.AppBar` é filho de `controls=[]` e a View tem `scroll`, o Flutter renderiza o AppBar como widget comum dentro do corpo scrollável. Ao rolar, ele sai da viewport. Quando colocado em `appbar=`, o Flutter o fixa acima do corpo (fora da área de scroll), sempre visível.

## Escopo da correção (atômico)

- Incluir: mover AppBar de `controls[]` para `appbar=` em 11 views; remover `scroll` de `/medicao` View e adicionar à Column interna.
- Excluir explicitamente: lógica de negócio, autenticação, sync, OCR, estilos.

## Plano de execução (ordem fixa)

1. `views/medicao.py` — mover AppBar para `appbar=`, remover `scroll` do View, adicionar `scroll=ft.ScrollMode.ADAPTIVE` à Column interna.
2. `views/menu_principal.py` — mover AppBar para `appbar=`.
3. `views/ajuda_view.py` — mover AppBar para `appbar=`.
4. `views/configuracoes.py` — mover AppBar para `appbar=`.
5. `views/dashboard.py` — mover AppBar para `appbar=`.
6. `views/dashboard_saude.py` — mover AppBar para `appbar=`.
7. `views/gerenciamento_usuarios.py` — mover AppBar para `appbar=`.
8. `views/qrcodes_view.py` — mover AppBar para `appbar=`.
9. `views/sobre_view.py` — mover AppBar para `appbar=`.
10. `views/relatorio_view.py` — mover AppBar para `appbar=`.
11. `views/sincronizacao.py` — mover AppBar para `appbar=`.

## Verificação

- Como validar: Login → /medicao → rolar formulário → clicar ← → deve voltar ao /menu. Log deve mostrar `Rota acessada: /menu` após `/medicao`.
- Regressões a checar: AppBar continua visível em todas as telas; logout do menu ainda funciona; ações de AppBar (botão sync em dashboard_saude) continuam funcionando.

## Convenções do projeto

- Camadas tocadas: views/
- Impacto em docs: não

## Riscos e lacunas

- `menu_principal.py` usa `actions=[btn_offline, btn_logout]` no AppBar — manter esses actions ao mover para `appbar=`.
- `dashboard_saude.py` usa `actions=[sincronizador.btn_sync]` — manter.
- `scanner_view.py` e `medicao.py` (appbar=) já estavam corretos segundo investigação anterior, mas leitura atual de medicao.py mostra AppBar em controls[]. O arquivo será corrigido.
