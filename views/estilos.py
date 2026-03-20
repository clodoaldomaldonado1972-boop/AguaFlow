import flet as ft

# --- CORES DO SISTEMA ---
COR_PRIMARIA = "#005b96"  # Azul ÁguaFlow
COR_SUCESSO  = "#2e7d32"  # Verde para Salvar/Concluído
COR_ALERTA   = "#d32f2f"  # Vermelho para Pular/Consumo Alto
COR_TEXTO_SEC = "#757575" # Cinza para textos menores
COR_BRANCO   = "#ffffff"

# --- TAMANHOS E ESTILOS ---
FONTE_TITULO = 30
FONTE_LABEL  = 16

# --- COMPONENTES PADRONIZADOS ---
def botao_salvar(texto, acao):
    return ft.FilledButton(
        content=ft.Row(
            controls=[
                ft.Icon("save", color="white"),
                ft.Text(texto, color="white", weight="bold"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True, # Adicione isso para o botão não tentar ocupar a largura toda
        ),
        on_click=acao,
        style=ft.ButtonStyle(bgcolor=COR_SUCESSO),
        # expand=True  <-- REMOVA OU COMENTE ESTA LINHA
    )

def botao_texto(texto, acao, icone="exit_to_app"):
    return ft.TextButton(
        content=ft.Row(
            controls=[
                ft.Icon(icone, color=COR_TEXTO_SEC),
                ft.Text(texto, color=COR_TEXTO_SEC),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        on_click=acao
    )