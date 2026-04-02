import flet as ft

# Cores mantidas conforme o padrão AguaFlow
BG_DARK = "#121417"
PRIMARY_BLUE = "#2196F3"
ACCENT_ORANGE = "#FF9800"
WHITE = "#FFFFFF"
GREY = "#B0B0B0"

# Novo: Estilo de Container para padronizar as views
STYLE_PAGE_CONTAINER = {
    "padding": 20,
    "alignment": ft.alignment.center,
    "expand": True,
    "bgcolor": BG_DARK
}


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
        height=60,  # Aumentado levemente para melhor toque (touch)
        on_submit=on_submit,
        border_radius=12,
        text_style=ft.TextStyle(color=WHITE),
        label_style=ft.TextStyle(color=GREY),
        cursor_color=PRIMARY_BLUE
    )


# Botões com estado de "Hover" (passar o mouse)
BTN_MAIN = ft.ButtonStyle(
    color={"": WHITE},
    bgcolor={"": PRIMARY_BLUE, "hovered": "#1976D2"},
    shape=ft.RoundedRectangleBorder(radius=10),
)
