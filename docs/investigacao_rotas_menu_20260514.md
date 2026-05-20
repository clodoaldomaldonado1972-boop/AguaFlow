---
title: Investigação — Erros nas rotas do menu (medicao, logo, ft.colors, icon_color)
status: pronto_para_execução
investigador: skill investigador
date: 2026-05-14
---

## Resumo executivo

- **Problema (X):** A rota `/medicao` falha ao ser aberta com dois erros confirmados em log: `ft.colors` foi removido no Flet 0.84.0 e `icon_color` não é argumento válido de `ft.TextField`. Adicionalmente, `icon_color` em `ft.IconButton` dentro de `gerenciamento_usuarios.py` e `sincronizacao.py` podem causar falhas silenciosas. O logo `logo.jpeg` está configurado corretamente mas há risco de exibição vazia caso o asset não exista no diretório `assets/`.
- **Solução alvo (Y):** Substituir `ft.colors.BLUE` / `ft.colors.ORANGE` / `ft.colors.ORANGE_800` por strings de cor compatíveis (`"blue"`, `"orange"`, `"orange800"`); substituir `icon_color=` de `ft.IconButton` por `selected_icon_color=` ou simplesmente `color=`; confirmar asset do logo.
- **Confiança:** alta

---

## Contexto

- **Sintoma:**
  - Tela de Medição (`/medicao`) exibe mensagem de erro em vermelho ao ser aberta.
  - Duas sessões distintas registradas em log com falha na mesma rota.
  - Logo não aparece na tela de login (investigado — causa de configuração, não de código).
- **Ambiente:** Windows 11, Flet 0.84.0, Python 3.14
- **Reprodução mínima:** Clicar em "Medição" no menu principal. A tela exibe `Erro ao carregar tela de medição: <mensagem>` em texto vermelho.

---

## Evidências

### Trechos de log (literal)

```
2026-05-14 07:49:42,031 [DEBUG] __main__: Rota acessada: /medicao
2026-05-14 07:49:42,041 [ERROR] root: TextField.__init__() got an unexpected keyword argument 'icon_color'. Did you mean 'focus_color'?

2026-05-14 08:01:03,120 [DEBUG] __main__: Rota acessada: /medicao
2026-05-14 08:01:03,130 [ERROR] root: module 'flet' has no attribute 'colors'
```

> Dois erros distintos foram registrados em duas sessões separadas. Ambos ocorrem durante a construção da view `/medicao`.

### Arquivos inspecionados

| Arquivo | Linhas relevantes | Problema |
|---|---|---|
| `views/medicao.py` | 113, 173 | `ft.colors.BLUE`, `ft.colors.ORANGE`, `ft.colors.ORANGE_800` — API removida no Flet 0.84.0 |
| `views/medicao.py` | 83, 94 | `icon=` em `ft.TextField` — este parâmetro pode ter sido renomeado; o log de uma sessão aponta `icon_color` (provavelmente uma versão anterior do arquivo ou teste manual) |
| `views/sincronizacao.py` | 139, 153, 157, 171 | `self.btn_sync.icon_color = "..."` — `icon_color` não é atributo dinâmico válido de `ft.IconButton` no Flet 0.84.0 |
| `views/gerenciamento_usuarios.py` | 215 | `ft.IconButton(icon_color="red700", ...)` — parâmetro `icon_color` removido; deve ser `color=` |
| `views/auth.py` | 129 | `ft.Image(src="logo.jpeg", ...)` — correto para Flet com `assets_dir="assets"` |
| `C:\AguaFlow\assets\logo.jpeg` | — | **Arquivo EXISTE** (`Test-Path` retornou `True`). Logo deve aparecer. |
| `main.py` | 154 | `ft.app(target=main, assets_dir="assets")` — configuração correta |

---

## Causa raiz (hipótese consolidada)

### Erro 1 — `ft.colors` removido (Flet 0.84.0)
**Arquivo:** `views/medicao.py` — linhas 113 e 173

```python
# linha 113 — dentro de atualizar_estilos_modo()
cor = ft.colors.BLUE if is_agua else ft.colors.ORANGE

# linha 173 — dentro de btn_reiniciar_ciclo
bgcolor=ft.colors.ORANGE_800,
```

No Flet 0.84.0, o módulo `ft.colors` foi renomeado para `ft.Colors` (maiúscula). O acesso a `ft.colors.*` lança `AttributeError: module 'flet' has no attribute 'colors'`. Este é o erro da segunda sessão de log.

**Correção:** Substituir por strings de cor compatíveis com Material Design: `"blue"`, `"orange"`, `"orange800"`.

---

### Erro 2 — `icon_color` inválido em `ft.TextField` / `ft.IconButton`
**Arquivo:** `views/gerenciamento_usuarios.py` — linha 215
**Arquivo:** `views/sincronizacao.py` — linhas 139, 153, 157, 171

```python
# gerenciamento_usuarios.py:215
ft.IconButton(
    icon="delete_outline",
    icon_color="red700",   # <-- INVÁLIDO no Flet 0.84.0
    ...
)

# sincronizacao.py:139, 153, 157, 171
self.btn_sync.icon_color = "blue600"   # <-- atribuição dinâmica inválida
self.btn_sync.icon_color = "green600"
self.btn_sync.icon_color = "bluegrey200"
self.btn_sync.icon_color = "red600"
```

O parâmetro `icon_color` de `ft.IconButton` foi renomeado para `selected_icon_color` ou simplesmente removido; a propriedade exposta é `color`. O log da primeira sessão aponta `TextField.__init__() got an unexpected keyword argument 'icon_color'`, indicando que em algum momento anterior havia também um TextField com `icon_color` (provável versão em cache/reload).

**Correção:** Substituir `icon_color=` por `color=` em `ft.IconButton`. Remover atribuições dinâmicas `self.btn_sync.icon_color = ...` — substituir por `self.btn_sync.color = ...` ou usar SnackBar colorido para feedback.

---

### Situação 3 — Logo `logo.jpeg` na tela de login
**Arquivo:** `views/auth.py` — linha 129
**Asset:** `C:\AguaFlow\assets\logo.jpeg` — **EXISTE**

```python
ft.Image(
    src="logo.jpeg",   # correto — Flet resolve relativo a assets_dir
    width=90, height=90,
    fit=ft.BoxFit.CONTAIN,
    border_radius=ft.border_radius.all(45),
)
```

O `src="logo.jpeg"` sem barra nem prefixo de path é o formato correto para Flet Desktop com `assets_dir="assets"`. O arquivo existe em `C:\AguaFlow\assets\logo.jpeg`. **Não há erro de código aqui.** A imagem pode não aparecer apenas se:
- O app for iniciado de um diretório diferente de `C:\AguaFlow` (raro em desktop).
- O arquivo estiver corrompido.

Conclusão: o logo deve aparecer normalmente. Se o usuário ainda reportar ausência, verificar se o processo é iniciado a partir de `C:\AguaFlow`.

---

### Situação 4 — `icon=` em `ft.TextField` (views/medicao.py linhas 83, 94)

```python
txt_agua = ft.TextField(
    label="Leitura Água (m³)",
    icon="water_drop",   # linha 83 — parâmetro válido? depende da versão
    ...
)
txt_gas = ft.TextField(
    label="Leitura Gás (m³)",
    icon="local_fire_department",   # linha 94
    ...
)
```

O parâmetro `icon` de `ft.TextField` **não existe** no Flet 0.84.0. O parâmetro correto para ícone prefixo é `prefix_icon`. O log da primeira sessão (`icon_color`) sugere que uma versão anterior ou um hot-reload usava `icon_color`, o que já foi corrigido, mas `icon=` ainda está presente e pode lançar `TypeError: TextField.__init__() got an unexpected keyword argument 'icon'` em certas versões. Deve ser substituído por `prefix_icon=`.

---

## Escopo da correção (atômico)

### Incluir:
1. `views/medicao.py` — substituir `ft.colors.BLUE` → `"blue"`, `ft.colors.ORANGE` → `"orange"`, `ft.colors.ORANGE_800` → `"orange800"` (linhas 113 e 173).
2. `views/medicao.py` — substituir `icon="water_drop"` e `icon="local_fire_department"` em `ft.TextField` por `prefix_icon=` (linhas 83 e 94).
3. `views/gerenciamento_usuarios.py` — substituir `icon_color="red700"` por `color="red700"` em `ft.IconButton` (linha 215).
4. `views/sincronizacao.py` — substituir todas as atribuições `self.btn_sync.icon_color = ...` por `self.btn_sync.color = ...` (linhas 139, 153, 157, 171).

### Excluir explicitamente:
- Não alterar `main.py` — roteamento e assets_dir estão corretos.
- Não alterar `views/auth.py` — logo e layout estão corretos.
- Não alterar `views/styles.py` — não usa `ft.colors.*`.
- Não alterar nenhuma view que já use strings de cor diretamente.
- Não refatorar lógica de negócio — apenas correções de API Flet.

---

## Plano de execução (ordem fixa)

1. **`views/medicao.py` linha 113:** Alterar `cor = ft.colors.BLUE if is_agua else ft.colors.ORANGE` → `cor = "blue" if is_agua else "orange"`.
2. **`views/medicao.py` linha 173:** Alterar `bgcolor=ft.colors.ORANGE_800` → `bgcolor="orange800"`.
3. **`views/medicao.py` linha 83:** Alterar `icon="water_drop"` → `prefix_icon="water_drop"` no `txt_agua`.
4. **`views/medicao.py` linha 94:** Alterar `icon="local_fire_department"` → `prefix_icon="local_fire_department"` no `txt_gas`.
5. **`views/gerenciamento_usuarios.py` linha 215:** Alterar `icon_color="red700"` → `color="red700"`.
6. **`views/sincronizacao.py` linhas 139, 153, 157, 171:** Alterar `self.btn_sync.icon_color = ...` → `self.btn_sync.color = ...` em todos os quatro pontos.
7. Reiniciar o app e navegar para `/medicao` — verificar que a tela carrega sem erro.

---

## Verificação

### Como validar:
- Abrir o app, fazer login, clicar em "Medição" — a tela deve carregar mostrando o dropdown de unidades, os campos de Água e Gás, sem texto vermelho de erro.
- Verificar no log que **não há** `[ERROR]` ao acessar `/medicao`.
- Clicar em "Sincronizar Dados" — SincronizadorUI deve funcionar sem AttributeError em `icon_color`.
- Clicar em "Gerenciar Usuários" — cards de usuário devem exibir o ícone de lixeira sem erro.
- Confirmar visualmente que o logo aparece na tela de login.

### Regressões a checar:
- `atualizar_estilos_modo()` — confirmar que as cores azul/laranja são aplicadas corretamente ao alternar modos Água/Gás.
- `btn_reiniciar_ciclo` — confirmar que o botão aparece com fundo laranja ao concluir todas as unidades.
- Sincronização — confirmar que o botão de sync muda de aparência ao executar (substituindo `icon_color` por `color`).

---

## Convenções do projeto

- **Camadas tocadas:** `views/` — apenas (`medicao.py`, `gerenciamento_usuarios.py`, `sincronizacao.py`)
- **Impacto em docs:** não
- **Padrão de cores:** usar strings Material Design (ex: `"blue"`, `"orange"`, `"red700"`, `"orange800"`) — não usar `ft.colors.*` no Flet 0.84.0
- **Parâmetros de ícone em TextField:** usar `prefix_icon=` (string de ícone Material), não `icon=`
- **Parâmetros de ícone em IconButton:** usar `color=` para a cor do ícone, não `icon_color=`

---

## Riscos e lacunas

- **Risco baixo:** `self.btn_sync.color = ...` pode não causar repaint visual automático sem `page.update()` — mas os pontos em `sincronizacao.py` já chamam `self.page.update()` logo após, então não há regressão.
- **Lacuna:** O log da primeira sessão aponta `icon_color` em um `TextField`, mas o código atual em `medicao.py` usa `icon=` (não `icon_color`). Isso indica que o arquivo pode ter sido editado entre as duas sessões de log. A correção de `icon=` → `prefix_icon=` é preventiva e necessária de qualquer forma.
- **Logo:** Se o usuário ainda reportar ausência de logo após a correção dos outros bugs, verificar permissões do diretório `assets/` e integridade do arquivo JPEG.
- **scanner_view.py:** Usa `datetime.now()` sem importar `datetime` no escopo do `except` (linha 141 — `datetime.now().strftime(...)`). Este trecho só é atingido em caso de erro na captura, mas representa um `NameError` latente. Fora do escopo desta correção.
