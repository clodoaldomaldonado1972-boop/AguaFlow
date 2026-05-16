import csv
import os
import re
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Pasta de saida — nao apaga automaticamente
RELATORIOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "relatorios")


def _sort_key_unidade(item):
    """Ordenacao numerica crescente. Duplex '163/164' usa o primeiro numero (163)."""
    u = str(item.get('unidade_id', '') or '')
    nums = re.findall(r'\d+', u)
    return int(nums[0]) if nums else 99999


class _AguaFlowPDF(FPDF):
    """FPDF com cabecalho repetido em todas as paginas e rodape com leiturista."""

    # Atributos definidos antes do add_page()
    titulo = ""
    mes_ref = ""
    leiturista = ""
    cor_header = (13, 71, 161)    # azul para agua
    cor_fill = (200, 220, 255)    # azul claro para agua

    def header(self):
        # -- Titulo principal --
        self.set_font("Arial", "B", 14)
        self.set_text_color(0, 0, 0)
        self.cell(0, 9, "AguaFlow - Relatorio de Consumo Mensal", ln=True, align='C')

        # -- Subtitulo --
        self.set_font("Arial", size=10)
        self.cell(0, 7,
                  "Condominio Vivere Prudente - Referencia: " + str(self.mes_ref),
                  ln=True, align='C')

        # -- Titulo da secao colorido --
        self.set_font("Arial", "B", 12)
        r, g, b = self.cor_header
        self.set_text_color(r, g, b)
        self.cell(0, 8, str(self.titulo), ln=True, align='L')
        self.set_text_color(0, 0, 0)

        # -- Linha separadora --
        y = self.get_y()
        self.line(10, y, 200, y)
        self.ln(2)

        # -- Cabecalho da tabela --
        self.set_font("Arial", "B", 10)
        fr, fg, fb = self.cor_fill
        self.set_fill_color(fr, fg, fb)
        self.cell(35, 9, "Unidade",        1, 0, 'C', True)
        self.cell(95, 9, "Data/Hora Coleta", 1, 0, 'C', True)
        self.cell(60, 9, "Leitura (m3)",   1, 1, 'C', True)
        self.set_font("Arial", size=10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(110, 110, 110)
        texto = (
            "Leiturista: " + str(self.leiturista) +
            "   |   Gerado em: " + datetime.now().strftime('%d/%m/%Y %H:%M') +
            "   |   Pagina " + str(self.page_no()) + "/{nb}"
        )
        self.cell(0, 5, texto, align='C')
        self.set_text_color(0, 0, 0)


def _criar_pdf(titulo, cor_header, cor_fill, mes_ref, leiturista):
    """Fabrica o objeto PDF com atributos pre-configurados."""
    pdf = _AguaFlowPDF()
    pdf.titulo = titulo
    pdf.mes_ref = mes_ref
    pdf.leiturista = leiturista
    pdf.cor_header = cor_header
    pdf.cor_fill = cor_fill
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    return pdf


class RelatorioEngine:
    """Motor de geracao de documentos e comunicacoes do AguaFlow."""

    # ── utilidades internas ──────────────────────────────────────────────────

    @staticmethod
    def _garantir_pasta():
        os.makedirs(RELATORIOS_DIR, exist_ok=True)
        return RELATORIOS_DIR

    @staticmethod
    def _caminho(tipo, ext):
        """Gera caminho com timestamp: relatorios/relatorio_agua_052026.pdf"""
        pasta = RelatorioEngine._garantir_pasta()
        mes = datetime.now().strftime('%m%Y')
        nome = f"relatorio_{tipo}_{mes}.{ext}"
        return os.path.join(pasta, nome)

    @staticmethod
    def _filtrar_e_ordenar(dados, campo):
        """Filtra por campo nao nulo e ordena por unidade numericamente crescente."""
        filtrado = [d for d in dados if d.get(campo) is not None]
        return sorted(filtrado, key=_sort_key_unidade)

    # ── geracao de PDFs ──────────────────────────────────────────────────────

    @staticmethod
    def gerar_relatorio_agua(dados, leiturista="Zelador"):
        """PDF de consumo de AGUA com cabecalho em todas as paginas."""
        mes_ref = datetime.now().strftime('%m/%Y')
        pdf = _criar_pdf(
            titulo="QUADRO DE CONSUMO: AGUA",
            cor_header=(13, 71, 161),
            cor_fill=(200, 220, 255),
            mes_ref=mes_ref,
            leiturista=leiturista
        )

        dados_agua = RelatorioEngine._filtrar_e_ordenar(dados, 'leitura_agua')
        for item in dados_agua:
            pdf.cell(35, 8, str(item.get('unidade_id', '')), 1)
            pdf.cell(95, 8, str(item.get('data_hora_coleta', '')), 1)
            pdf.cell(60, 8, f"{float(item.get('leitura_agua', 0)):.2f}", 1, 0, 'R')
            pdf.ln()

        # Linha de total
        total = sum(float(d.get('leitura_agua', 0) or 0) for d in dados_agua)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(130, 8, "TOTAL CONSUMO (m3)", 1, 0, 'R')
        pdf.cell(60,  8, f"{total:.2f}", 1, 1, 'C')

        caminho = RelatorioEngine._caminho("agua", "pdf")
        pdf.output(caminho)
        return caminho

    @staticmethod
    def gerar_relatorio_gas(dados, leiturista="Zelador"):
        """PDF de consumo de GAS com cabecalho em todas as paginas."""
        mes_ref = datetime.now().strftime('%m/%Y')
        pdf = _criar_pdf(
            titulo="QUADRO DE CONSUMO: GAS",
            cor_header=(230, 81, 0),
            cor_fill=(255, 224, 178),
            mes_ref=mes_ref,
            leiturista=leiturista
        )

        dados_gas = RelatorioEngine._filtrar_e_ordenar(dados, 'leitura_gas')
        for item in dados_gas:
            pdf.cell(35, 8, str(item.get('unidade_id', '')), 1)
            pdf.cell(95, 8, str(item.get('data_hora_coleta', '')), 1)
            pdf.cell(60, 8, f"{float(item.get('leitura_gas', 0)):.3f}", 1, 0, 'R')
            pdf.ln()

        # Linha de total
        total = sum(float(d.get('leitura_gas', 0) or 0) for d in dados_gas)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(130, 8, "TOTAL CONSUMO (m3)", 1, 0, 'R')
        pdf.cell(60,  8, f"{total:.3f}", 1, 1, 'C')

        caminho = RelatorioEngine._caminho("gas", "pdf")
        pdf.output(caminho)
        return caminho

    # ── geracao de CSVs ──────────────────────────────────────────────────────

    @staticmethod
    def gerar_csv_agua(dados):
        """CSV de consumo de AGUA, ordenado numericamente, com leiturista."""
        caminho = RelatorioEngine._caminho("agua", "csv")
        campos = ["unidade_id", "leitura_agua", "data_hora_coleta", "leiturista"]
        dados_agua = RelatorioEngine._filtrar_e_ordenar(dados, 'leitura_agua')

        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=campos, delimiter=';')
            writer.writeheader()
            for item in dados_agua:
                writer.writerow({k: item.get(k, '') for k in campos})
        return caminho

    @staticmethod
    def gerar_csv_gas(dados):
        """CSV de consumo de GAS, ordenado numericamente, com leiturista."""
        caminho = RelatorioEngine._caminho("gas", "csv")
        campos = ["unidade_id", "leitura_gas", "data_hora_coleta", "leiturista"]
        dados_gas = RelatorioEngine._filtrar_e_ordenar(dados, 'leitura_gas')

        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=campos, delimiter=';')
            writer.writeheader()
            for item in dados_gas:
                writer.writerow({k: item.get(k, '') for k in campos})
        return caminho

    # ── geracao de todos os arquivos ─────────────────────────────────────────

    @staticmethod
    def gerar_todos(dados, leiturista="Zelador"):
        """
        Gera os 4 arquivos (PDF agua, PDF gas, CSV agua, CSV gas).
        Salva em relatorios/ com nome datado. Nao sobrescreve automaticamente.
        Retorna dict com os caminhos.
        """
        return {
            "pdf_agua": RelatorioEngine.gerar_relatorio_agua(dados, leiturista),
            "pdf_gas":  RelatorioEngine.gerar_relatorio_gas(dados, leiturista),
            "csv_agua": RelatorioEngine.gerar_csv_agua(dados),
            "csv_gas":  RelatorioEngine.gerar_csv_gas(dados),
        }

    # ── envio de email ───────────────────────────────────────────────────────

    @staticmethod
    def enviar_relatorios_por_email(arquivos, destinatario=None):
        """
        Envia arquivos gerados via SMTP.
        arquivos: dict {'pdf_agua': ..., 'pdf_gas': ..., 'csv_agua': ..., 'csv_gas': ...}
                  ou lista de caminhos
        NAO apaga os arquivos apos o envio.
        """
        EMAIL_ORIGEM = os.getenv("EMAIL_USER", "")
        SENHA_APP    = os.getenv("EMAIL_PASS", "")
        EMAIL_DESTINO = destinatario or os.getenv("EMAIL_DESTINO", "escritorio@vivereprudente.com.br")
        mes_ref = datetime.now().strftime('%m/%Y')

        # Normaliza para lista de caminhos
        if isinstance(arquivos, dict):
            lista = [v for v in arquivos.values() if v]
        elif isinstance(arquivos, (list, tuple)):
            lista = [p for p in arquivos if p]
        else:
            lista = [arquivos] if arquivos else []

        try:
            msg = EmailMessage()
            msg['Subject'] = f"Relatorio de Consumo Agua/Gas - {mes_ref}"
            msg['From']    = EMAIL_ORIGEM
            msg['To']      = EMAIL_DESTINO

            nomes = "\n".join(
                f"  - {os.path.basename(p)}" for p in lista if os.path.exists(p)
            )
            msg.set_content(
                f"Prezados,\n\n"
                f"Segue em anexo o relatorio de fechamento de leituras\n"
                f"do Condominio Vivere Prudente - referencia {mes_ref}.\n\n"
                f"Arquivos:\n{nomes}\n\n"
                f"Gerado automaticamente pelo AguaFlow."
            )

            for path in lista:
                if not path or not os.path.exists(path):
                    continue
                ext = os.path.splitext(path)[1].lower()
                subtype = 'pdf' if ext == '.pdf' else 'csv'
                with open(path, 'rb') as f:
                    msg.add_attachment(
                        f.read(), maintype='application', subtype=subtype,
                        filename=os.path.basename(path)
                    )

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_ORIGEM, SENHA_APP)
                smtp.send_message(msg)

            return True, f"Relatorios enviados com sucesso para {EMAIL_DESTINO}!"
        except Exception as e:
            return False, f"Falha no envio do e-mail: {str(e)}"

    # ── retrocompatibilidade ─────────────────────────────────────────────────

    @staticmethod
    def gerar_relatorio_consumo(dados, leiturista="Zelador"):
        """Compatibilidade com chamadas antigas. Gera PDF agua e gas."""
        RelatorioEngine.gerar_relatorio_gas(dados, leiturista)
        return RelatorioEngine.gerar_relatorio_agua(dados, leiturista)

    @staticmethod
    def gerar_csv_consumo(dados):
        """Compatibilidade com chamadas antigas. Gera CSV agua e gas."""
        RelatorioEngine.gerar_csv_gas(dados)
        return RelatorioEngine.gerar_csv_agua(dados)
