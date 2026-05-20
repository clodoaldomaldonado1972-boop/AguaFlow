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


def criar_mira_scanner(page=None):
    # Offset inicial: topo do box de 220px. Fração da altura da linha (2px): 220/2/2 = 55
    linha_scanner = ft.Container(
        width=280,
        height=2,
        bgcolor=RED_ERROR,
        offset=ft.Offset(0, -55),
        animate_offset=ft.Animation(1500, ft.AnimationCurve.EASE_IN_OUT),
    )

    async def animar_linha():
        while True:
            await asyncio.sleep(0.1)
            # Alterna entre topo (-110px) e base (+110px) do box de 220px
            linha_scanner.offset = (
                ft.Offset(0, 55) if linha_scanner.offset.y < 0 else ft.Offset(0, -55)
            )
            try:
                if page:
                    page.update()
                else:
                    linha_scanner.update()
            except Exception:
                break
            await asyncio.sleep(1.5)

    try:
        if page:
            page.run_task(animar_linha)
        else:
            asyncio.get_running_loop()
            asyncio.create_task(animar_linha())
    except RuntimeError:
        pass

    return ft.Container(
        width=300,
        height=260,
        content=ft.Stack([
            ft.Container(
                width=300, height=220,
                border=ft.border.all(2, PRIMARY_BLUE),
                border_radius=20,
            ),
            linha_scanner,
        ], alignment="center"),
        margin=ft.Margin.only(top=10, bottom=10),
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

