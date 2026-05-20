---
title: Investigação — SyntaxError e API quebradas em audio_utils.py bloqueiam rota /configuracoes
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-14
---

## Resumo executivo

- Problema (X): Três falhas em `utils/audio_utils.py` tornam a rota `/configuracoes` inacessível e `tocar_alerta()` crashável: (1) bloco `except` vazio na linha 61 gera SyntaxError no import do módulo; (2) `ft.Audio` não existe no Flet 0.84.0, causando AttributeError em `isinstance(control, ft.Audio)` e `ft.Audio(...)`; (3) `page.snack_bar = ...` + `.open = True` é API removida no Flet 0.84.0.
- Solução alvo (Y): (1) Adicionar `pass` no bloco except vazio; (2) Guardar usos de `ft.Audio` com `hasattr(ft, 'Audio')`; (3) Substituir `page.snack_bar`/`.open` por `page.show_dialog(ft.SnackBar(...))`.
- Confiança: alta

## Contexto

- Sintoma: `views.configuracoes` falha ao importar (`SyntaxError: expected an indented block after 'except'`). Ao clicar em "Configurações" no menu, a rota crasha. `tocar_alerta()` crasharia com `AttributeError: module 'flet' has no attribute 'Audio'` se fosse chamada.
- Ambiente: Windows 11, Flet 0.84.0, Python 3.14
- Reprodução mínima: `python -c "import views.configuracoes"` → SyntaxError.

## Evidências

```
FAIL: views.configuracoes -> expected an indented block after 'except' statement on line 59 (audio_utils.py, line 60)
```

Verificação Python:
```
>>> import flet as ft; hasattr(ft, 'Audio')
False
```

Arquivo: `utils/audio_utils.py`
- Linha 18: `isinstance(control, ft.Audio)` — AttributeError
- Linha 38-43: `page.snack_bar = ft.SnackBar(...)` + `page.snack_bar.open = True` — API removida
- Linha 46: `audio = ft.Audio(...)` — AttributeError
- Linha 57-61: bloco `except` vazio — SyntaxError

## Causa raiz (hipótese consolidada)

`utils/audio_utils.py` foi escrito para Flet com suporte a `ft.Audio` (removido em 0.21+) e para a antiga API `page.snack_bar`. O bloco `except` na linha 60 foi deixado vazio (sem `pass`), gerando SyntaxError que impede a carga do módulo inteiro, bloqueando qualquer arquivo que o importe (só `configuracoes.py` importa atualmente).

## Escopo da correção (atômico)

- Incluir: `utils/audio_utils.py` — 4 correções, ~8 linhas
- Excluir explicitamente: qualquer outra view, database, main.py

## Plano de execução (ordem fixa)

1. **Linha 61** — Adicionar `pass` no bloco `except` vazio (corrige SyntaxError imediatamente)

2. **Linhas 17-19** — Substituir `isinstance(control, ft.Audio)` por guard seguro:
   ```python
   # DE:
   for control in page.overlay[:]:
       if isinstance(control, ft.Audio):
           page.overlay.remove(control)
   # PARA:
   if hasattr(ft, 'Audio'):
       for control in page.overlay[:]:
           if isinstance(control, ft.Audio):
               page.overlay.remove(control)
   ```

3. **Linhas 38-43** — Substituir `page.snack_bar` por `page.show_dialog`:
   ```python
   # DE:
   page.snack_bar = ft.SnackBar(content=ft.Text(mensagem, color="white"), bgcolor=cor, duration=3000)
   page.snack_bar.open = True
   # PARA:
   page.show_dialog(ft.SnackBar(content=ft.Text(mensagem, color="white"), bgcolor=cor))
   ```

4. **Linhas 46-55** — Guardar criação e uso de `ft.Audio` com try/except:
   ```python
   # DE:
   audio = ft.Audio(src=caminho_audio, autoplay=False)
   page.overlay.append(audio)
   page.update()
   try:
       audio.play()
   except Exception as e:
       pass  # (após correção 1)
   # PARA:
   page.update()
   try:
       audio = ft.Audio(src=caminho_audio, autoplay=False)
       page.overlay.append(audio)
       page.update()
       audio.play()
   except (AttributeError, Exception):
       pass
   ```

## Verificação

- `python -c "import views.configuracoes"` → sem SyntaxError
- Navegar para `/configuracoes` → tela abre normalmente
- Trocar senha → sem AttributeError na chamada de `tocar_alerta`
- Nenhum `[ERROR]` no log ao acessar `/configuracoes`

## Convenções do projeto

- Camadas tocadas: `utils/audio_utils.py`
- Impacto em docs: não

## Riscos e lacunas

- `tocar_alerta` ficará silenciosa (sem som) no Flet 0.84.0 pois ft.Audio não existe — comportamento esperado e aceitável.
- Apenas `views/configuracoes.py` importa `tocar_alerta` atualmente — impacto cirúrgico.
