import flet as ft
import os

def get_audio_path(nome_audio: str) -> str:
    """Retorna o caminho relativo para arquivos de áudio compatível com APK."""
    # Usa path relativo para funcionar tanto no desktop quanto no APK
    return os.path.join("assets", "audio", nome_audio)

def tocar_alerta(page: ft.Page, tipo="sucesso"):
    """
    Toca áudio de feedback sonoro usando ft.Audio nativo do Flet (compatível APK).
    Os arquivos de áudio devem estar na pasta assets/audio/ do projeto.
    """
    # Seleciona o arquivo de áudio baseado no tipo de evento
    if tipo == "sucesso":
        nome_arquivo = "sucesso.wav"
    elif tipo == "erro":
        nome_arquivo = "erro.wav"
    else:
        nome_arquivo = "alerta.wav"

    caminho_audio = get_audio_path(nome_arquivo)

    # Criar o componente de áudio nativo do Flet (funciona no Android)
    audio = ft.Audio(
        src=caminho_audio,
        autoplay=False,
    )

    # Adicionar ao overlay da página (necessário para o Flet processar o som)
    if audio not in page.overlay:
        page.overlay.append(audio)

    page.update()

    try:
        audio.play()
    except Exception as e:
        print(f"Erro ao tocar som no Android: {e}")