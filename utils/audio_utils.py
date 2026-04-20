import winsound
import os

def tocar_alerta(tipo="sucesso"):
    """
    Tenta tocar o arquivo físico conforme o tipo de evento.
    - Se falhar ou for um formato não suportado pelo winsound, 
      utiliza o Beep do Windows como fallback.
    """
    # 1. Definição de caminhos e parâmetros de fallback
    if tipo == "sucesso":
        # Som agudo e curto para confirmação
        caminho_audio = "assets/audio/sucesso.wav"
        frequencia, duracao = 1000, 300 
    elif tipo == "erro":
        # Som grave e longo para erro/atenção
        caminho_audio = "assets/audio/erro.wav"
        frequencia, duracao = 400, 600  
    else:
        # Alerta padrão
        caminho_audio = "assets/audio/alerta.wav"
        frequencia, duracao = 800, 400

    # 2. Lógica de Execução
    if os.path.exists(caminho_audio):
        try:
            # SND_FILENAME: identifica que é um arquivo
            # SND_ASYNC: permite que o som toque sem travar a interface (UI) do Flet
            winsound.PlaySound(
                caminho_audio, 
                winsound.SND_FILENAME | winsound.SND_ASYNC
            )
        except Exception as e:
            print(f"[AUDIO] Erro ao reproduzir arquivo: {e}")
            # Fallback para Beep do sistema
            winsound.Beep(frequencia, duracao)
    else:
        # Se os arquivos de áudio não estiverem na pasta assets, usa o Beep
        winsound.Beep(frequencia, duracao)