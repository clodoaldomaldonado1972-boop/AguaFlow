# Investigação: Varredura Completa de Views — Flet 0.84.0
**Data:** 2026-05-14  
**Escopo:** `C:\AguaFlow\views\` (todos os arquivos .py)  
**Versão Flet instalada:** 0.84.0 (confirmado via `pip show flet`)  
**status: pronto_para_execução**

---

## Resumo Executivo

Foram encontrados **5 grupos de problemas** afetando **7 arquivos**. Todos são bugs reais que vão causar `AttributeError` ou comportamento incorreto em tempo de execução no Flet 0.84.0.

| # | Padrão Quebrado | Arquivos Afetados | Severidade |
|---|---|---|---|
| 1 | `from flet import colors` | `dashboard.py` | CRÍTICO — ImportError na carga do módulo |
| 2 | `ft.transform.Offset` / `ft.animation.Animation` | `styles.py` | CRÍTICO — AttributeError ao abrir scanner |
| 3 | `ft.Row(..., icon="close")` | `dashboard.py` | CRÍTICO — TypeError ao abrir detalhe de unidade |
| 4 | `page.dialog = ...` / `page.snack_bar = ...` | 5 arquivos | CRÍTICO — AttributeError em toda interação |
| 5 | `ft.Audio(...)` | `scanner_view.py` | CRÍTICO — AttributeError ao abrir scanner |
| 6 | `page.on_view_appear` | `dashboard_saude.py` | ALTO — AttributeError silencioso, log não carrega |
| 7 | `ft.AppBar` em `controls[]` | 8 arquivos | MÉDIO — misrendering (não crasha, mas AppBar não é posicionada corretamente) |

---

## Problemas Detalhados por Arquivo

### ARQUIVO 1: `views/dashboard.py`

#### Problema 1.1 — `from flet import colors` (linha 5)
```python
# LINHA 5 — QUEBRADO:
from flet import colors  # Importar colors para uso direto
```
- **Erro:** `ImportError: cannot import name 'colors' from 'flet'`
- **Quando quebra:** Na carga do módulo (`import views.dashboard`) — crash imediato antes de qualquer view ser montada
- **Verificado:** `python -c "from flet import colors"` → `ImportError`
- **Correção:** Remover a linha. O módulo `ft.colors` foi removido no Flet 0.21+; usar strings diretas como `"green"`, `"red"` (o código no arquivo já faz isso — o import é letra morta, mas causa ImportError)

```python
# LINHA 5 — CORRETO (remover completamente):
# (deletar a linha)
```

#### Problema 1.2 — `ft.Row(..., icon="close")` (linha 50)
```python
# LINHA 50 — QUEBRADO:
], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, icon="close"),
```
- **Erro:** `TypeError: Row.__init__() got an unexpected keyword argument 'icon'`
- **Quando quebra:** Ao clicar em qualquer unidade no mapa de coleta (abre o BottomSheet)
- **Verificado:** `ft.Row` não tem parâmetro `icon` em Flet 0.84.0
- **Correção:** Remover `icon="close"` — o `ft.IconButton("close", ...)` já está dentro do Row corretamente

```python
# LINHA 50 — CORRETO:
], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
```

---

### ARQUIVO 2: `views/styles.py`

#### Problema 2.1 — `ft.transform.Offset` (linhas 58, 68, 69)
```python
# LINHA 58 — QUEBRADO:
offset=ft.transform.Offset(0, -2.5),
# LINHA 68-69 — QUEBRADO:
linha_scanner.offset = ft.transform.Offset(
    0, 2.5) if linha_scanner.offset.y == -2.5 else ft.transform.Offset(0, -2.5)
```
- **Erro:** `AttributeError: module 'flet' has no attribute 'transform'`
- **Quando quebra:** Ao abrir a tela do scanner (função `criar_mira_scanner()` é chamada em `scanner_view.py`)
- **Verificado:** `ft.transform` não existe; API correta é `ft.Offset`
- **Correção:** Substituir `ft.transform.Offset` → `ft.Offset`

```python
# LINHAS 58, 68, 69 — CORRETO:
offset=ft.Offset(0, -2.5),
# ...
linha_scanner.offset = ft.Offset(
    0, 2.5) if linha_scanner.offset.y == -2.5 else ft.Offset(0, -2.5)
```

#### Problema 2.2 — `ft.animation.Animation` (linha 59)
```python
# LINHA 59-60 — QUEBRADO:
animate_offset=ft.animation.Animation(
    1500, ft.AnimationCurve.EASE_IN_OUT)
```
- **Erro:** `AttributeError: module 'flet' has no attribute 'animation'`
- **Quando quebra:** Junto com o problema 2.1, ao abrir o scanner
- **Verificado:** `ft.animation` não existe; API correta é `ft.Animation`
- **Correção:** Substituir `ft.animation.Animation` → `ft.Animation`

```python
# LINHAS 59-60 — CORRETO:
animate_offset=ft.Animation(
    1500, ft.AnimationCurve.EASE_IN_OUT)
```

---

### ARQUIVO 3: `views/scanner_view.py`

#### Problema 3.1 — `ft.Audio(...)` (linha 20)
```python
# LINHA 20 — QUEBRADO:
audio_beep = ft.Audio(src="audio/beep.mp3", autoplay=False)
```
- **Erro:** `AttributeError: module 'flet' has no attribute 'Audio'`
- **Quando quebra:** Ao abrir a tela do scanner
- **Verificado:** `ft.Audio` não existe no Flet 0.84.0 (removido — sem substituto direto no módulo flet)
- **Correção:** Remover `ft.Audio` e substituir a lógica de beep por `playsound` ou `pygame` em thread separada. Como solução mínima de impacto zero: envolver em try/except para que o scanner funcione sem áudio.

```python
# LINHA 20-21 — CORRETO (solução defensiva mínima):
try:
    audio_beep = ft.Audio(src="audio/beep.mp3", autoplay=False)
    if audio_beep not in page.overlay:
        page.overlay.append(audio_beep)
except AttributeError:
    audio_beep = None  # Audio não suportado nesta versão do Flet
```
> **Nota:** Qualquer chamada posterior a `audio_beep.play()` deve ser também protegida com `if audio_beep:`.

---

### ARQUIVO 4: `views/dashboard_saude.py`

#### Problema 4.1 — `page.on_view_appear` (linha 100)
```python
# LINHA 100 — QUEBRADO:
page.on_view_appear = lambda e: carregar_log_file(None)
```
- **Erro:** `AttributeError: 'Page' object has no attribute 'on_view_appear'`
- **Quando quebra:** Na montagem da tela `/dashboard_saude` (atribuição de handler inexistente)
- **Verificado:** `on_view_appear` não existe em `ft.Page` no Flet 0.84.0; os eventos disponíveis são `on_route_change`, `on_view_pop`, etc.
- **Correção:** Remover o handler e chamar `carregar_log_file(None)` diretamente ao final da função `montar_tela_saude`, ou usar `page.on_route_change`.

```python
# LINHA 100 — CORRETO (duas opções):

# Opção A: Carregar log diretamente ao montar a tela (mais simples)
# (remover a linha 100 e adicionar antes do return:)
carregar_log_file(None)

# Opção B: Usar on_route_change (se quiser recarregar ao revisitar)
# (remover a linha 100 — on_route_change é gerenciado no main.py)
```

---

### ARQUIVO 5: `views/configuracoes.py`

#### Problema 5.1 — `page.dialog = ...` e `page.snack_bar = ...` (múltiplas linhas)
```python
# LINHAS 58, 64, 72, 78, 105, 112 — QUEBRADO (exemplos):
page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=st.SUCCESS_GREEN)
page.snack_bar.open = True
# LINHA 130:
page.dialog = ft.AlertDialog(...)
page.dialog.open = True
page.update()
```
- **Erro:** `AttributeError: 'Page' object has no attribute 'snack_bar'` / `'dialog'`
- **Quando quebra:** Ao trocar senha, limpar cache, ou excluir conta
- **API correta Flet 0.84.0:**
  - `page.show_dialog(dialog)` — para AlertDialog E SnackBar (ambos herdam de `DialogControl`)
  - `page.pop_dialog()` — para fechar o dialog do topo
  - `page.show_dialog` já define `open=True` internamente; não chamar `page.update()` manualmente

```python
# CORRETO — AlertDialog:
dlg = ft.AlertDialog(title=..., content=..., actions=[...])
page.show_dialog(dlg)
# Para fechar de dentro do handler:
page.pop_dialog()

# CORRETO — SnackBar:
page.show_dialog(ft.SnackBar(ft.Text(msg), bgcolor=st.SUCCESS_GREEN))
```

---

### ARQUIVO 6: `views/gerenciamento_usuarios.py`

#### Problema 6.1 — `page.dialog = ...` e `page.snack_bar = ...` (múltiplas linhas)
```
Linhas afetadas: 55, 60, 78, 82, 97-108, 124, 131, 138, 143, 148-159
```
- **Mesmo padrão e correção que Arquivo 5.**
- Todos os `page.dialog = ft.AlertDialog(...)` + `page.dialog.open = True` + `page.update()` devem virar `page.show_dialog(ft.AlertDialog(...))`
- Todos os `page.snack_bar = ft.SnackBar(...)` + `page.snack_bar.open = True` devem virar `page.show_dialog(ft.SnackBar(...))`
- Os `fechar(e)` internos que fazem `page.dialog.open = False; page.update()` devem virar `page.pop_dialog()`

---

### ARQUIVO 7: `views/menu_principal.py`

#### Problema 7.1 — `page.dialog = ...` e `page.snack_bar = ...` (linhas 44-49, 57-67)
```python
# LINHA 44 — QUEBRADO:
page.snack_bar = ft.SnackBar(content=ft.Text("Logout realizado com sucesso!"), ...)
page.snack_bar.open = True
# LINHA 57 — QUEBRADO:
page.dialog = ft.AlertDialog(...)
page.dialog.open = True
page.update()
```
- **Mesmo padrão e correção que Arquivos 5 e 6.**

---

### ARQUIVO 8: `views/medicao.py`

#### Problema 8.1 — `page.dialog = ...` e `page.snack_bar = ...`
```
Linhas afetadas: 148, 238-..., 259, 275, 294
```
- **Mesmo padrão e correção que Arquivos 5, 6, 7.**

---

### ARQUIVO 9: `views/sincronizacao.py`

#### Problema 9.1 — `page.snack_bar = ...` (linhas 160, 175)
```python
# LINHA 160 — QUEBRADO (dentro de SincronizadorUI.executar_sincronismo):
self.page.snack_bar = ft.SnackBar(content=ft.Text(feedback_msg), ..., open=True)
# LINHA 175 — QUEBRADO:
self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro: ..."), ..., open=True)
```
- **Mesmo padrão e correção. Nota:** Aqui o código já passa `open=True` no construtor, mas a atribuição a `page.snack_bar` ainda vai crashar.
- **Correção:**
```python
self.page.show_dialog(ft.SnackBar(content=ft.Text(feedback_msg), bgcolor=..., open=True))
```

---

## Padrões Verificados e Confirmados VÁLIDOS no Flet 0.84.0

Os seguintes padrões foram inspecionados e **não requerem correção**:

| Padrão | Status | Observação |
|---|---|---|
| `ft.MainAxisAlignment.CENTER/END/SPACE_BETWEEN` | OK | Enum válido |
| `ft.CrossAxisAlignment.CENTER/START` | OK | Enum válido |
| `ft.ScrollMode.ADAPTIVE` | OK | Enum válido |
| `ft.TextAlign.CENTER` | OK | Enum válido |
| `ft.TextStyle(size=..., color=...)` | OK | Classe válida |
| `ft.ButtonStyle(color=..., bgcolor=...)` | OK | Classe válida |
| `ft.RoundedRectangleBorder(radius=...)` | OK | Classe válida |
| `ft.AnimationCurve.EASE_IN_OUT` | OK | Enum válido |
| `ft.alignment.Alignment(0, 0)` | OK | Classe válida |
| `ft.border.all(...)` / `ft.border_radius.*` | OK | Módulo válido |
| `ft.margin.only(...)` | OK | Módulo válido |
| `ft.ClipBehavior.ANTI_ALIAS` | OK | Enum válido |
| `ft.dropdown.Option(...)` | OK | Válido |
| `ft.View(route=..., controls=[...])` | OK | kwargs corretos |
| `ft.View(vertical_alignment=ft.MainAxisAlignment.*)` | OK | Aceita enum |
| `ft.IconButton(icon_color=...)` | OK | Válido em IconButton (não TextField) |
| `ft.icons.*` em comentários | OK | Inativo |
| `ft.SnackBar(content=ft.Text(...), bgcolor=...)` | OK | content aceita Control |
| `page.overlay.append(ft.BottomSheet(...))` | OK | Padrão válido |
| `ft.BottomSheet(content=ft.Container(...), open=True)` | OK | Parâmetros válidos |

### Aviso sobre AppBar em `controls[]` (não-fatal, MÉDIO)

Em 8 arquivos, o `ft.AppBar(...)` é colocado dentro de `controls=[]` do `ft.View` em vez de usar o parâmetro `appbar=`. No Flet 0.84.0 isso **não causa crash** (AppBar herda de BaseControl), mas o AppBar é renderizado como um widget comum dentro do scroll da página, não fixo no topo. Os arquivos que já usam `appbar=` corretamente: `scanner_view.py` (linha 182), `medicao.py` (linha 365).

Arquivos que usam AppBar em controls[]: `configuracoes.py`, `gerenciamento_usuarios.py`, `dashboard_saude.py`, `dashboard.py`, `sincronizacao.py`, `sobre_view.py`, `qrcodes_view.py`, `relatorio_view.py`.

**Recomendação:** Corrigir em batch futuro, mas não é bloqueante para execução.

---

## Plano de Execução

### Ordem de prioridade (CRÍTICO primeiro)

#### PASSO 1 — `views/dashboard.py` (2 fixes, 2 linhas)
1. **Linha 5:** Deletar `from flet import colors`
2. **Linha 50:** Remover `, icon="close"` do `ft.Row(...)`

#### PASSO 2 — `views/styles.py` (2 fixes, 4 linhas)
1. **Linha 58:** `ft.transform.Offset` → `ft.Offset`
2. **Linha 59:** `ft.animation.Animation` → `ft.Animation`
3. **Linhas 68-69:** `ft.transform.Offset` → `ft.Offset` (2 ocorrências)

#### PASSO 3 — `views/scanner_view.py` (1 fix)
1. **Linha 20:** Envolver `ft.Audio(...)` em try/except com fallback `audio_beep = None`

#### PASSO 4 — `views/dashboard_saude.py` (1 fix)
1. **Linha 100:** Remover `page.on_view_appear = ...`; chamar `carregar_log_file(None)` diretamente antes do `return`

#### PASSO 5 — Migração `page.dialog` / `page.snack_bar` → `page.show_dialog()` (5 arquivos)
- `views/configuracoes.py`
- `views/gerenciamento_usuarios.py`
- `views/menu_principal.py`
- `views/medicao.py`
- `views/sincronizacao.py`

**Template de substituição para cada arquivo:**

```python
# DE:
page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=cor)
page.snack_bar.open = True
page.update()

# PARA:
page.show_dialog(ft.SnackBar(ft.Text(msg), bgcolor=cor))
page.update()
```

```python
# DE:
page.dialog = ft.AlertDialog(title=..., content=..., actions=[...], actions_alignment=...)
page.dialog.open = True
page.update()

# PARA:
page.show_dialog(ft.AlertDialog(title=..., content=..., actions=[...], actions_alignment=...))
```

```python
# DE (dentro de on_click handler para fechar dialog):
page.dialog.open = False
page.update()

# PARA:
page.pop_dialog()
```

---

## Contagem Total de Problemas

| Severidade | Quantidade |
|---|---|
| CRÍTICO (causa crash/AttributeError) | 7 ocorrências em 7 arquivos |
| ALTO (comportamento errado sem crash) | 1 ocorrência em 1 arquivo |
| MÉDIO (visual incorreto, não-fatal) | 8 arquivos (AppBar em controls[]) |

**Total de linhas a editar (crítico + alto):** ~50 linhas distribuídas em 7 arquivos.
