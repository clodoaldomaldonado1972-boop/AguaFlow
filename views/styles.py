import flet as ft

# Cores principais do AguaFlow
BG_COLOR = "#121417"
PRIMARY_COLOR = "#2196F3"
GREY = "#808080"
ERROR_COLOR = "#FF5252"

# Additional color constants
WHITE = "white"
BG_DARK = BG_COLOR
PRIMARY_BLUE = PRIMARY_COLOR
ACCENT_ORANGE = "#FF9800"

# Estilos de Texto
TEXT_TITLE = ft.TextStyle(size=32, weight="bold", color="white")
TEXT_SUB = ft.TextStyle(size=18, color=GREY)
# 2. Estilos de Texto (CRITICAL: Adicionado para resolver o erro do menu)
TEXT_TITLE = ft.TextStyle(
    size=24,
    weight=ft.FontWeight.BOLD,
    color=WHITE
)

# 3. Configurações de Container de Página
STYLE_PAGE_CONTAINER = {
    "padding": 20,
    "alignment": ft.Alignment(0, 0),
    "expand": True,
    "bgcolor": BG_DARK
}

# 4. Função para campos de entrada (TextField)


def campo_estilo(label, icon_name, password=False, on_submit=None):
    return ft.TextField(
        label=label,
        prefix_icon=icon_name,
        password=password,
        can_reveal_password=True,
        border_color=PRIMARY_BLUE,
        focused_border_color=WHITE,
        color=WHITE,
        width=320,
        height=60,
        on_submit=on_submit,
        border_radius=12,
        text_style=ft.TextStyle(color=WHITE),
        label_style=ft.TextStyle(color=GREY),
        cursor_color=PRIMARY_BLUE
    )


# 5. Estilos de Botão (Corrigido para sintaxe de dicionário do Flet)
BTN_MAIN = ft.ButtonStyle(
    color={"": WHITE},
    bgcolor={"": PRIMARY_BLUE, "hovered": "#1976D2"},
    shape=ft.RoundedRectangleBorder(radius=10),
)

BTN_SPECIAL = ft.ButtonStyle(
    color={"": WHITE},
    bgcolor={"": ACCENT_ORANGE, "hovered": "#FB8C00"},
    shape=ft.RoundedRectangleBorder(radius=10),
)
