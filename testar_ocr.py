import leitor_ocr
import os
import glob

# 1. Busca automaticamente por arquivos de imagem na pasta
extensoes = ["*.jpg", "*.jpeg", "*.png"]
fotos = []
for ext in extensoes:
    fotos.extend(glob.glob(ext))

if fotos:
    # Pega a primeira foto encontrada para o teste
    arquivo_para_teste = fotos[0]
    print(f"--- 📸 Foto encontrada: {arquivo_para_teste} ---")

    # Chama o nosso motor de leitura otimizado
    resultado = leitor_ocr.extrair_dados_fluxo(arquivo_para_teste)

    if resultado:
        print(f"✅ LEITURA: {resultado}")
    else:
        print("❌ Não foi possível extrair números desta imagem.")
else:
    print("⚠️ Nenhuma foto (.jpg, .jpeg, .png) encontrada na pasta C:\ÁguaFlow")
    print("Dica: Arraste uma foto para dentro da pasta do projeto no VS Code.")
