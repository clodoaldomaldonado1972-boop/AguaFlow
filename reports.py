import os
import qrcode
import smtplib
from datetime import datetime
import flet as ft
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import database as db

# =============================================================================
# 1. MÓDULO DE INFRAESTRUTURA (Arquivos e Pastas)
# =============================================================================


def preparar_caminho_pdf():
    """
    MODULARIDADE: Separa a criação de pastas da criação do PDF.
    Cria uma pasta para o mês atual e gera um nome de arquivo único com timestamp.
    """
    pasta_mensal = datetime.now().strftime("Relatorios_%Y_%m")
    if not os.path.exists(pasta_mensal):
        os.makedirs(pasta_mensal)

    timestamp = datetime.now().strftime("%d_%H%M%S")
    return os.path.join(pasta_mensal, f"Relatorio_{timestamp}.pdf")


def buscar_imagem_qr(unidade):
    """
    MODULARIDADE: Centraliza a gestão de imagens QR.
    Verifica se a pasta existe, se a imagem já foi gerada e retorna o caminho.
    """
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")

    caminho = f"qrcodes/{str(unidade)}.png"
    if not os.path.exists(caminho):
        img = qrcode.make(str(unidade))
        img.save(caminho)
    return caminho

# =============================================================================
# 2. MÓDULO DE FORMATAÇÃO VISUAL (Design do PDF)
# =============================================================================


def desenhar_cabecalho(canvas_obj, y_pos):
    """
    MODULARIDADE: Padroniza o topo de todas as páginas do relatório.
    Retorna a nova posição 'y' onde o conteúdo deve começar.
    """
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawString(1.5*cm, y_pos, "Vivere Flow - Relatório de Leituras")

    y_pos -= 0.8*cm
    canvas_obj.setFont("Helvetica-Bold", 9)
    canvas_obj.drawString(1.5*cm, y_pos, "Unidade")
    canvas_obj.drawString(4.0*cm, y_pos, "Leitura Anterior")
    canvas_obj.drawString(10.0*cm, y_pos, "Leitura Atual")
    canvas_obj.drawString(16.0*cm, y_pos, "Consumo")

    # Linha divisória para separar o cabeçalho dos dados
    canvas_obj.line(1.5*cm, y_pos - 0.2*cm, 19.5*cm, y_pos - 0.2*cm)
    return y_pos - 0.6*cm


def formatar_celula_data(valor, data_bruta, data_referencia):
    """
    LÓGICA DE DATA INTELIGENTE:
    Compara a data da linha atual com a 'data_referencia' (última exibida).
    Se for igual, retorna apenas o valor. Se for diferente, retorna Valor + Data.
    """
    data_limpa = data_bruta[:10] if data_bruta else "--/--/--"
    texto_formatado = f"{valor:8.2f}"

    # Se a data mudou em relação à linha anterior, nós a exibimos
    if data_limpa != data_referencia:
        texto_formatado += f" ({data_limpa})"
        return texto_formatado, data_limpa  # Retorna o texto e atualiza a referência

    # Retorna o texto e mantém a referência
    return texto_formatado, data_referencia


# =============================================================================
# 3. MÓDULO DE PROCESSAMENTO (Orquestração do Relatório)
# =============================================================================

def gerar_relatorio_consumo(dados):
    """
    FUNÇÃO PRINCIPAL: Une todos os módulos para construir o relatório final.
    """
    caminho_pdf = preparar_caminho_pdf()
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    width, height = A4

    # Estado inicial do desenho
    y = desenhar_cabecalho(c, height - 2*cm)
    soma_total = 0
    cont_unidades = 0
    ref_data_ant = ""  # Guarda a última data da coluna Anterior
    ref_data_atu = ""  # Guarda a última data da coluna Atual

    for row in dados:
        # 1. Tratamento de Dados (Prevenção de erros de tipo)
        unid = str(row[0])
        try:
            atu = float(row[1]) if row[1] is not None else 0.0
            ant = float(row[2]) if row[2] is not None else 0.0
        except:
            atu, ant = 0.0, 0.0

        # 2. Cálculos de Consumo
        consumo = max(0, atu - ant)
        soma_total += consumo
        if row[1] is not None:
            cont_unidades += 1

        # 3. Obtenção de Textos Formatados (Usa a função modular de data)
        txt_col_ant, ref_data_ant = formatar_celula_data(
            ant, row[4], ref_data_ant)
        txt_col_atu, ref_data_atu = formatar_celula_data(
            atu, row[3], ref_data_atu)

        # 4. Impressão das Colunas no PDF
        c.setFont("Helvetica", 9)
        c.drawString(1.5*cm, y, unid)
        c.drawString(4.0*cm, y, txt_col_ant)
        c.drawString(10.0*cm, y, txt_col_atu)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(16.0*cm, y, f"{consumo:8.2f} m³")

        # 5. Controle de Salto de Linha e Nova Página
        y -= 0.5*cm
        if y < 3*cm:
            c.showPage()
            y = desenhar_cabecalho(c, height - 2*cm)
            ref_data_ant = ref_data_atu = ""  # Força exibir a data no topo da folha nova

    # 6. Finalização e Rodapé
    c.line(1.5*cm, y + 0.3*cm, 19.5*cm, y + 0.3*cm)
    c.setFont("Helvetica-Bold", 10)
    media = soma_total / cont_unidades if cont_unidades > 0 else 0
    c.drawString(1.5*cm, y - 0.5*cm,
                 f"TOTAL CONDOMÍNIO: {soma_total:.2f} m³  |  MÉDIA: {media:.2f} m³")

    c.save()
    if os.name == 'nt':
        os.startfile(caminho_pdf)  # Abre o PDF automaticamente no Windows
    return caminho_pdf

# =============================================================================
# 4. MÓDULO DE INTERFACE (Flet UI)
# =============================================================================


def montar_tela_relatorios(page, voltar):
    """
    Constrói a interface de botões e gerencia os eventos de clique.
    """
    # Dicionário local para persistir o caminho do último PDF gerado
    estado = {"ultimo_gerado": None}

    def btn_gerar_leitura(e):
        leituras = db.buscar_todas_leituras()
        if leituras:
            estado["ultimo_gerado"] = gerar_relatorio_consumo(leituras)
            page.snack_bar = ft.SnackBar(
                ft.Text("Relatório PDF criado com sucesso!"), open=True)
            page.update()

    def btn_gerar_etiquetas(e):
        # Extrai apenas os nomes das unidades para gerar os QR Codes
        lista_unids = [str(u[0]) for u in db.buscar_todas_leituras()]
        if lista_unids:
            # Aqui você pode chamar sua função de etiquetas QR (gerar_pdf_etiquetas)
            page.snack_bar = ft.SnackBar(
                ft.Text("Etiquetas geradas!"), open=True)
            page.update()

    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column([
            ft.Text("Painel de Relatórios", size=28,
                    color="white", weight="bold"),
            ft.Divider(color="white10"),
            ft.Container(height=20),

            ft.ElevatedButton("GERAR RELATÓRIO MENSAL", icon=ft.Icons.PICTURE_AS_PDF,
                              on_click=btn_gerar_leitura, width=350, height=50),

            ft.ElevatedButton("GERAR ETIQUETAS QR", icon=ft.Icons.QR_CODE,
                              on_click=btn_gerar_etiquetas, width=350, height=50, bgcolor="blue800", color="white"),

            ft.Container(height=20),
            ft.TextButton("Sair dos Relatórios", on_click=lambda _: voltar())
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
