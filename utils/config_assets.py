import os

# Caminhos das imagens para facilitar o uso nas Views
class Assets:
    # Caminho base (opcional, o Flet já busca em /assets se configurado)
    LOGO = "logo_aguaflow.png"
    ICONE_AGUA = "icon_agua.png"
    ICONE_GAS = "icon_gas.png"
    BANNER_VIVERE = "vivere_prudente_banner.png"
    
    # Exemplo de verificação se os arquivos existem (bom para debug)
    @staticmethod
    def verificar_assets():
        if not os.path.exists("assets"):
            print("⚠️ Alerta: Pasta /assets não encontrada na raiz!")
        else:
            print("✅ Pasta /assets detectada.")

# Se rodar este arquivo sozinho, ele testa a pasta
if __name__ == "__main__":
    Assets.verificar_assets()