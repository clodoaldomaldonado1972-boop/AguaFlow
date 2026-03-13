import leitor_ocr
import os
import glob

# Busca imagens
extensoes = ["*.jpg", "*.jpeg", "*.png"]
fotos = []
for ext in extensoes:
    fotos.extend(glob.glob(ext))

# Filtra imagens de diagnóstico e de sistema
fotos = [f for f in fotos if "visao_" not in f and "logo" not in f]

print(f"\n{'='*60}")
print(f"🚀 SISTEMA ÁGUA FLOW - IDENTIFICAÇÃO + CONSUMO")
print(f"{'='*60}")

if fotos:
    for arquivo in fotos:
        print(f"\n📸 ANALISANDO: {arquivo}")

        # Agora recebemos dois valores: Apto (do QR Code) e Leitura (do Visor)
        apto, leitura = leitor_ocr.extrair_dados_fluxo(arquivo)

        # Exibição organizada dos resultados
        print(f"📍 UNIDADE: {apto}")

        if leitura:
            print(f"✅ CONSUMO: {leitura} m³")
        else:
            print(f"❌ CONSUMO: Não foi possível extrair os 6 dígitos do visor.")

    print(f"\n{'='*60}")
    print(f"✨ Processamento de {len(fotos)} imagens finalizado.")
    print(f"{'='*60}")
else:
    print("⚠️ Nenhuma imagem encontrada para teste na pasta C:\\ÁguaFlow")
