import flet as ft

# --- 1. CORES BASE ---
BG_DARK = "#121417"
PRIMARY_BLUE = "#2196F3"
WHITE = "#FFFFFF"
GREY_TEXT = "#BDBDBD"
ACCENT_ORANGE = "#FF9800"
RED_ERROR = "#FF5252"
SUCCESS_GREEN = "#2E7D32"

# --- 2. APELIDOS DE COMPATIBILIDADE ---
BG_COLOR = BG_DARK
PRIMARY_COLOR = PRIMARY_BLUE
TEXT_COLOR = WHITE
GREY = GREY_TEXT
ERROR_COLOR = RED_ERROR
SECUNDARY_COLOR = ACCENT_ORANGE
TEXT_TITLE = ft.TextStyle(size=22, weight="bold", color=WHITE)
TEXT_SUB = ft.TextStyle(size=16, color=GREY_TEXT)
TEXT_BODY = ft.TextStyle(size=14, color=WHITE)

# --- 3. ESTILOS (CORREÇÃO: Transformado em função) ---
def campo_estilo(label, icon=None, password=False):
    return ft.TextField(
        label=label,
        prefix_icon=icon if icon is not None else None,
        password=password,
        can_reveal_password=password,
        border_color=PRIMARY_BLUE,
        focused_border_color=ACCENT_ORANGE,
        label_style=ft.TextStyle(color=GREY_TEXT),
        color=WHITE,
        border_radius=10,
        bgcolor="#25282D"
    )

STYLE_PAGE_CONTAINER = {
    "padding": 20,
    "border_radius": 15,
    "expand": True,
    "bgcolor": "#1E2126"
}

# --- 4. ELEMENTOS VISUAIS ---
def criar_mira_scanner():
    return ft.Container(
        content=ft.Stack([
            ft.Container(width=300, height=220, border=ft.border.all(2, PRIMARY_BLUE), border_radius=20),
            ft.Container(
                width=280, height=2, bgcolor=RED_ERROR,
                animate_offset=ft.animation.Animation(1500, ft.AnimationCurve.EASE_IN_OUT)
            )
        ], alignment="center"),
        margin=ft.margin.only(top=20, bottom=20)
    )

# --- 5. ESTILOS DE BOTÕES ---
BTN_MAIN = ft.ButtonStyle(
    color=WHITE, bgcolor=PRIMARY_BLUE, 
    shape=ft.RoundedRectangleBorder(radius=15), elevation=5
)

BTN_SPECIAL = ft.ButtonStyle(
    color=WHITE, bgcolor=ACCENT_ORANGE, 
    shape=ft.RoundedRectangleBorder(radius=15)
)