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
        
        x += 4.8*cm # Move para o lado
        if x > width - 4*cm: # Pula linha
            x = 1.5*cm
            y -= 5*cm
        if y < 2*cm: # Nova página
            c.showPage()
            y = height - 4*cm
    c.save()
    return nome_pdf