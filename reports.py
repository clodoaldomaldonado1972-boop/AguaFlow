from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import qrcode
import os

def gerar_qr_imagem(unidade):
    """Cria o PNG se não existir"""
    if not os.path.exists("qrcodes"): os.makedirs("qrcodes")
    caminho = f"qrcodes/{str(unidade)}.png"
    if not os.path.exists(caminho):
        img = qrcode.make(str(unidade))
        img.save(caminho)
    return caminho

def gerar_pdf_etiquetas_qr(lista_unidades, nome_pdf="Etiquetas_A4.pdf"):
    """Monta a grade de etiquetas no PDF A4"""
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4
    x, y = 1.5*cm, height - 4*cm
    
    for unidade in lista_unidades:
        img = gerar_qr_imagem(unidade)
        c.drawImage(img, x, y, width=3.5*cm, height=3.5*cm)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + 1.75*cm, y - 0.4*cm, f"UNIDADE: {unidade}")
        
        x += 4.8*cm
        if x > width - 4*cm:
            x = 1.5*cm
            y -= 5*cm
        if y < 2*cm:
            c.showPage()
            y = height - 4*cm
    c.save()
    return nome_pdf

def gerar_relatorio_leituras_pdf(dados, nome_pdf="Relatorio_Mensal.pdf"):
    """Gera um PDF listando todas as leituras feitas no banco"""
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4
    y = height - 2*cm
    
    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, y, "ÁguaFlow - Relatório de Leituras Mensal")
    y -= 1*cm
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, "Condomínio Vivere Prudente")
    y -= 1.5*cm
    
    # Títulos da Tabela
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Unidade")
    c.drawString(5*cm, y, "Anterior (m³)")
    c.drawString(9*cm, y, "Atual (m³)")
    c.drawString(13*cm, y, "Consumo (m³)")
    c.drawString(17*cm, y, "Data")
    y -= 0.5*cm
    c.line(2*cm, y, 19*cm, y)
    y -= 0.6*cm
    
    c.setFont("Helvetica", 10)
    for row in dados:
        unid = row[1]
        ant  = row[2] if row[2] is not None else 0.0
        atu  = row[3] if row[3] is not None else 0.0
        cons = row[4] if row[4] is not None else 0.0
        data = row[5] if row[5] is not None else "---"
        
        c.drawString(2*cm, y, str(unid))
        c.drawString(5*cm, y, f"{ant:.2f}")
        c.drawString(9*cm, y, f"{atu:.2f}")
        c.drawString(13*cm, y, f"{cons:.2f}")
        c.drawString(17*cm, y, str(data)[:10])
        
        y -= 0.6*cm
        
        # Correção de identação aqui:
        if y < 2*cm: 
            c.showPage()
            y = height - 2*cm
            c.setFont("Helvetica", 10)

    c.save()
    return nome_pdf