import flet as ft

def tocar_alerta(page: ft.Page, tipo="sucesso"):
    """
    No APK, a 'frequência' é substituída pela escolha do arquivo 
    de áudio correspondente ao evento.
    """
    # Em vez de calcular frequência/duração, selecionamos o arquivo gravado
    if tipo == "sucesso":
        caminho_audio = "audio/sucesso.wav"  # Grave um som de 1000Hz aqui
    elif tipo == "erro":
        caminho_audio = "audio/erro.wav"     # Grave um som de 400Hz aqui
    else:
        caminho_audio = "audio/alerta.wav"

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