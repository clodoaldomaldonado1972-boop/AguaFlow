import flet as ft
import asyncio

# --- 1. CORES BASE ---
BG_DARK = "#121417"
PRIMARY_BLUE = "#2196F3"
WHITE = "#FFFFFF"
GREY_TEXT = "#BDBDBD"
ACCENT_ORANGE = "#FF9800"
RED_ERROR = "#FF5252"
SUCCESS_GREEN = "#2E7D32"

BG_LIGHT = "#FAFAFA"


def get_bgcolor(page):
    if page is None or not hasattr(page, "theme_mode"):
        return BG_DARK
    return BG_DARK if page.theme_mode == ft.ThemeMode.DARK else BG_LIGHT


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

# --- 3. ESTILOS ---


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

# --- 4. ELEMENTOS VISUAIS (ATUALIZADO COM ANIMAÇÃO) ---


def criar_mira_scanner():
    # A linha vermelha agora começa no topo (-100 unidades de offset vertical)
    linha_scanner = ft.Container(
        width=280,
        height=2,
        bgcolor=RED_ERROR,
        offset=ft.Offset(0, -2.5),
        animate_offset=ft.Animation(
            1500, ft.AnimationCurve.EASE_IN_OUT)
    )

    # Função interna para gerenciar o movimento infinito da linha
    async def animar_linha():
        while True:
            await asyncio.sleep(0.1)
            # Alterna entre o topo e a base do container azul
            linha_scanner.offset = ft.Offset(
                0, 2.5) if linha_scanner.offset.y == -2.5 else ft.Offset(0, -2.5)
            try:
                linha_scanner.update()
            except:
                break  # Para a animação se a tela for fechada
            await asyncio.sleep(1.5)

    # Dispara a animação em background (só funciona dentro do loop de eventos do Flet)
    try:
        asyncio.get_running_loop()
        asyncio.create_task(animar_linha())
    except RuntimeError:
        pass

    return ft.Container(
        content=ft.Stack([
            # Moldura azul do scanner[cite: 7]
            ft.Container(width=300, height=220, border=ft.border.all(
                2, PRIMARY_BLUE), border_radius=20),
            linha_scanner
        ], alignment="center"),
        margin=ft.Margin.only(top=20, bottom=20)
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


def criar_card_metrica(titulo, valor, icone, cor, col=3):
    return ft.Container(
        col=col,
        content=ft.Column([
            ft.Icon(icone, color=cor, size=28),
            ft.Text(valor, size=22, weight="bold", color=WHITE),
            ft.Text(titulo, size=12, color=GREY_TEXT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
        bgcolor="#1E2126",
        border_radius=12,
        padding=16,
    )

