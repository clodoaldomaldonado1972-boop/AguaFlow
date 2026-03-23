import leitor_ocr
import sys
import os


def testar():
    # Procura pela foto mais recente tirada ou um nome padrão
    arquivo = "meu_teste.jpg"

    if not os.path.exists(arquivo):
        print(
            f"❌ Erro: Coloque a foto com o nome '{arquivo}' na pasta do projeto.")
        return

    print(f"🔍 Analisando {arquivo}...")
    unidade, consumo = leitor_ocr.extrair_dados_fluxo(arquivo)

    print("\n" + "="*30)
    print(f"📍 UNIDADE DETECTADA: {unidade}")
    print(f"💧 CONSUMO DETECTADO: {consumo} m³")
    print("="*30)
    print("\n👀 Verifique o arquivo 'visao_do_visor.png' para ver como o robô 'enxergou' os números.")


if __name__ == "__main__":
    testar()
