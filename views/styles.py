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
MAIN_COLOR = "blue"

# --- CONFIGURAÇÕES DE PÁGINA (STYLE_PAGE_CONTAINER) ---
STYLE_PAGE_CONTAINER = {
    "padding": 20,
    "alignment": ft.alignment.center,
    "expand": True,
    "bgcolor": BG_DARK
}

# --- ESTILOS DE TEXTO ---
TEXT_TITLE = ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=WHITE)
TEXT_SUB = ft.TextStyle(size=18, color=GREY)

# --- ESTILOS DE BOTÕES (RESOLVE O IMPORT ERROR) ---

# Estilo para botões principais (Azul)
BTN_MAIN = ft.ButtonStyle(
    color=WHITE,
    bgcolor=PRIMARY_BLUE,
    padding=20,
    shape=ft.RoundedRectangleBorder(radius=12),
)

# Estilo para botões de destaque/scanner (Laranja)
BTN_SPECIAL = ft.ButtonStyle(
    color=WHITE,
    bgcolor=ACCENT_ORANGE,
    padding=20,
    shape=ft.RoundedRectangleBorder(radius=12),
)

# --- COMPONENTES PADRONIZADOS ---

def campo_estilo(label, icon_name, password=False, on_submit=None, keyboard_type=None, read_only=False):
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
        cursor_color=PRIMARY_BLUE,
        read_only=read_only,
        keyboard_type=keyboard_type if keyboard_type else ft.KeyboardType.TEXT
    )

# --- A MIRA DO SCANNER (VIEWFINDER) ---
def criar_mira_scanner():
    """
    Cria um componente visual de 'mira' para orientar o utilizador 
    a centralizar o hidrómetro e o QR Code.
    """
    return ft.Container(
        width=300,
        height=250,
        border=ft.border.all(2, ACCENT_ORANGE),
        border_radius=20,
        alignment=ft.alignment.center,
        bgcolor=ft.colors.with_opacity(0.05, WHITE),
        content=ft.Stack([
            # Linha de Scan "Laser"
            ft.Container(
                width=280,
                height=2,
                bgcolor=ft.colors.with_opacity(0.4, ERROR_COLOR),
                top=125
            ),
            ft.Text(
                "POSICIONE O VISOR AQUI", 
                size=10, 
                color=ACCENT_ORANGE, 
                weight="bold",
                bottom=10,
                right=80
            )
        ])
    )