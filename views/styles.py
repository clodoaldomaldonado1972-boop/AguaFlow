import flet as ft
import asyncio

# --- 1. CORES BASE — Paleta AguaFlow Brand (guia ov9ngi) ---
AGUA_BLUE = "#2255FE"   # azul elétrico — cor primária
FLOW_ORANGE = "#FFA360"   # laranja quente — cor secundária
GOLDEN = "#FFE060"   # dourado — acento no gradiente da chama

BG_DARK = "#0E1628"      # navy escuro — dark mode
BG_LIGHT = "#FFFFFF"      # branco puro — light mode

# Aliases de compatibilidade com o resto do projeto
PRIMARY_BLUE = AGUA_BLUE
ACCENT_ORANGE = FLOW_ORANGE
WHITE = "#FFFFFF"
GREY_TEXT = "#BDBDBD"
RED_ERROR = "#FF5252"
SUCCESS_GREEN = "#2E7D32"


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


def criar_mira_scanner(page=None, border_color=None):
    # Spacer animado empurra a linha de cima para baixo dentro do box de 220px.
    # height: 0 → linha no topo; height: 218 → linha na base (218+2=220).
    spacer_topo = ft.Container(
        height=0,
        animate=ft.Animation(1500, ft.AnimationCurve.EASE_IN_OUT),
    )
    linha_scanner = ft.Container(width=300, height=2, bgcolor=RED_ERROR)
    _direcao = [True]  # True = descendo

    async def animar_linha():
        while True:
            await asyncio.sleep(0.1)
            spacer_topo.height = 218 if _direcao[0] else 0
            _direcao[0] = not _direcao[0]
            try:
                if page:
                    page.update()
                else:
                    spacer_topo.update()
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
        height=240,
        content=ft.Container(
            width=300, height=220,
            border=ft.border.all(3, border_color or PRIMARY_BLUE),
            border_radius=20,
            content=ft.Column([spacer_topo, linha_scanner], spacing=0),
        ),
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


def logo_aguaflow(size: int = 90) -> ft.Image:
    """Logo AguaFlow — imagem paisagem 3054×1408, size = altura."""
    return ft.Image(
        src="logo.png",
        width=int(size * 2.17),
        height=size,
        fit=ft.BoxFit.CONTAIN,
    )


def logo_aguaflow_com_texto(size: int = 90, text_size: int = 30) -> ft.Image:
    """Logo AguaFlow com texto já embutido na imagem."""
    return logo_aguaflow(size)


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
