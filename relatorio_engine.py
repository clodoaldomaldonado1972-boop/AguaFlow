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

# Larguras das colunas (mm) — total 190mm (A4 com margem 10mm cada lado)
# Unidade larga o suficiente para "TERREO GERAL AGUA" (18 chars)
CW = {
    'unidade':   50,   # Unidade
    'data':      48,   # Data/Hora Coleta
    'anterior':  30,   # Leitura Anterior (m3)
    'atual':     32,   # Leitura Atual (m3)
    'consumo':   30,   # Consumo (m3)
}
# Total: 50+48+30+32+30 = 190 ✓


def _sort_key_unidade(item):
    """Ordenacao numerica crescente. Duplex '163/164' usa o primeiro numero (163)."""
    u = str(item.get('unidade_id', '') or '')
    nums = re.findall(r'\d+', u)
    return int(nums[0]) if nums else 99999


class _AguaFlowPDF(FPDF):
    """FPDF com cabecalho repetido em todas as paginas e rodape com leiturista."""

    titulo = ""
    mes_ref = ""
    leiturista = ""
    cor_header = (13, 71, 161)
    cor_fill = (200, 220, 255)

    def header(self):
        # Titulo principal
        self.set_font("Arial", "B", 13)
        self.set_text_color(0, 0, 0)
        self.cell(0, 9, "AguaFlow - Relatorio de Consumo Mensal", ln=True, align='C')

        # Subtitulo
        self.set_font("Arial", size=9)
        self.cell(0, 6,
                  "Condominio Vivere Prudente - Referencia: " + str(self.mes_ref),
                  ln=True, align='C')

        # Titulo da secao (colorido)
        self.set_font("Arial", "B", 11)
        r, g, b = self.cor_header
        self.set_text_color(r, g, b)
        self.cell(0, 7, str(self.titulo), ln=True, align='L')
        self.set_text_color(0, 0, 0)

        # Linha separadora
        y = self.get_y()
        self.line(10, y, 200, y)
        self.ln(1)

        # Cabecalho da tabela (5 colunas)
        self.set_font("Arial", "B", 9)
        fr, fg, fb = self.cor_fill
        self.set_fill_color(fr, fg, fb)
        h = 8
        self.cell(CW['unidade'],  h, "Unidade",          1, 0, 'C', True)
        self.cell(CW['data'],     h, "Data/Hora Coleta", 1, 0, 'C', True)
        self.cell(CW['anterior'], h, "Ant. (m3)",         1, 0, 'C', True)
        self.cell(CW['atual'],    h, "Atual (m3)",        1, 0, 'C', True)
        self.cell(CW['consumo'],  h, "Consumo (m3)",      1, 1, 'C', True)
        self.set_font("Arial", size=9)

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
    pdf = _AguaFlowPDF()
    pdf.titulo = titulo
    pdf.mes_ref = mes_ref
    pdf.leiturista = leiturista
    pdf.cor_header = cor_header
    pdf.cor_fill = cor_fill
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(10, 10, 10)
    pdf.add_page()
    return pdf


def _fmt_anterior(val):
    """Formata leitura anterior: '---' quando nao existe (primeiro ciclo)."""
    if val is None:
        return "---"
    try:
        return f"{float(val):.2f}"
    except Exception:
        return "---"


def _fmt_consumo(atual, anterior):
    """Calcula consumo = atual - anterior. Retorna '---' quando anterior nao existe."""
    if anterior is None:
        return "---"
    try:
        c = float(atual or 0) - float(anterior)
        return f"{c:.2f}"
    except Exception:
        return "---"


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
        """Filtra por campo nao nulo e ordena numericamente crescente."""
        filtrado = [d for d in dados if d.get(campo) is not None]
        return sorted(filtrado, key=_sort_key_unidade)

    # ── geracao de PDFs ──────────────────────────────────────────────────────

    @staticmethod
    def gerar_relatorio_agua(dados, leiturista="Zelador"):
        """PDF de consumo de AGUA — colunas: Unidade, Data, Anterior, Atual, Consumo."""
        mes_ref = datetime.now().strftime('%m/%Y')
        pdf = _criar_pdf(
            titulo="QUADRO DE CONSUMO: AGUA",
            cor_header=(13, 71, 161),
            cor_fill=(200, 220, 255),
            mes_ref=mes_ref,
            leiturista=leiturista
        )

        dados_agua = RelatorioEngine._filtrar_e_ordenar(dados, 'leitura_agua')
        h = 7
        total_atual = 0.0
        total_consumo = 0.0
        tem_anterior = any(d.get('leitura_anterior_agua') is not None for d in dados_agua)

        for item in dados_agua:
            atual = float(item.get('leitura_agua', 0) or 0)
            anterior = item.get('leitura_anterior_agua')
            consumo_str = _fmt_consumo(atual, anterior)
            total_atual += atual
            if anterior is not None:
                try:
                    total_consumo += float(atual) - float(anterior)
                except Exception:
                    pass

            pdf.cell(CW['unidade'],  h, str(item.get('unidade_id', '')),            1, 0, 'L')
            pdf.cell(CW['data'],     h, str(item.get('data_hora_coleta', '')),       1, 0, 'L')
            pdf.cell(CW['anterior'], h, _fmt_anterior(anterior),                     1, 0, 'R')
            pdf.cell(CW['atual'],    h, f"{atual:.2f}",                              1, 0, 'R')
            pdf.cell(CW['consumo'],  h, consumo_str,                                 1, 1, 'R')

        # Linha de totais
        pdf.set_font("Arial", "B", 9)
        pdf.cell(CW['unidade'] + CW['data'], h, "TOTAL", 1, 0, 'R')
        pdf.cell(CW['anterior'], h, "---" if not tem_anterior else "",               1, 0, 'R')
        pdf.cell(CW['atual'],    h, f"{total_atual:.2f}",                            1, 0, 'R')
        pdf.cell(CW['consumo'],  h, "---" if not tem_anterior else f"{total_consumo:.2f}", 1, 1, 'R')

        caminho = RelatorioEngine._caminho("agua", "pdf")
        pdf.output(caminho)
        return caminho

    @staticmethod
    def gerar_relatorio_gas(dados, leiturista="Zelador"):
        """PDF de consumo de GAS — colunas: Unidade, Data, Anterior, Atual, Consumo."""
        mes_ref = datetime.now().strftime('%m/%Y')
        pdf = _criar_pdf(
            titulo="QUADRO DE CONSUMO: GAS",
            cor_header=(230, 81, 0),
            cor_fill=(255, 224, 178),
            mes_ref=mes_ref,
            leiturista=leiturista
        )

        dados_gas = RelatorioEngine._filtrar_e_ordenar(dados, 'leitura_gas')
        h = 7
        total_atual = 0.0
        total_consumo = 0.0
        tem_anterior = any(d.get('leitura_anterior_gas') is not None for d in dados_gas)

        for item in dados_gas:
            atual = float(item.get('leitura_gas', 0) or 0)
            anterior = item.get('leitura_anterior_gas')
            consumo_str = _fmt_consumo(atual, anterior)
            total_atual += atual
            if anterior is not None:
                try:
                    total_consumo += float(atual) - float(anterior)
                except Exception:
                    pass

            pdf.cell(CW['unidade'],  h, str(item.get('unidade_id', '')),            1, 0, 'L')
            pdf.cell(CW['data'],     h, str(item.get('data_hora_coleta', '')),       1, 0, 'L')
            pdf.cell(CW['anterior'], h, _fmt_anterior(anterior),                     1, 0, 'R')
            pdf.cell(CW['atual'],    h, f"{atual:.3f}",                              1, 0, 'R')
            pdf.cell(CW['consumo'],  h, consumo_str,                                 1, 1, 'R')

        # Linha de totais
        pdf.set_font("Arial", "B", 9)
        pdf.cell(CW['unidade'] + CW['data'], h, "TOTAL", 1, 0, 'R')
        pdf.cell(CW['anterior'], h, "---" if not tem_anterior else "",               1, 0, 'R')
        pdf.cell(CW['atual'],    h, f"{total_atual:.3f}",                            1, 0, 'R')
        pdf.cell(CW['consumo'],  h, "---" if not tem_anterior else f"{total_consumo:.3f}", 1, 1, 'R')

        caminho = RelatorioEngine._caminho("gas", "pdf")
        pdf.output(caminho)
        return caminho

    # ── geracao de CSVs ──────────────────────────────────────────────────────

    @staticmethod
    def gerar_csv_agua(dados):
        """CSV de AGUA com leitura anterior, consumo e leiturista."""
        caminho = RelatorioEngine._caminho("agua", "csv")
        dados_agua = RelatorioEngine._filtrar_e_ordenar(dados, 'leitura_agua')
        campos = ["unidade_id", "data_hora_coleta", "leitura_anterior_agua",
                  "leitura_agua", "consumo_agua", "leiturista"]

        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=campos, delimiter=';')
            writer.writeheader()
            for item in dados_agua:
                atual = item.get('leitura_agua')
                anterior = item.get('leitura_anterior_agua')
                consumo = ""
                if atual is not None and anterior is not None:
                    try:
                        consumo = round(float(atual) - float(anterior), 2)
                    except Exception:
                        pass
                writer.writerow({
                    "unidade_id":            item.get('unidade_id', ''),
                    "data_hora_coleta":      item.get('data_hora_coleta', ''),
                    "leitura_anterior_agua": anterior if anterior is not None else '',
                    "leitura_agua":          atual if atual is not None else '',
                    "consumo_agua":          consumo,
                    "leiturista":            item.get('leiturista', ''),
                })
        return caminho

    @staticmethod
    def gerar_csv_gas(dados):
        """CSV de GAS com leitura anterior, consumo e leiturista."""
        caminho = RelatorioEngine._caminho("gas", "csv")
        dados_gas = RelatorioEngine._filtrar_e_ordenar(dados, 'leitura_gas')
        campos = ["unidade_id", "data_hora_coleta", "leitura_anterior_gas",
                  "leitura_gas", "consumo_gas", "leiturista"]

        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=campos, delimiter=';')
            writer.writeheader()
            for item in dados_gas:
                atual = item.get('leitura_gas')
                anterior = item.get('leitura_anterior_gas')
                consumo = ""
                if atual is not None and anterior is not None:
                    try:
                        consumo = round(float(atual) - float(anterior), 3)
                    except Exception:
                        pass
                writer.writerow({
                    "unidade_id":           item.get('unidade_id', ''),
                    "data_hora_coleta":     item.get('data_hora_coleta', ''),
                    "leitura_anterior_gas": anterior if anterior is not None else '',
                    "leitura_gas":          atual if atual is not None else '',
                    "consumo_gas":          consumo,
                    "leiturista":           item.get('leiturista', ''),
                })
        return caminho

    # ── geracao de todos os arquivos ─────────────────────────────────────────

    @staticmethod
    def gerar_todos(dados, leiturista="Zelador"):
        """
        Gera os 4 arquivos (PDF agua, PDF gas, CSV agua, CSV gas).
        Salva em relatorios/ com nome datado. Nao sobrescreve. Nao apaga.
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
        arquivos: dict com chaves pdf_agua/pdf_gas/csv_agua/csv_gas, ou lista de caminhos.
        NAO apaga arquivos apos o envio.
        """
        EMAIL_ORIGEM  = os.getenv("EMAIL_USER", "")
        SENHA_APP     = os.getenv("EMAIL_PASS", "")
        EMAIL_DESTINO = destinatario or os.getenv("EMAIL_DESTINO", "escritorio@vivereprudente.com.br")
        mes_ref = datetime.now().strftime('%m/%Y')

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
                f"  - {os.path.basename(p)}" for p in lista if p and os.path.exists(p)
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
