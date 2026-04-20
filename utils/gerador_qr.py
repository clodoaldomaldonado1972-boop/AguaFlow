import os
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from database.database import Database

# --- CONFIGURAÇÕES DE LAYOUT (Etiquetas Otimizadas) ---
COLUNAS = 5  
LINHAS = 10  
NOME_CONDOMINIO = "VIVERE PRUDENTE"

def gerar_qr_codes(filtro_tipo="AMBOS", unidade_alvo=None):
    """
    Gera PDF de etiquetas consultando a tabela de MEDIDORES.
    Ideal para identificação física dos dispositivos de leitura.
    """
    print(f"\n[GERADOR] 🚀 Iniciando criação de etiquetas: {filtro_tipo}")

    try:
        # 1. Configuração de Saída e Pastas
        # IHC: Centralizando arquivos na pasta storage para facilitar gestão no Android
        pasta_output = os.path.join(os.getcwd(), "storage")
        os.makedirs(pasta_output, exist_ok=True)
        
        nome_arquivo = f"Etiquetas_{filtro_tipo}.pdf"
        caminho_final = os.path.join(pasta_output, nome_arquivo)

        # 2. Busca de Dados (Integração com Database)
        # Busca medidores específicos ou todos
        medidores_db = Database.get_medidores(filtro_tipo)
        
        if not medidores_db:
            print("[GERADOR] ⚠️ Nenhum medidor encontrado no banco de dados.")
            return None

        # 3. Preparação do Canvas (PDF A4)
        c = canvas.Canvas(caminho_final, pagesize=A4)
        largura_a4, altura_a4 = A4
        
        # Cálculos de Medidas (em pontos)
        w_cel = largura_a4 / COLUNAS
        h_cel = altura_a4 / LINHAS
        
        x_atual = 0
        y_atual = altura_a4 - h_cel
        count = 0

        # 4. Loop de Criação das Etiquetas
        for idx, item in enumerate(medidores_db):
            m_id = str(item.get('id_qrcode', 'ID_ERRO'))
            u_id = str(item.get('unidade_id', '???'))
            tipo = str(item.get('tipo', 'Geral'))

            # Desenha borda da etiqueta (Auxílio no corte manual)
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.setLineWidth(0.5)
            c.rect(x_atual + 2, y_atual + 2, w_cel - 4, h_cel - 4, stroke=1)

            # Geração do QR Code
            # O texto do QR contém o ID único que o ScannerOCR buscará
            qr = qrcode.QRCode(version=1, border=1, box_size=10)
            qr.add_data(f"AGUAFLOW|{m_id}")
            qr.make(fit=True)
            
            img_qr = qr.make_image(fill_color="black", back_color="white")
            
            # Caminho temporário único para evitar erros de permissão
            temp_img = os.path.join(pasta_output, f"temp_qr_{idx}.png")
            img_qr.save(temp_img)

            # Desenha o QR Code centralizado na célula
            c.drawImage(ImageReader(temp_img), x_atual + (w_cel-60)/2, y_atual + 25, width=60, height=60)

            # Legendas e Identificação (IHC: Fonte legível)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(x_atual + w_cel/2, y_atual + 15, NOME_CONDOMINIO)
            
            c.setFont("Helvetica", 9)
            c.drawCentredString(x_atual + w_cel/2, y_atual + 5, f"UNID: {u_id} - {tipo.upper()}")

            # Limpeza do arquivo temporário imediatamente após uso
            if os.path.exists(temp_img): 
                os.remove(temp_img)

            # Lógica de Posicionamento (Grade)
            count += 1
            if count % COLUNAS == 0:
                x_atual = 0
                y_atual -= h_cel
            else:
                x_atual += w_cel

            # Quebra de Página
            if count % (COLUNAS * LINHAS) == 0:
                c.showPage()
                x_atual = 0
                y_atual = altura_a4 - h_cel

        c.save()
        print(f"[GERADOR] ✅ PDF gerado com sucesso em: {caminho_final}")
        return caminho_final

    except Exception as e:
        print(f"[GERADOR] ❌ Erro crítico na geração: {e}")
        return None