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

def criar_mira_scanner():
    """
    Cria o Viewfinder com a linha horizontal vermelha animada (Laser).
    """
    # A LINHA VERMELHA (LASER)
    linha_laser = ft.Container(
        width=260,
        height=3,
        bgcolor=ft.colors.RED_ACCENT_400,
        border_radius=5,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.RED_600),
        offset=ft.Offset(0, 0),
        # Animação de 1.5 segundos para o movimento
        animate_offset=ft.animation.Animation(1500, ft.AnimationCurve.EASE_IN_OUT),
    )

    # O QUADRO DA MIRA
    mira_container = ft.Container(
        width=300,
        height=250,
        border=ft.border.all(2, ACCENT_ORANGE),
        border_radius=20,
        bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE),
        alignment=ft.alignment.top_center,
        padding=ft.padding.only(top=20),
        content=ft.Stack([
            linha_laser
        ])
    )

    # Motor da Mira: Faz a linha descer e subir infinitamente
    async def animar_laser():
        while True:
            try:
                await asyncio.sleep(1.6)
                linha_laser.offset = ft.Offset(0, 70) # Desce
                linha_laser.update()
                await asyncio.sleep(1.6)
                linha_laser.offset = ft.Offset(0, 0)  # Sobe
                linha_laser.update()
            except:
                break # Para a animação se o componente for destruído

    # Inicia a animação quando o controle é renderizado/tocado
    mira_container.on_click = lambda _: asyncio.create_task(animar_laser())
    
    return mira_container

def campo_estilo(label, icon_name, password=False, read_only=False, keyboard_type=None, on_submit=None):
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
        read_only=read_only,
        keyboard_type=keyboard_type if keyboard_type else ft.KeyboardType.TEXT
    )