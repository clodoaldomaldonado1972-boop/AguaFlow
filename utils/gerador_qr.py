import os
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from database.database import Database

# --- CONFIGURAÇÕES DE LAYOUT ---
COLUNAS = 4
LINHAS = 6
NOME_CONDOMINIO = "Vivere Prudente"

def gerar_qr_codes(filtro_tipo="AMBOS", unidade_alvo=None):
    """
    Gera PDF de etiquetas consultando o banco de dados.
    Organiza em grade para evitar sobreposição.
    """
    print(f"\n[GERADOR] 🚀 Iniciando processo para: {unidade_alvo if unidade_alvo else 'TODOS'}")

    try:
        # 1. Configuração de Pastas e Caminho
        pasta_output = "storage"
        os.makedirs(pasta_output, exist_ok=True)
        
        sufixo = f"UNID_{unidade_alvo}" if unidade_alvo else "COMPLETO"
        nome_arquivo = f"Etiquetas_{filtro_tipo}_{sufixo}.pdf"
        caminho_final = os.path.join(pasta_output, nome_arquivo)

        # 2. Busca de Dados Reais no Banco
        # Database.get_unidades deve retornar [{'id': '101', 'tipo': 'AGUA', 'payload': '...'}, ...]
        unidades_db = Database.get_unidades() 
        
        if unidade_alvo:
            dados = [u for u in unidades_db if str(u['id']) == str(unidade_alvo)]
        else:
            dados = unidades_db

        if not dados:
            print("[GERADOR] ⚠️ Nenhuma unidade encontrada para gerar.")
            return None

        # 3. Inicialização do PDF
        c = canvas.Canvas(caminho_final, pagesize=A4)
        width_a4, height_a4 = A4

        # Configurações de tamanho da etiqueta (célula)
        margin_x = 30
        margin_y = 40
        w_cel = (width_a4 - (2 * margin_x)) / COLUNAS
        h_cel = (height_a4 - (2 * margin_y)) / LINHAS

        idx = 0
        for item in dados:
            # Controle de nova página
            if idx > 0 and idx % (COLUNAS * LINHAS) == 0:
                c.showPage()
            
            # Cálculo de Posição (Grade)
            pos_na_pagina = idx % (COLUNAS * LINHAS)
            col = pos_na_pagina % COLUNAS
            lin = pos_na_pagina // COLUNAS
            
            x = margin_x + (col * w_cel)
            y = (height_a4 - margin_y - h_cel) - (lin * h_cel)

            # --- DESENHO DA ETIQUETA ---
            # Borda da etiqueta
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x + 5, y + 5, w_cel - 10, h_cel - 10, stroke=1, fill=0)

            # Geração do QR Code em memória (BytesIO) para evitar lixo no disco
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            # O payload deve ser o que o scanner vai ler (ex: ID da unidade)
            payload = f"AGUAFLOW|{item['id']}|{item['tipo']}"
            qr.add_data(payload)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")

            temp_img = f"temp_qr_{idx}.png"
            img_qr.save(temp_img)

            # Desenha QR Code centralizado na parte superior da etiqueta
            c.drawImage(ImageReader(temp_img), x + (w_cel - 70)/2, y + 40, width=70, height=70)

            # Texto: Nome do Condomínio
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(x + w_cel/2, y + 25, NOME_CONDOMINIO)

            # Texto: Unidade e Tipo
            c.setFont("Helvetica", 10)
            c.drawCentredString(x + w_cel/2, y + 12, f"UNID: {item['id']} - {item['tipo']}")

            # Remove arquivo temporário
            if os.path.exists(temp_img):
                os.remove(temp_img)
            
            idx += 1

        c.save()
        print(f"[GERADOR] ✅ Sucesso! PDF disponível em: {caminho_final}")
        return caminho_final

    except Exception as e:
        print(f"[GERADOR] ❌ ERRO CRÍTICO: {str(e)}")
        return None