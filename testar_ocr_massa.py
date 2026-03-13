import leitor_ocr
import os
import glob


Busca imagens
extensoes = ["*.jpg", "*.jpeg", "*.png"]
fotos = []
for ext in extensoes:
    fotos.extend(glob.glob(ext))

fotos = [f for f in fotos if "visao_do_robo" not in f]

print(f"\n{'='*50}")
print(f"🚀 SISTEMA ÁGUA FLOW - TESTE EM MASSA")
print(f"{'='*50}")

if fotos:
    for arquivo in fotos:
        print(f"\n🔍 ARQUIVO: {arquivo}")
        resultado = leitor_ocr.extrair_dados_fluxo(arquivo)

        if resultado:
            print(f"✅ RESULTADO NA TELA: {resultado} m³")
        else:
            # Se o leitor_ocr retornar None, ele caiu na nossa trava de segurança
            print(f"❌ STATUS: Leitura inválida ou descartada (Ruído/Série)")

    print(f"\n{'='*50}")
    print(f"✨ Processamento de {len(fotos)} imagens finalizado.")
    print(f"{'='*50}")
else:
    print("⚠️ Nenhuma imagem encontrada para teste.")
