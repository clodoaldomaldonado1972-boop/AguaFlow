import leitor_ocr
import os
import glob

extensoes = ["*.jpg", "*.jpeg", "*.png"]
fotos = []
for ext in extensoes:
    fotos.extend(glob.glob(ext))

fotos = [f for f in fotos if "visao_do_robo" not in f]

if fotos:
    print(f"--- 🚀 Iniciando teste em {len(fotos)} imagens ---")
    for arquivo in fotos:
        print(f"📸 Analisando: {arquivo}")
        # Aqui ele chama a função que está lá no outro arquivo
        resultado = leitor_ocr.extrair_dados_fluxo(arquivo)
        if resultado:
            print(f"✅ LEITURA: {resultado}")
        else:
            print("❌ Falha na leitura.")

else:  # No loop do teste, mude a forma de exibir o resultado:
    if resultado and len(resultado) >= 4:  # Ignora leituras muito curtas (ruído)
        # Remove quebras de linha para o resultado ficar em uma linha só
        limpo = resultado.replace("\n", " ").strip()
        print(f"✅ LEITURA: {limpo}")
    elif resultado:
        print(f"⚠️ LEITURA DUVIDOSA (Muito curta): {resultado}")
    else:
        print("❌ Falha na leitura.")
