import flet as ft


def adicionar_sons(page: ft.Page):
    """Inicializa e carrega os sons no overlay da página."""

    # Bipe de Alerta (Esquecimento/Erro)
    som_alerta = ft.Audio(
        src="https://www.soundjay.com/buttons/beep-07a.mp3",
        autoplay=False
    )

    # Som de Sucesso (Conclusão de leitura/OCR)
    som_sucesso = ft.Audio(
        src="https://www.soundjay.com/buttons/button-37.mp3",
        autoplay=False
    )

    page.overlay.extend([som_alerta, som_sucesso])
    page.update()

    return som_alerta, som_sucesso
