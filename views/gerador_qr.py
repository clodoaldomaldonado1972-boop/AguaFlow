import qrcode
from fpdf import FPDF
import os

# --- CONFIGURAÇÕES DE LAYOUT ---
COLUNAS = 5
LINHAS = 8
NOME_CONDOMINIO = "Vivere Prudente"

def gerar_qr_codes(filtro_tipo="AMBOS"):
    # 1. CRIAÇÃO DO OBJETO PDF (Define 'pdf' antes de usar)
    pdf = FPDF()
    pdf.set_auto_page_break(False) # Agora 'pdf' existe, não dará erro
    pdf.add_page()
    
    lista_impressao = []

    # 2. LÓGICA DE LOOP (16 -> 1)
    for andar in range(16, 0, -1):
        for final in range(6, 0, -1):
            unidade = f"{andar}{final}"
            if filtro_tipo in ["AGUA", "AMBOS"]:
                lista_impressao.append({"id": unidade, "tipo": "ÁGUA", "payload": f"{unidade}-AGUA"})
            if filtro_tipo in ["GAS", "AMBOS"]:
                lista_impressao.append({"id": unidade, "tipo": "GÁS", "payload": f"{unidade}-GAS"})

    if filtro_tipo in ["GAS", "AMBOS"]:
        lista_impressao.append({"id": "LAZER", "tipo": "GÁS", "payload": "LAZER-GAS"})
    if filtro_tipo in ["AGUA", "AMBOS"]:
        lista_impressao.append({"id": "GERAL", "tipo": "ÁGUA", "payload": "GERAL-AGUA"})

    # 3. CÁLCULOS DE MARGENS E GRADE
    margem_x = 10
    margem_y = 15
    w_cel = 190 / COLUNAS
    h_cel = 267 / LINHAS

    for i, item in enumerate(lista_impressao):
        # QUEBRA DE PÁGINA MANUAL (A cada 40 itens)
        if i > 0 and i % (COLUNAS * LINHAS) == 0:
            pdf.add_page()

        idx_na_pagina = i % (COLUNAS * LINHAS)
        col = idx_na_pagina % COLUNAS
        row = idx_na_pagina // COLUNAS
        
        x = margem_x + (col * w_cel)
        y = margem_y + (row * h_cel)

        # GERAR QR TEMPORÁRIO
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(item['payload'])
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        temp_img = f"temp_{i}.png"
        img_qr.save(temp_img)

        # DESENHO DA ETIQUETA
        pdf.set_draw_color(200, 200, 200) 
        pdf.rect(x, y, w_cel, h_cel)

        # Imagem do QR (Centralizada e menor para não encavalar)
        qr_size = w_cel * 0.55
        pdf.image(temp_img, x + (w_cel - qr_size)/2, y + 3, qr_size)

        # Texto Condomínio
        pdf.set_text_color(100, 100, 100)
        pdf.set_font("helvetica", "B", 6)
        pdf.set_xy(x, y + h_cel - 9) 
        pdf.cell(w_cel, 3, NOME_CONDOMINIO, align='C')

        # Texto Unidade - Tipo
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_xy(x, y + h_cel - 6) 
        pdf.cell(w_cel, 5, f"{item['id']} - {item['tipo']}", align='C')

        os.remove(temp_img)

    nome_output = f"Etiquetas_Vivere_{filtro_tipo}.pdf"
    pdf.output(nome_output)
    print(f"\n✅ PDF Gerado com sucesso: {nome_output}")

if __name__ == "__main__":
    opcao = input("Gerar: AGUA, GAS ou AMBOS? ").strip().upper()
    if opcao in ["AGUA", "GAS", "AMBOS"]:
        gerar_qr_codes(opcao)
    else:
        print("Opção inválida!")