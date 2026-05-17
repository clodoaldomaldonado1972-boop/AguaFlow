import os
import io
import re
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
import qrcode
import gc


class ExportManager:
    @staticmethod
    def obter_caminho_exportacao():
        if os.environ.get("FLET_PLATFORM") == "android":
            caminho = os.path.join(os.getcwd(), "storage")
        else:
            caminho = os.path.join(os.getcwd(), "exports")
        os.makedirs(caminho, exist_ok=True)
        return caminho

    @staticmethod
    def _qr_image_reader(conteudo: str) -> ImageReader:
        """Gera QR em memória (BytesIO) e retorna ImageReader pronto para ReportLab.
        Converte para RGB para evitar problema de renderização com imagens modo '1'."""
        img = qrcode.make(conteudo).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return ImageReader(buf)

    @staticmethod
    def gerar_etiquetas_qr_50_por_folha(lista_unidades, tipo_medidor="Água"):
        pasta = ExportManager.obter_caminho_exportacao()
        prefixo = "Agua" if tipo_medidor == "Água" else "Gas"
        pdf_path = os.path.join(pasta, f"Etiquetas_50_{prefixo}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)

        colunas, linhas = 5, 10
        largura_et = 4.0 * cm
        altura_et = 2.8 * cm
        margem_x = 0.6 * cm

        curr_x = margem_x
        curr_y = A4[1] - 1.0 * cm - altura_et

        cont_col = 0
        cont_lin = 0

        for unidade in lista_unidades:
            reader = ExportManager._qr_image_reader(f"{unidade}-{tipo_medidor}")

            # Etiqueta: título, QR e label
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(curr_x + 2 * cm, curr_y + 2.5 * cm, "VIVERE PRUDENTE")
            c.drawImage(reader, curr_x + 1 * cm, curr_y + 0.5 * cm, width=2 * cm, height=2 * cm)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(curr_x + 2 * cm, curr_y + 0.1 * cm,
                                f"UNID: {unidade} - {tipo_medidor.upper()}")

            cont_col += 1
            if cont_col >= colunas:
                # Linha separadora ao fim de cada linha completa
                c.setLineWidth(0.4)
                c.setStrokeColorRGB(0.6, 0.6, 0.6)
                c.line(margem_x, curr_y - 0.05 * cm,
                       A4[0] - margem_x, curr_y - 0.05 * cm)

                cont_col = 0
                curr_x = margem_x
                curr_y -= altura_et
                cont_lin += 1
            else:
                curr_x += largura_et

            if cont_lin >= linhas:
                c.showPage()
                curr_x = margem_x
                curr_y = A4[1] - 1.0 * cm - altura_et
                cont_lin = 0

        c.save()
        gc.collect()
        return pdf_path
