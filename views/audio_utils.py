import flet as ft
import flet_audio as ft_audio


def adicionar_sons(page: ft.Page):
    # Usando o novo pacote flet_audio
    som_alerta = ft_audio.Audio(
        src="audios/alerta.mp3", autoplay=False
    )
    som_sucesso = ft_audio.Audio(
        src="audios/sucesso.mp3", autoplay=False
    )

    page.overlay.append(som_alerta)
    page.overlay.append(som_sucesso)

    # Retornamos as funções para tocar os sons
    return som_alerta, som_sucesso
