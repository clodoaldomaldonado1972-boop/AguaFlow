import flet as ft


def adicionar_sons(page: ft.Page):
    """
    Carrega os bipes de alerta e sucesso no overlay da página.
    """
    # URLs de bipes curtos (padrão MP3)
    som_alerta = ft.Audio(
        src="https://lasonotheque.org/upload/mp3/0034.mp3",
        autoplay=False
    )

    som_sucesso = ft.Audio(
        src="https://lasonotheque.org/upload/mp3/0504.mp3",
        autoplay=False
    )

    # Adiciona ao overlay (obrigatório no Flet para áudio funcionar)
    page.overlay.append(som_alerta)
    page.overlay.append(som_sucesso)

    page.update()

    return som_alerta, som_sucesso
