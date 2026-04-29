import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
import qrcode
import gc

class ExportManager:
    @staticmethod
    def _normalizar_nome_arquivo(texto: str) -> str:
        """Gera um nome seguro para ficheiro temporário."""
        return re.sub(r"[^A-Za-z0-9._-]+", "_", str(texto))

    @staticmethod
    def obter_caminho_exportacao():
        if os.environ.get("FLET_PLATFORM") == "android":
            caminho = os.path.join(os.getcwd(), "storage")
        else:
            caminho = os.path.join(os.getcwd(), "exports")
        os.makedirs(caminho, exist_ok=True)
        return caminho

    @staticmethod
    def gerar_etiquetas_qr_50_por_folha(lista_unidades, tipo_medidor="Água"):
        pasta = ExportManager.obter_caminho_exportacao()
        prefixo = "Agua" if tipo_medidor == "Água" else "Gas"
        pdf_path = os.path.join(pasta, f"Etiquetas_50_{prefixo}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        
        colunas, linhas = 5, 10
        largura_et, altura_et = 4.0 * cm, 2.8 * cm
        curr_x, curr_y = 0.6 * cm, A4[1] - 1.0 * cm - altura_et
        
        cont_col = 0
        cont_lin = 0

        for unidade in lista_unidades:
            # QR Code com Unidade-Tipo
            qr = qrcode.make(f"{unidade}-{tipo_medidor}")
            unidade_safe = ExportManager._normalizar_nome_arquivo(unidade)
            temp_path = os.path.join(pasta, f"tmp_{unidade_safe}_{prefixo}.png")
            qr.save(temp_path)
            
            # Desenho da Etiqueta
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(curr_x + 2*cm, curr_y + 2.5*cm, "VIVERE PRUDENTE")
            c.drawImage(ImageReader(temp_path), curr_x + 1*cm, curr_y + 0.5*cm, width=2*cm, height=2*cm)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(curr_x + 2*cm, curr_y + 0.1*cm, f"UNID: {unidade} - {tipo_medidor.upper()}")
            
            os.remove(temp_path)
            
            cont_col += 1
            if cont_col >= colunas:
                cont_col = 0
                curr_x = 0.6 * cm
                curr_y -= altura_et
                cont_lin += 1
            else:
                curr_x += largura_et
            
            if cont_lin >= linhas:
                c.showPage()
                curr_y = A4[1] - 1.0 * cm - altura_et
                cont_lin = 0

        c.save()
        gc.collect()
        return pdf_path