import sqlite3
from datetime import datetime

def get_dados():
    """Retorna as leituras calculando o consumo para o relatório"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Como 'consumo' e 'data' não são colunas reais na sua tabela 'leituras',
    # nós calculamos o consumo (atual - anterior) e pegamos a data de hoje.
    cursor.execute("""
        SELECT 
            id, 
            unidade, 
            leitura_anterior, 
            leitura_atual, 
            (IFNULL(leitura_atual, 0) - leitura_anterior) AS consumo,
            date('now') AS data, 
            status 
        FROM leituras 
        WHERE leitura_atual IS NOT NULL
        ORDER BY unidade ASC
    """)
    
    dados = cursor.fetchall()
    conn.close()
    return dados

def get_connection():
    """Estabelece a conexão com o banco de dados SQLite."""
    return sqlite3.connect("aguaflow.db", check_same_thread=False)

def init_db():
    """Inicializa as tabelas com os nomes de colunas corretos."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Criando a tabela principal com os nomes que o medicao.py espera
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            leitura_anterior REAL DEFAULT 0.0,
            leitura_atual REAL,
            status TEXT DEFAULT 'pendente'
        )
    """)
    
    # Criando a tabela de histórico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT,
            mes_referencia TEXT,
            consumo REAL,
            leitura_final REAL
        )
    """)
    
    # Se a tabela estiver vazia, popula com os apartamentos
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        unidades = []
        # Gera apartamentos do 16 ao 1 (finais 1 a 6)
        for andar in range(16, 0, -1):
            for final in range(6, 0, -1):
                unidades.append((f"{andar}{final}", 0.0))
        
        unidades.append(('LAZER', 0.0))
        unidades.append(('GERAL', 0.0))
        
        cursor.executemany("INSERT INTO leituras (unidade, leitura_anterior) VALUES (?, ?)", unidades)
        conn.commit()
    
    conn.close()

def buscar_proximo_pendente():
    conn = get_connection()
    cursor = conn.cursor()
    # Busca a primeira unidade onde a leitura_atual ainda é NULA
    cursor.execute("SELECT id, unidade, leitura_anterior FROM leituras WHERE leitura_atual IS NULL LIMIT 1")
    res = cursor.fetchone()
    conn.close()
    return res

def registrar_leitura(id_unidade, valor, status="lido"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE leituras SET leitura_atual = ?, status = ? WHERE id = ?", (valor, status, id_unidade))
    conn.commit()
    conn.close()

def fechar_mes_e_resetar():
    """Migra para histórico e prepara o próximo mês."""
    conn = get_connection()
    cursor = conn.cursor()
    mes_ano = datetime.now().strftime("%m/%Y")

    # 1. Salva no Histórico
    cursor.execute("""
        INSERT INTO historico_consumo (unidade, mes_referencia, consumo, leitura_final)
        SELECT unidade, ?, (leitura_atual - leitura_anterior), leitura_atual 
        FROM leituras 
        WHERE status = 'lido'
    """, (mes_ano,))

    # 2. Faz o 'Rollover' (A atual vira anterior para o próximo mês)
    cursor.execute("""
        UPDATE leituras 
        SET leitura_anterior = CASE WHEN status = 'lido' THEN leitura_atual ELSE leitura_anterior END,
            leitura_atual = NULL,
            status = 'pendente'
    """)
    
    conn.commit()
    conn.close()