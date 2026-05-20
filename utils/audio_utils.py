import flet as ft
import os


def get_audio_path(nome_audio: str) -> str:
    """Retorna o caminho relativo para arquivos de áudio compatível com APK."""
    # Usa path relativo para funcionar tanto no desktop quanto no APK
    return os.path.join("assets", "audio", nome_audio)


def tocar_alerta(page: ft.Page, tipo="sucesso"):
    """
    Toca áudio de feedback sonoro usando ft.Audio nativo do Flet (compatível APK)
    e exibe uma SnackBar para feedback visual na interface.
    """
    # OTIMIZAÇÃO: Remove áudios anteriores do overlay para evitar vazamento de memória
    if hasattr(ft, 'Audio'):
        for control in page.overlay[:]:
            if isinstance(control, ft.Audio):
                page.overlay.remove(control)

    # Configurações de feedback visual (SnackBar) e sonoro (Audio)
    if tipo == "sucesso":
        nome_arquivo = "sucesso.wav"
        mensagem = "✅ Operação concluída com sucesso!"
        cor = "green700"
    elif tipo == "erro":
        nome_arquivo = "erro.wav"
        mensagem = "❌ Erro ao processar solicitação."
        cor = "red700"
    else:
        nome_arquivo = "alerta.wav"
        mensagem = "⚠️ Atenção: Verifique as informações."
        cor = "orange700"

    caminho_audio = get_audio_path(nome_arquivo)

    # Feedback visual
    page.open(ft.SnackBar(content=ft.Text(mensagem, color="white"), bgcolor=cor))

    # Feedback sonoro (ft.Audio removido no Flet 0.84+; falha silenciosa)
    page.update()
    try:
        audio = ft.Audio(src=caminho_audio, autoplay=False)
        page.overlay.append(audio)
        page.update()
        audio.play()
    except (AttributeError, Exception):
        # Erros de áudio não devem disparar report de e-mail por não serem fatais
        pass
