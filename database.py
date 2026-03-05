import sqlite3
from datetime import datetime

DB_NAME = "aguaflow.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Criando a tabela do zero com a sintaxe exata
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            bloco TEXT,
            leitura_valor REAL,
            data_leitura TEXT,
            status TEXT DEFAULT 'pendente'
        )
    """)
    
    # Conferindo se o banco está vazio para colocar os apartamentos de teste
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        apartamentos = [
            ('101', 'A'), ('102', 'A'), ('201', 'A'),
            ('101', 'B'), ('102', 'B'), ('201', 'B')
        ]
        for apto, bloco in apartamentos:
            cursor.execute(
                "INSERT INTO leituras (unidade, bloco, status) VALUES (?, ?, 'pendente')",
                (apto, bloco)
            )
    
    conn.commit()
    conn.close()

def buscar_proximo_pendente():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, unidade, bloco FROM leituras WHERE status = 'pendente' ORDER BY id LIMIT 1"
    )
    resultado = cursor.fetchone()
    conn.close()
    return resultado

def salvar_leitura(id_registro, valor):
    data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE leituras 
        SET leitura_valor = ?, data_leitura = ?, status = 'concluido'
        WHERE id = ?
    """, (valor, data_hoje, id_registro))
    conn.commit()
    conn.close()

def resetar_todas_leituras():
    conn = get_connection()
    cursor = conn.cursor()
    # Limpa os valores e volta o status para pendente
    cursor.execute("UPDATE leituras SET leitura_valor = NULL, data_leitura = NULL, status = 'pendente'")
    conn.commit()
    conn.close()
    print("🔄 Banco de dados resetado para novas leituras!")
        