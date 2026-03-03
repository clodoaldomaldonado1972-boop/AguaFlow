import sqlite3  # Biblioteca padrão para banco de dados local
from fpdf import FPDF  # Biblioteca para gerar o relatório PDF

# Função para conectar ao arquivo de banco de dados


def conectar():
    return sqlite3.connect("aguaflow.db", check_same_thread=False)

# Passo 1: Criar a tabela se ela não existir ao iniciar o app


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            leitura_agua REAL,
            leitura_gas REAL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Passo 2: Buscar a última leitura de água para calcular o consumo


def buscar_ultima_leitura(unidade):
    conn = conectar()
    cursor = conn.cursor()
    # Pega o valor da leitura_agua do registro mais recente daquela unidade
    cursor.execute(
        "SELECT leitura_agua FROM leituras WHERE unidade = ? ORDER BY data_hora DESC LIMIT 1", (unidade,))
    resultado = cursor.fetchone()
    conn.close()
    # Se não houver leitura anterior, retorna 0
    return resultado[0] if resultado else 0

# Passo 3: Salvar os dados digitados pelo leiturista


def salvar_leitura(unidade, agua, gas):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leituras (unidade, leitura_agua, leitura_gas)
        VALUES (?, ?, ?)
    """, (unidade, agua, gas))
    conn.commit()
    conn.close()
    print(f"✅ Dados de {unidade} salvos no banco!")

# Passo 4: Gerar o arquivo PDF com os dados do banco


def gerar_pdf_relatorio():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unidade, leitura_agua, leitura_gas, data_hora FROM leituras")
    dados = cursor.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Relatorio de Medicao - AguaFlow", ln=True, align="C")
    pdf.ln(10)  # Pula linha

    # Cabeçalho da tabela no PDF
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "Unidade", 1)
    pdf.cell(40, 10, "Agua (m3)", 1)
    pdf.cell(40, 10, "Gas (m3)", 1)
    pdf.cell(60, 10, "Data/Hora", 1)
    pdf.ln()

    # Preenchendo as linhas com os dados do SQLite
    pdf.set_font("Arial", "", 12)
    for linha in dados:
        pdf.cell(50, 10, str(linha[0]), 1)
        pdf.cell(40, 10, str(linha[1]), 1)
        pdf.cell(40, 10, str(linha[2]), 1)
        pdf.cell(60, 10, str(linha[3]), 1)
        pdf.ln()

    pdf.output("relatorio_aguaflow.pdf")
    return "relatorio_aguaflow.pdf"


# Executa a criação da tabela sempre que o script for carregado
criar_tabelas()
