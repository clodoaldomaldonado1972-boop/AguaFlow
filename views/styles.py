import flet as ft
import asyncio

# --- PALETA DE CORES (Nomes novos + Sinônimos para evitar ImportError) ---
BG_DARK = "#121417"
BG_COLOR = BG_DARK
PRIMARY_BLUE = "#2196F3"
PRIMARY_COLOR = PRIMARY_BLUE
DARK_BLUE = "#1976D2"

# Cores de texto forçadas para alto contraste
WHITE = "#FFFFFF" 
GREY_TEXT = "#BDBDBD" 
GREY = GREY_TEXT  # Mantido para compatibilidade com outros arquivos

ACCENT_ORANGE = "#FF9800"
SUCCESS_GREEN = "#4CAF50"
ERROR_COLOR = "#FF5252"

# --- CONFIGURAÇÕES DE PÁGINA ---
STYLE_PAGE_CONTAINER = {
    "padding": 20,
    "alignment": ft.Alignment(0, 0),
    "expand": True,
    "bgcolor": BG_DARK
}

# --- ESTILOS DE TEXTO (Aumentados para melhor leitura no APK) ---
TEXT_TITLE = ft.TextStyle(
    size=28, 
    weight=ft.FontWeight.BOLD, 
    color=WHITE
)

TEXT_SUB = ft.TextStyle(
    size=16, 
    color=GREY_TEXT
)

TEXT_LABEL = ft.TextStyle(
    size=14, 
    weight=ft.FontWeight.W_500, 
    color=PRIMARY_BLUE
)

# --- ESTILOS DE BOTÕES ---
# --- ESTILOS DE BOTÕES ---
BTN_MAIN = ft.ButtonStyle(
    color=WHITE,
    bgcolor={
        ft.ControlState.DEFAULT: PRIMARY_BLUE,
        ft.ControlState.HOVERED: DARK_BLUE, # Mudei para HOVERED para fazer sentido
    },
    padding=20,
    shape=ft.RoundedRectangleBorder(radius=15),
    elevation={"pressed": 0, "": 5},
)

BTN_SPECIAL = ft.ButtonStyle(
    color=WHITE,
    bgcolor={
        ft.ControlState.DEFAULT: ACCENT_ORANGE, # Corrigido: removido o ":" extra
        ft.ControlState.PRESSED: "#E68A00",
    },
    padding=20,
    shape=ft.RoundedRectangleBorder(radius=15),
)
BTN_PRIMARY = ft.ButtonStyle(
    color=WHITE,
    bgcolor={
        ft.ControlState.DEFAULT: PRIMARY_BLUE,
        ft.ControlState.PRESSED: DARK_BLUE,
    },
    shape=ft.RoundedRectangleBorder(radius=10),
)

# --- COMPONENTES ---

def campo_estilo(label, icon_name, password=False, read_only=False, keyboard_type=None, on_submit=None):
    """Campo de texto com cores forçadas para evitar sumir no Android."""
    return ft.TextField(
        label=label,
        prefix_icon=icon_name,
        password=password,
        can_reveal_password=True,
        read_only=read_only,
        keyboard_type=keyboard_type if keyboard_type else ft.KeyboardType.TEXT,
        border_color=PRIMARY_BLUE,
        focused_border_color=ACCENT_ORANGE,
        border_radius=12,
        color=WHITE, 
        label_style=ft.TextStyle(color=GREY_TEXT),
        bgcolor=ft.colors.with_opacity(0.1, WHITE),
        content_padding=15,
        on_submit=on_submit
    )

def card_informativo(titulo, valor, icone, cor=PRIMARY_BLUE):
    """Card de Dashboard com alto contraste."""
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(icone, color=cor, size=20), 
                ft.Text(titulo, size=12, color=GREY_TEXT)
            ]),
            ft.Text(valor, size=24, weight=ft.FontWeight.BOLD, color=WHITE)
        ], spacing=5),
        padding=15,
        bgcolor="#1E2126",
        border_radius=15,
        border=ft.border.all(1, ft.colors.with_opacity(0.1, WHITE)),
        width=170
    )