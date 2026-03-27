import flet as ft

# CORES (Baseadas na imagem do medidor)
BG_DARK = "#121417"
PRIMARY_BLUE = "#2196F3"
ACCENT_ORANGE = "#FF9800"
WHITE = "#FFFFFF"
GREY = "#B0B0B0"
# Adicione isso ao seu views/styles.py
ERROR_COLOR = "#FF5252"
SUCCESS_COLOR = "#4CAF50"

def campo_estilo(label, icon, password=False, on_submit=None):
    return ft.TextField(
        label=label,
        prefix_icon=icon,
        password=password,
        can_reveal_password=True, # Olhinho para mostrar senha
        border_color=PRIMARY_BLUE,
        focused_border_color=WHITE,
        color=WHITE,
        width=320,
        on_submit=on_submit,
        border_radius=10,
    )

# ESTILOS DE TEXTO
TEXT_TITLE = ft.TextStyle(size=24, weight="bold", color=WHITE)
TEXT_LABEL = ft.TextStyle(size=16, color=GREY)

# PADRÃO DE BOTÕES
BTN_MAIN = ft.ButtonStyle(
    color=WHITE,
    bgcolor=PRIMARY_BLUE,
    shape=ft.RoundedRectangleBorder(radius=10),
)

BTN_SPECIAL = ft.ButtonStyle(
    color=WHITE,
    bgcolor=ACCENT_ORANGE,
    shape=ft.RoundedRectangleBorder(radius=10),
)