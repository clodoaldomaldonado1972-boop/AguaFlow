import qrcode
from fpdf import FPDF
import os

# --- CONFIGURAÇÕES DE LAYOUT ---
COLUNAS = 4
LINHAS = 5
NOME_CONDOMINIO = "Vivere Prudente"


def gerar_qr_codes(filtro_tipo="AMBOS"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 8)

    # Definição das Unidades
    aptos = [f"Apto {i}" for i in range(11, 165)]
    gerais = ["Medidor Geral"]  # Nome que sairá na etiqueta Geral
    lazer_unico = ["Área de Lazer"]

    lista_impressao = []

    # 1. Lógica para Apartamentos (Água e Gás)
    for a in aptos:
        if filtro_tipo in ["AGUA", "AMBOS"]:
            lista_impressao.append((a, "AGUA"))
        if filtro_tipo in ["GAS", "AMBOS"]:
            lista_impressao.append((a, "GAS"))

    # 2. Lógica para Geral (Somente Água)
    if filtro_tipo in ["AGUA", "AMBOS"]:
        for g in gerais:
            lista_impressao.append((g, "AGUA"))

    # 3. Lógica para Lazer (Somente UM medidor de Gás)
    if filtro_tipo in ["GAS", "AMBOS"]:
        for l in lazer_unico:
            lista_impressao.append((l, "GAS"))

    # Cálculos de Grade
    largura_util = 190
    altura_util = 277
    w_cel = largura_util / COLUNAS
    h_cel = altura_util / LINHAS

    for i, (nome, tipo) in enumerate(lista_impressao):
        # Quebra de página automática a cada 20 etiquetas (4x5)
        if i > 0 and i % (COLUNAS * LINHAS) == 0:
            pdf.add_page()

        col = (i % (COLUNAS * LINHAS)) % COLUNAS
        row = (i % (COLUNAS * LINHAS)) // COLUNAS
        x = 10 + (col * w_cel)
        y = 10 + (row * h_cel)

        # Dados do QR Code
        qr_payload = f"CONDO:{NOME_CONDOMINIO}|ID:{nome}|TIPO:{tipo}"
        qr = qrcode.make(qr_payload)
        temp_img = f"temp_{i}.png"
        qr.save(temp_img)

        # Desenho da Etiqueta
        pdf.rect(x, y, w_cel, h_cel)

        # QR Code - posicionado um pouco mais para cima
        pdf.image(temp_img, x + (w_cel*0.2), y + 3, w_cel*0.6)

        # Texto: Nome do Condomínio
        pdf.set_font("helvetica", "B", 7)
        pdf.set_xy(x, y + h_cel - 11)
        pdf.cell(w_cel, 4, NOME_CONDOMINIO, align='C')

        # Texto: Unidade e Tipo (Em destaque)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_xy(x, y + h_cel - 7)
        pdf.cell(w_cel, 5, f"{nome} - {tipo}", align='C')

        os.remove(temp_img)

    nome_arquivo = f"QR_Codes_{filtro_tipo}.pdf"
    pdf.output(nome_arquivo)
    print(
        f"✅ Sucesso! Geradas {len(lista_impressao)} etiquetas em '{nome_arquivo}'.")


if __name__ == "__main__":
    tipo = input("Gerar: AGUA, GAS ou AMBOS? ").upper()
    if tipo in ["AGUA", "GAS", "AMBOS"]:
        gerar_qr_codes(tipo)
    else:
        print("Opção inválida! Escolha AGUA, GAS ou AMBOS.")
