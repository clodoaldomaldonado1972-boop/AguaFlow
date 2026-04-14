import winsound
import os

def tocar_alerta():
    """Tenta tocar o arquivo físico, se falhar, usa o Beep do Windows."""
    caminho_audio = "assets/audio/alerta.mp3"
    
    if os.path.exists(caminho_audio):
        try:
            # Toca o arquivo MP3 (SND_FILENAME toca o arquivo, SND_ASYNC não trava o app)
            import winsound
            winsound.PlaySound(caminho_audio, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            # Fallback caso o PlaySound falhe
            winsound.Beep(1000, 500)
    else:
        # Se o arquivo não existir, vai direto para o Beep
        winsound.Beep(1000, 500)