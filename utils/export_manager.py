import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
import qrcode
import gc

# Unidades exclusivas de cada tipo de medidor
_EXCLUSIVO_GAS = {"LAZER GÁS"}
_EXCLUSIVO_AGUA = {"TERREO GERAL ÁGUA"}


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
        img = qrcode.make(conteudo).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return ImageReader(buf)

    @staticmethod
    def _filtrar_unidades(lista_unidades, tipo_medidor: str) -> list:
        """Remove unidades que não têm o medidor do tipo solicitado."""
        if tipo_medidor == "Água":
            return [u for u in lista_unidades if u not in _EXCLUSIVO_GAS]
        else:
            return [u for u in lista_unidades if u not in _EXCLUSIVO_AGUA]

    @staticmethod
    def _desenhar_grade(c, margem_x, curr_y, colunas, largura_et, altura_et):
        """Desenha linhas horizontais e verticais da grade de etiquetas."""
        c.setLineWidth(0.4)
        c.setStrokeColorRGB(0.6, 0.6, 0.6)
        largura_total = colunas * largura_et

        # Linha horizontal (separador inferior da linha)
        c.line(margem_x, curr_y - 0.05 * cm,
               margem_x + largura_total, curr_y - 0.05 * cm)

        # Linhas verticais entre colunas
        for col in range(1, colunas):
            x_sep = margem_x + col * largura_et
            c.line(x_sep, curr_y - 0.05 * cm,
                   x_sep, curr_y + altura_et - 0.05 * cm)

    @staticmethod
    def gerar_etiquetas_qr_50_por_folha(lista_unidades, tipo_medidor="Água"):
        pasta = ExportManager.obter_caminho_exportacao()
        prefixo = "Agua" if tipo_medidor == "Água" else "Gas"
        pdf_path = os.path.join(pasta, f"Etiquetas_50_{prefixo}.pdf")

        unidades = ExportManager._filtrar_unidades(lista_unidades, tipo_medidor)

        c = canvas.Canvas(pdf_path, pagesize=A4)

        colunas, linhas = 5, 10
        largura_et = 4.0 * cm
        altura_et = 2.8 * cm
        margem_x = 0.6 * cm

        curr_x = margem_x
        curr_y = A4[1] - 1.0 * cm - altura_et

        cont_col = 0
        cont_lin = 0
        y_inicio_linha = curr_y  # y do topo da linha atual (para grade vertical)

        for unidade in unidades:
            reader = ExportManager._qr_image_reader(f"{unidade}-{tipo_medidor}")

            # Título
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(curr_x + 2 * cm, curr_y + 2.5 * cm, "VIVERE PRUDENTE")

            # QR Code
            c.drawImage(reader, curr_x + 1 * cm, curr_y + 0.5 * cm,
                        width=2 * cm, height=2 * cm)

            # Label da unidade — reduz fonte se o texto for longo
            label = f"UNID: {unidade} - {tipo_medidor.upper()}"
            font_size = 8 if len(label) <= 24 else 6
            c.setFont("Helvetica-Bold", font_size)
            c.drawCentredString(curr_x + 2 * cm, curr_y + 0.1 * cm, label)

            cont_col += 1
            if cont_col >= colunas:
                ExportManager._desenhar_grade(
                    c, margem_x, curr_y, colunas, largura_et, altura_et)

                cont_col = 0
                curr_x = margem_x
                curr_y -= altura_et
                y_inicio_linha = curr_y
                cont_lin += 1
            else:
                curr_x += largura_et

            if cont_lin >= linhas:
                c.showPage()
                curr_x = margem_x
                curr_y = A4[1] - 1.0 * cm - altura_et
                y_inicio_linha = curr_y
                cont_lin = 0

        # Grade para última linha parcial (se houver unidades restantes)
        if cont_col > 0:
            ExportManager._desenhar_grade(
                c, margem_x, curr_y, colunas, largura_et, altura_et)

        c.save()
        gc.collect()
        return pdf_path
