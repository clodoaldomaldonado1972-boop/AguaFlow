import leitor_ocr
import os
import glob
from datetime import datetime

# 1. Configuração inicial
extensoes = ["*.jpg", "*.jpeg", "*.png"]
fotos = []
for ext in extensoes:
    fotos.extend(glob.glob(ext))

# Filtra imagens de sistema
fotos = [f for f in fotos if "visao_" not in f and "logo" not in f]

# Nome do arquivo de relatório com a data de hoje
data_atual = datetime.now().strftime("%d-%m-%Y_%H-%M")
nome_relatorio = f"relatorio_leituras_{data_atual}.txt"

print(f"\n🚀 INICIANDO PROCESSAMENTO - {len(fotos)} IMAGENS")

# 2. Abre o arquivo para escrita (o 'with' garante que o arquivo seja fechado ao final)
with open(nome_relatorio, "w", encoding="utf-8") as f:
    f.write(f"=== RELATÓRIO ÁGUA FLOW - VIVERE PRUDENTE ===\n")
    f.write(
        f"Data do Processamento: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    f.write(f"{'='*45}\n\n")

    for arquivo in fotos:
        print(f"🔍 Lendo: {arquivo}...", end=" ", flush=True)

        apto, leitura = leitor_ocr.extrair_dados_fluxo(arquivo)

        if leitura:
            status = "SUCESSO"
            info = f"Unidade: {apto} | Consumo: {leitura} m³"
            print(f"✅ {leitura} m³")
        else:
            status = "FALHA"
            info = f"Unidade: {apto} | Consumo: Não identificado"
            print(f"❌ Falha")

        # Escreve no arquivo TXT
        f.write(f"[{status}] Foto: {arquivo}\n")
        f.write(f" -> {info}\n")
        f.write(f"{'-'*45}\n")

print(f"\n{'='*50}")
print(f"✨ Concluído! Relatório salvo como: {nome_relatorio}")
print(f"{'='*50}")
