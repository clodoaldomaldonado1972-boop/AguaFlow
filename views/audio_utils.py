import flet as ft


def adicionar_sons(page: ft.Page):
    # Tente esta forma (padrão das versões novas):
    som_alerta = ft.Audio(src="audio/alerta.mp3")
    # Se o erro persistir, use: ft.audio.Audio(src=...)

    # IMPORTANTE: No Flet novo, o áudio PRECISA estar no overlay
    # para não gerar aquela faixa vermelha de "Unknown control"
    return som_alerta, som_sucesso
