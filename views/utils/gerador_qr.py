import qrcode
from fpdf2 import FPDF  # Use apenas fpdf2
import os

# --- CONFIGURAÇÕES DE LAYOUT ---
COLUNAS = 5
LINHAS = 8
NOME_CONDOMINIO = "Vivere Prudente"

def gerar_qr_codes(filtro_tipo="AMBOS"):
    """Gera o PDF de etiquetas para o condomínio."""
    pdf = FPDF()
    pdf.set_auto_page_break(False)
    pdf.add_page()
    
    lista_impressao = []

    # 1. GERAÇÃO DA LISTA (Andares 16 ao 1)
    for andar in range(16, 0, -1):
        for final in range(6, 0, -1):
            unidade = f"{andar}{final}"
            if filtro_tipo in ["AGUA", "AMBOS"]:
                lista_impressao.append({"id": unidade, "tipo": "AGUA", "payload": f"{unidade}-AGUA"})
            if filtro_tipo in ["GAS", "AMBOS"]:
                lista_impressao.append({"id": unidade, "tipo": "GAS", "payload": f"{unidade}-GAS"})

    # Áreas Especiais
    if filtro_tipo in ["GAS", "AMBOS"]:
        lista_impressao.append({"id": "LAZER", "tipo": "GAS", "payload": "LAZER-GAS"})
    if filtro_tipo in ["AGUA", "AMBOS"]:
        lista_impressao.append({"id": "GERAL", "tipo": "AGUA", "payload": "GERAL-AGUA"})

    # 2. CÁLCULOS DE POSICIONAMENTO (A4 Padrão)
    margem_x, margem_y = 10, 10
    w_cel = 190 / COLUNAS
    h_cel = 277 / LINHAS 

    print(f"📄 Criando {len(lista_impressao)} etiquetas...")

    for i, item in enumerate(lista_impressao):
        if i > 0 and i % (COLUNAS * LINHAS) == 0:
            pdf.add_page()

        idx = i % (COLUNAS * LINHAS)
        col, row = idx % COLUNAS, idx // COLUNAS
        x, y = margem_x + (col * w_cel), margem_y + (row * h_cel)

        # 3. GERAR QR CODE
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(item['payload'])
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        # Salva com nome único para evitar conflito de acesso ao arquivo
        temp_img = f"temp_qr_{item['payload']}.png"
        img_qr.save(temp_img)

        # 4. DESENHO DA ETIQUETA
        pdf.set_draw_color(200, 200, 200) 
        pdf.rect(x, y, w_cel, h_cel)

        qr_size = w_cel * 0.7
        pdf.image(temp_img, x + (w_cel - qr_size)/2, y + 5, qr_size)

        # Texto da Unidade (Zelador precisa ler de longe)
        pdf.set_font("helvetica", "B", 11)
        pdf.set_xy(x, y + h_cel - 10) 
        pdf.cell(w_cel, 5, f"{item['id']} - {item['tipo']}", align='C')

        # Nome do Condomínio (Rodapé discreto)
        pdf.set_font("helvetica", "", 7)
        pdf.set_xy(x, y + h_cel - 5) 
        pdf.cell(w_cel, 4, NOME_CONDOMINIO, align='C')

        # Limpeza
        os.remove(temp_img)

    nome_output = f"Etiquetas_AguaFlow_{filtro_tipo}.pdf"
    pdf.output(nome_output)
    print(f"✅ Arquivo '{nome_output}' gerado com sucesso!")

if __name__ == "__main__":
    gerar_qr_codes("AMBOS")