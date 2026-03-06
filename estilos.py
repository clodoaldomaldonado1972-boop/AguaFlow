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
        label=texto,          # CORREÇÃO: No FilledButton o certo é 'label'
        icon="save",
        on_click=acao,
        style=ft.ButtonStyle(bgcolor=COR_SUCESSO, color=COR_BRANCO),
        expand=True
    )

def botao_texto(texto, acao, icone="exit_to_app"):
    return ft.TextButton(
        text=texto,           # No TextButton o argumento é 'text' (é confuso, eu sei!)
        icon=icone,
        icon_color=COR_TEXTO_SEC,
        on_click=acao
    )