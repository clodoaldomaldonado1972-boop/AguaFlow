---
title: Investigação — Medição volta ao menu em vez de avançar para próxima unidade
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-22
---

## Resumo executivo

- Problema (X): Após salvar leitura ou retornar do scanner, o app navega para `/menu`
  em vez de permanecer em `/medicao` e avançar para a próxima unidade; ao retornar,
  a tela exibe a unidade 66 (a que estava sendo lida antes da interrupção).
- Solução alvo (Y): Eliminar a janela de vulnerabilidade de 0.5 s em `salvar_clique()`
  (onde o back button do Android cancela a navegação), garantir que `_persistir_estado()`
  salva a PRÓXIMA unidade (não a atual) e adicionar log ao `on_view_pop` para rastreio.
- Confiança: alta (para a causa A) / média (para a causa B)

## Contexto

- Sintoma: Após gravar leitura da unidade 66 ÁGUA, o app vai para o menu principal;
  ao retornar à medição, a tela exibe novamente a unidade 66.
- Ambiente: Android, APK 1.2.0 build 123, Flet 0.82.2.
- Reprodução mínima: Ler qualquer unidade → pressionar "GRAVAR LEITURA" → durante os
  0.5 s da animação do ícone de salvo, pressionar (ou gesturar) o botão voltar →
  app vai ao menu; ou: sair do scanner via back button enquanto o OCR ainda roda.

## Evidências

- `views/medicao.py` linha 471–496: `salvar_clique()` tem `await asyncio.sleep(0.5)`
  *entre* o `page.update()` da animação e a chamada a `avancar()` ou `abrir_dialogo_gas()`.
  Durante esses 500 ms o event loop do Flet processa outros eventos — incluindo o back
  button do Android, que dispara `on_view_pop` → `page.go("/menu")`.
- `main.py` linhas 143–150 (versão anterior): `on_view_pop` verificava `page.route`
  (já atualizado) em vez de `view.route` (rota da view sendo fechada); race condition
  fazia o app ir ao menu em vez de `/medicao` ao fechar o scanner. **Corrigido no APK
  17:35**, mas o `asyncio.sleep(0.5)` é uma vulnerabilidade independente.
- `views/medicao.py` linha 353: `_persistir_estado()` em `avancar()` é chamado *após*
  `txt_unidade.value = proxima`, portanto salva a unidade correta — MAS só é chamado se
  `avancar()` chega a ser executado. Se o proceso for morto durante o `asyncio.sleep`,
  `client_storage` ainda tem `medicao_unidade = "66"` (salvo pelo `_abrir_scanner()`
  do commit ccc7740), explicando por que a tela exibe "66" ao retornar.
- `database/database.py` linha 327: `salvar_leitura()` faz `INSERT` (não UPSERT); se o
  processo for morto após o commit do SQLite mas antes do `avancar()`, a unidade 66
  está marcada como lida no banco, mas o `client_storage` ainda aponta para ela → ao
  retornar, `buscar_primeira_pendente()` devolveria 65, mas o fluxo de restauração
  `_cs_unidade` verifica `_unidade_lida("66", _cs_lidos)` = True → não usa "66" →
  usa a pendente → deveria mostrar 65. **Inconsistência:** o usuário relata "66" na
  tela, o que indica que o processo foi morto ANTES do commit do SQLite.

## Causa raiz (hipótese consolidada)

**Causa A (alta confiança):** O `asyncio.sleep(0.5)` em `salvar_clique()` cria uma janela
de 500 ms onde o back button do Android (ou swipe lateral) dispara `on_view_pop` →
`page.go("/menu")`. O coroutine de `salvar_clique()` continua rodando em segundo plano
após a navegação, executando `avancar()` ou `abrir_dialogo_gas()` em uma view destruída
— sem efeito visível para o usuário.

**Causa B (média confiança):** Em dispositivos com pouca RAM, o Android mata o processo
Python durante o `await asyncio.to_thread(Database.salvar_leitura, ...)` ou durante o
`asyncio.sleep(0.5)`. O `client_storage` retém `medicao_unidade = "66"` e o banco pode
ou não ter o commit — dependendo do timing do kill.

## Escopo da correção (atômico)

- Incluir:
  1. Remover `asyncio.sleep(0.5)` de `salvar_clique()` — substituir por animação
     não-bloqueante (mostrar ícone por 300 ms via `asyncio.create_task`).
  2. Em `salvar_clique()`, chamar `_persistir_estado()` imediatamente após o save
     bem-sucedido (antes de qualquer `await`), para que o `client_storage` reflita
     o estado atual mesmo se o processo for morto logo depois.
  3. Adicionar `logger.info` no `_on_view_pop` para rastrear quando e de onde é chamado.
- Excluir explicitamente:
  - Refatoração de `avancar()`, `buscar_proxima_pendente()` ou do schema do banco.
  - Alteração na lógica de GÁS (`abrir_dialogo_gas`).
  - Mudança no APK build number (só código Python — sem recompilação de Dart).

## Plano de execução (ordem fixa)

1. **`views/medicao.py` — `salvar_clique()`**: substituir o bloco de animação síncrona:
   ```python
   # ANTES (cria janela de vulnerabilidade de 500 ms)
   img_icon.visible, icon_save.visible = False, True
   page.update()
   await asyncio.sleep(0.5)
   img_icon.visible, icon_save.visible = True, False

   # DEPOIS (animação não-bloqueante + persistência imediata)
   _persistir_estado()   # persiste antes de qualquer await
   img_icon.visible, icon_save.visible = False, True
   page.update()
   asyncio.create_task(_restaurar_icone())  # não bloqueia o handler
   ```
   Adicionar helper síncrono ao escopo da função:
   ```python
   async def _restaurar_icone():
       await asyncio.sleep(0.3)
       if img_icon and icon_save:
           img_icon.visible, icon_save.visible = True, False
           try:
               page.update()
           except Exception:
               pass
   ```

2. **`views/medicao.py` — `salvar_clique()`**: remover o `await asyncio.sleep(0.5)`
   e a linha `img_icon.visible, icon_save.visible = True, False` que estava após o sleep.

3. **`main.py` — `_on_view_pop()`**: adicionar log:
   ```python
   def _on_view_pop(view):
       popped = getattr(view, "route", None) or page.route
       logger.info(f"🔙 on_view_pop: popped={popped} | page.route={page.route}")
       if popped == "/scanner":
           page.go("/medicao")
       else:
           page.go("/menu")
   ```

4. Rodar `pytest tests/ -q` para confirmar 114 testes passando.

5. Commit: `fix(medicao): elimina sleep bloqueante em salvar_clique + log no_view_pop`

## Verificação

- Como validar que o problema sumiu: gravar leitura → pressionar back imediatamente
  após o clique → app deve permanecer em `/medicao` (o back button precisa ser
  pressionado *antes* do clique; após o clique não deve mais vazar para o menu).
- Regressões a checar: animação do ícone de salvo ainda visível (300 ms);
  `abrir_dialogo_gas()` ainda abre após salvar última unidade do hall;
  `avancar()` ainda avança para a próxima unidade pendente.

## Convenções do projeto

- Camadas tocadas: `views/` (medicao.py), `main.py`
- Impacto em docs: não — nenhuma alteração em AGENTS.md ou docs/

## Riscos e lacunas

- Se o Android matar o processo durante `asyncio.to_thread(Database.salvar_leitura, ...)`,
  a unidade pode ou não ter sido gravada. Não há rollback automático para este caso.
  Mitigação: o `client_storage` com `medicao_unidade` permite retomar, e o usuário
  verá o campo com o valor que digitou (via `client_storage`) — pode regravar sem dano.
- O helper `_restaurar_icone()` acessa `img_icon` e `icon_save` via closure; se a view
  for destruída antes dos 300 ms, o `page.update()` pode lançar exceção — por isso o
  `try/except` é necessário.
- Não foi possível reproduzir em ambiente desktop (requer Android físico para confirmar
  a janela de vulnerabilidade do back button).
