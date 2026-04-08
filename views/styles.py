import flet as ft

# --- CORES PRINCIPAIS ---
BG_COLOR = "#121417"
PRIMARY_COLOR = "#2196F3"
GREY = "#808080"
ERROR_COLOR = "#FF5252"
WHITE = "white"
BG_DARK = BG_COLOR
PRIMARY_BLUE = PRIMARY_COLOR
ACCENT_ORANGE = "#FF9800"

# --- ESTILOS DE TEXTO ---
TEXT_TITLE = ft.TextStyle(
    size=24,
    weight=ft.FontWeight.BOLD,
    color=WHITE
)
TEXT_SUB = ft.TextStyle(size=18, color=GREY)

# --- CONFIGURAÇÕES DE CONTAINER ---
STYLE_PAGE_CONTAINER = {
    "padding": 20,
    "alignment": ft.Alignment(0, 0),
    "expand": True,
    "bgcolor": BG_DARK
}

# --- COMPONENTES PADRONIZADOS ---


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


# --- ESTILOS DE BOTÃO ---
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
