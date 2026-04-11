import os
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- CONFIGURAÇÕES DE LAYOUT ---
COLUNAS = 5
LINHAS = 8
NOME_CONDOMINIO = "Vivere Prudente"


def gerar_qr_codes(filtro_tipo="AMBOS", unidade_alvo=None):
    """
    Gera o PDF de etiquetas com a nova ordem:
    1. QR Code
    2. Nome do Condomínio
    3. Unidade - Tipo
    """
    print(
        f"\n[GERADOR] 🚀 Iniciando processo para: {unidade_alvo if unidade_alvo else 'TODOS'}")

    try:
        # 1. Configuração de Pastas
        pasta_output = "storage"
        if not os.path.exists(pasta_output):
            os.makedirs('storage', exist_ok=True)  # Acrescentado

        # 2. Definição do Nome do Arquivo
        sufixo = f"UNID_{unidade_alvo}" if unidade_alvo else "COMPLETO"
        nome_arquivo = f"Etiquetas_{filtro_tipo}_{sufixo}.pdf"

        caminho_final = os.path.join(pasta_output, nome_arquivo)

        # 3. Geração das Etiquetas
        c = canvas.Canvas(caminho_final, pagesize=A4)
        width, height = A4
        lista_impressao = []

        if unidade_alvo:
            if filtro_tipo in ["AGUA", "AMBOS"]:
                lista_impressao.append(
                    {"id": unidade_alvo, "tipo": "ÁGUA", "payload": f"{unidade_alvo}-AGUA"})
            if filtro_tipo in ["GAS", "AMBOS"]:
                lista_impressao.append(
                    {"id": unidade_alvo, "tipo": "GÁS", "payload": f"{unidade_alvo}-GAS"})
        else:
            for andar in range(16, 0, -1):
                for final in range(6, 0, -1):
                    unidade = f"{andar}{final}"
                    if filtro_tipo in ["AGUA", "AMBOS"]:
                        lista_impressao.append(
                            {"id": unidade, "tipo": "ÁGUA", "payload": f"{unidade}-AGUA"})
                    if filtro_tipo in ["GAS", "AMBOS"]:
                        lista_impressao.append(
                            {"id": unidade, "tipo": "GÁS", "payload": f"{unidade}-GAS"})

        w_cel = (width - 2 * 15) / COLUNAS
        h_cel = (height - 2 * 15) / LINHAS

        for i, item in enumerate(lista_impressao):
            if i > 0 and i % (COLUNAS * LINHAS) == 0:
                c.showPage()

            idx = i % (COLUNAS * LINHAS)
            col, row = idx % COLUNAS, idx // COLUNAS
            x = 15 + (col * w_cel)
            y = height - 15 - ((row + 1) * h_cel)

            # --- DESENHO DA ETIQUETA ---

            # A) Borda Cinza
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x + 5, y + 5, w_cel - 10, h_cel - 10, stroke=1, fill=0)

            # B) QR CODE (Agora no TOPO da etiqueta)
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(item['payload'])
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white")

            temp_img = f"temp_{i}_{item['id']}.png"
            img_qr.save(temp_img)

            # Posicionando na parte superior da célula
            c.drawImage(ImageReader(temp_img), x + (w_cel - 60)/2,
                        y + 35, width=60, height=60)

            # C) NOME DO CONDOMÍNIO (Logo depois do QR Code)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x + w_cel/2, y + 12,
                                f"{item['id']} - {item['tipo']}")

            # D) Unidade
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(95, y+30,
                                f"{unidade_alvo or 'UNIDADE'}")

            # Cleanup
            if os.path.exists(temp_img):
                os.remove(temp_img)

        c.save()
        print(f"✅ [GERADOR] Sucesso! Arquivo: {caminho_final}")

    except Exception as e:
        print(f"❌ [GERADOR] ERRO: {str(e)}")
        return None


if __name__ == "__main__":
    # Teste de validação
    gerar_qr_codes("AMBOS", "101")
