import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import utils.gerador_qr as gerador_qr

# AJUSTE DE PATH: Garante que o script enxergue a raiz do projeto no APK
caminho_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if caminho_raiz not in sys.path:
    sys.path.append(caminho_raiz)

# --- 1. GERAÇÃO DE ETIQUETAS QR ---

def gerar_pdf_etiquetas(lista_unidades):
    """
    Gera um PDF com etiquetas QR Code para colagem nos hidrômetros.
    Organizado em grade (3 colunas x 5 linhas).
    """
    pasta_storage = os.path.join(caminho_raiz, "storage")
    if not os.path.exists(pasta_storage):
        os.makedirs(pasta_storage)

    caminho_pdf = os.path.join(pasta_storage, "Etiquetas_QR_Vivere.pdf")
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    width, height = A4

    colunas, linhas = 3, 5
    margem_x, margem_y = 1.5 * cm, 2.0 * cm
    espaco_x, espaco_y = 6.0 * cm, 5.0 * cm
    tamanho_qr = 3.5 * cm

    x_atual, y_atual = margem_x, height - margem_y - tamanho_qr
    contador = 0

    for unidade in lista_unidades:
        # Gera o arquivo PNG temporário do QR Code
        path_qr = gerador_qr.gerar_qr_unidade(unidade)
        
        if path_qr and os.path.exists(path_qr):
            # Desenha o QR Code
            c.drawImage(path_qr, x_atual, y_atual, width=tamanho_qr, height=tamanho_qr)
            # Legenda da Unidade
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(x_atual + (tamanho_qr/2), y_atual - 15, f"UNIDADE: {unidade}")
            c.setFont("Helvetica", 8)
            c.drawCentredString(x_atual + (tamanho_qr/2), y_atual - 28, "VIVERE PRUDENTE - AGUAFLOW")

            contador += 1
            x_atual += espaco_x

            # Lógica de quebra de linha e página
            if contador % colunas == 0:
                x_atual = margem_x
                y_atual -= espaco_y
            
            if contador % (colunas * linhas) == 0:
                c.showPage()
                x_atual, y_atual = margem_x, height - margem_y - tamanho_qr

    c.save()
    return caminho_pdf

# --- 2. GERAÇÃO DE RELATÓRIO DE CONSUMO ---

def gerar_pdf_consumo(dados_leituras):
    """
    Gera o relatório mensal consolidado para o síndico.
    dados_leituras: Lista de tuplas ou dicionários vindo do Database.
    """
    pasta_storage = os.path.join(caminho_raiz, "storage")
    caminho_pdf = os.path.join(pasta_storage, f"Relatorio_Consumo_{datetime.now().strftime('%m_%Y')}.pdf")
    
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    width, height = A4

    def desenhar_cabecalho(canvas_obj, y_pos):
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawCentredString(width/2, y_pos, "RELATÓRIO DE CONSUMO - VIVERE PRUDENTE")
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawCentredString(width/2, y_pos - 20, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        y_tab = y_pos - 60
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(50, y_tab, "UNID")
        canvas_obj.drawString(120, y_tab, "LEIT. ANTERIOR")
        canvas_obj.drawString(250, y_tab, "LEIT. ATUAL")
        canvas_obj.drawString(400, y_tab, "CONSUMO (m³)")
        canvas_obj.line(50, y_tab - 5, 550, y_tab - 5)
        return y_tab - 20

    y = desenhar_cabecalho(c, 800)

    for r in dados_leituras:
        # Se a página acabar, cria uma nova
        if y < 50:
            c.showPage()
            y = desenhar_cabecalho(c, 800)

        unid = str(r['unidade'])
        atu = float(r['leitura_agua']) if r['leitura_agua'] else 0.0
        # Simulação de cálculo de consumo (Diferença entre atual e anterior)
        # No seu sistema, você buscaria a anterior no DB antes de passar para cá
        ant = 0.0 # Placeholder
        consumo = max(0, atu - ant)

        c.setFont("Helvetica", 10)
        c.drawString(50, y, unid)
        c.drawString(120, y, f"{ant:.2f}")
        c.drawString(250, y, f"{atu:.2f}")
        c.drawString(400, y, f"{consumo:.2f}")
        
        y -= 20

    c.save()
    return caminho_pdf