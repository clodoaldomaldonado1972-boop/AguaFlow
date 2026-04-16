import os
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from database.database import Database

# --- CONFIGURAÇÕES DE LAYOUT (50 ETIQUETAS POR PÁGINA) ---
COLUNAS = 5  
LINHAS = 10  
NOME_CONDOMINIO = "Vivere Prudente"

def gerar_qr_codes(filtro_tipo="AMBOS", unidade_alvo=None):
    """
    Gera PDF de etiquetas consultando a tabela de MEDIDORES do Supabase.
    O argumento 'unidade_alvo' foi adicionado para evitar o erro de TypeError.
    """
    print(f"\n[GERADOR] 🚀 Gerando etiquetas para: {filtro_tipo} | Alvo: {unidade_alvo}")

    try:
        # 1. Configuração de Saída
        pasta_output = "storage"
        os.makedirs(pasta_output, exist_ok=True)
        nome_arquivo = f"Etiquetas_{filtro_tipo}.pdf"
        caminho_final = os.path.join(pasta_output, nome_arquivo)

        # 2. Busca de Dados (Ajustado para ler Medidores)
        medidores_db = Database.get_medidores(filtro_tipo)
        
        if not medidores_db:
            print("[GERADOR] ⚠️ Nenhum medidor encontrado.")
            return None

        # Filtro opcional por unidade alvo (se vier da interface)
        if unidade_alvo:
            medidores_db = [m for m in medidores_db if m.get('unidade_id') == unidade_alvo]

        # 3. Configuração do PDF
        c = canvas.Canvas(caminho_final, pagesize=A4)
        largura_a4, altura_a4 = A4
        margem_x, margem_y, espaco = 18, 25, 4
        
        w_cel = (largura_a4 - (2 * margem_x) - ((COLUNAS - 1) * espaco)) / COLUNAS
        h_cel = (altura_a4 - (2 * margem_y) - ((LINHAS - 1) * espaco)) / LINHAS

        x_atual, y_atual = margem_x, altura_a4 - margem_y - h_cel

        count = 0
        for idx, item in enumerate(medidores_db):
            m_id = str(item.get('id_qrcode', ''))
            u_id = str(item.get('unidade_id', ''))
            tipo = str(item.get('tipo', ''))

            # Desenha borda da etiqueta
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.setLineWidth(0.3)
            c.rect(x_atual, y_atual, w_cel, h_cel, stroke=1)

            # QR Code
            qr = qrcode.make(f"AGUAFLOW|{m_id}")
            temp_img = f"temp_qr_{idx}.png"
            qr.save(temp_img)

            c.drawImage(ImageReader(temp_img), x_atual + (w_cel-55)/2, y_atual + 20, width=55, height=55)

            # Legendas
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(x_atual + w_cel/2, y_atual + 12, NOME_CONDOMINIO)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(x_atual + w_cel/2, y_atual + 3, f"{u_id} - {tipo.upper()}")

            if os.path.exists(temp_img): os.remove(temp_img)

            # Lógica de posições
            count += 1
            x_atual += w_cel + espaco
            if count % COLUNAS == 0:
                x_atual = margem_x
                y_atual -= (h_cel + espaco)
            if count % (COLUNAS * LINHAS) == 0 and idx < len(medidores_db)-1:
                c.showPage()
                x_atual, y_atual = margem_x, altura_a4 - margem_y - h_cel

        c.save()
        print(f"[GERADOR] ✅ Sucesso: {caminho_final}")
        return caminho_final
    except Exception as e:
        print(f"Erro: {e}")
        return None