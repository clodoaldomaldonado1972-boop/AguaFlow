import qrcode
from fpdf import FPDF
import os

# --- CONFIGURAÇÕES DE LAYOUT (Ajustado para Folha A4 Padrão) ---
COLUNAS = 5
LINHAS = 8
NOME_CONDOMINIO = "Vivere Prudente"

def gerar_qr_codes(filtro_tipo="AMBOS"):
    """Gera um PDF formatado com QR Codes para colagem nos hidrômetros."""
    pdf = FPDF()
    pdf.set_auto_page_break(False)
    pdf.add_page()
    
    lista_impressao = []

    # 1. GERAÇÃO DA LISTA (Andares 16 ao 1 + Áreas Comuns)
    for andar in range(16, 0, -1):
        for final in range(6, 0, -1):
            unidade = f"{andar}{final}"
            # Adiciona Água e Gás separadamente se for AMBOS
            if filtro_tipo in ["AGUA", "AMBOS"]:
                lista_impressao.append({"id": unidade, "tipo": "AGUA", "payload": f"{unidade}-AGUA"})
            if filtro_tipo in ["GAS", "AMBOS"]:
                lista_impressao.append({"id": unidade, "tipo": "GAS", "payload": f"{unidade}-GAS"})

    # Adiciona itens especiais
    if filtro_tipo in ["GAS", "AMBOS"]:
        lista_impressao.append({"id": "LAZER", "tipo": "GAS", "payload": "LAZER-GAS"})
    if filtro_tipo in ["AGUA", "AMBOS"]:
        lista_impressao.append({"id": "GERAL", "tipo": "AGUA", "payload": "GERAL-AGUA"})

    # 2. CÁLCULOS DE POSICIONAMENTO
    margem_x = 10
    margem_y = 10
    w_cel = 190 / COLUNAS
    h_cel = 277 / LINHAS # Ajustado para preencher melhor a A4

    print(f"📄 Gerando {len(lista_impressao)} etiquetas...")

    for i, item in enumerate(lista_impressao):
        # Quebra de página automática
        if i > 0 and i % (COLUNAS * LINHAS) == 0:
            pdf.add_page()

        idx_na_pagina = i % (COLUNAS * LINHAS)
        col = idx_na_pagina % COLUNAS
        row = idx_na_pagina // COLUNAS
        
        x = margem_x + (col * w_cel)
        y = margem_y + (row * h_cel)

        # 3. GERAR QR CODE (Usa o payload para identificar unidade + tipo)
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(item['payload'])
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        temp_img = f"temp_qr_{i}.png"
        img_qr.save(temp_img)

        # 4. DESENHO DA ETIQUETA NO PDF
        # Moldura suave para guia de corte
        pdf.set_draw_color(220, 220, 220) 
        pdf.rect(x, y, w_cel, h_cel)

        # Inserção do QR Code
        qr_size = w_cel * 0.65 # Tamanho otimizado para leitura rápida
        pdf.image(temp_img, x + (w_cel - qr_size)/2, y + 4, qr_size)

        # Rodapé da Etiqueta: Condomínio
        pdf.set_text_color(120, 120, 120)
        pdf.set_font("helvetica", "B", 6)
        pdf.set_xy(x, y + h_cel - 10) 
        pdf.cell(w_cel, 3, NOME_CONDOMINIO, align='C')

        # Rodapé da Etiqueta: Unidade e Tipo (Em negrito para o zelador ler fácil)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_xy(x, y + h_cel - 7) 
        pdf.cell(w_cel, 5, f"{item['id']} - {item['tipo']}", align='C')

        # Limpeza imediata do arquivo temporário
        if os.path.exists(temp_img):
            os.remove(temp_img)

    # 5. SALVAMENTO FINAL
    nome_output = f"Etiquetas_AguaFlow_{filtro_tipo}.pdf"
    pdf.output(nome_output)
    print(f"✅ Sucesso! Arquivo '{nome_output}' pronto para impressão.")

if __name__ == "__main__":
    print("--- GERADOR DE ETIQUETAS AGUAFLOW ---")
    opcao = input("Deseja gerar etiquetas para: AGUA, GAS ou AMBOS? ").strip().upper()
    if opcao in ["AGUA", "GAS", "AMBOS"]:
        gerar_qr_codes(opcao)
    else:
        print("Opção inválida! Escolha entre AGUA, GAS ou AMBOS.")