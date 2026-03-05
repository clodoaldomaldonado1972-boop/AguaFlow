import sqlite3
from datetime import datetime # Import necessário para o fechar_mes

def get_connection():
    """Estabelece a conexão com o banco de dados SQLite."""
    return sqlite3.connect("aguaflow.db", check_same_thread=False)

def init_db():
    """Inicializa as tabelas principal e de histórico."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela Principal
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            agua_anterior REAL DEFAULT 0.0,
            agua_atual REAL DEFAULT 0.0,
            gas_anterior REAL DEFAULT 0.0,
            gas_atual REAL DEFAULT 0.0,
            status TEXT DEFAULT 'pendente'
        )
    """)
    
    # NOVA: Tabela de Histórico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT,
            mes_referencia TEXT,
            tipo TEXT, -- 'agua' ou 'gas'
            consumo REAL,
            leitura_final REAL
        )
    """)
    
    # Popula unidades se estiver vazio
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        unidades = []
        for andar in range(16, 0, -1):
            for final in range(6, 0, -1):
                unidades.append((f"{andar}{final}",))
        unidades.append(('LAZER',))
        unidades.append(('GERAL',))
        cursor.executemany("INSERT INTO leituras (unidade) VALUES (?)", unidades)
        conn.commit()
    conn.close()

def buscar_proximo_pendente():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leituras WHERE status = 'pendente' ORDER BY id ASC LIMIT 1")
    resultado = cursor.fetchone()
    conn.close()
    return resultado

def registrar_leitura(id_unidade, valor, tipo="agua", status="lido"):
    conn = get_connection()
    cursor = conn.cursor()
    coluna = "agua_atual" if tipo == "agua" else "gas_atual"
    cursor.execute(f"UPDATE leituras SET {coluna} = ?, status = ? WHERE id = ?", (valor, status, id_unidade))
    conn.commit()
    conn.close()

def fechar_mes_e_resetar():
    """Migra dados para histórico e prepara o banco para o novo mês."""
    conn = get_connection()
    cursor = conn.cursor()
    mes_ano = datetime.now().strftime("%m/%Y")

    # 1. Salva Água no Histórico (Apenas se status for 'lido' e houve consumo)
    cursor.execute("""
        INSERT INTO historico_consumo (unidade, mes_referencia, tipo, consumo, leitura_final)
        SELECT unidade, ?, 'agua', (agua_atual - agua_anterior), agua_atual 
        FROM leituras 
        WHERE status = 'lido' AND (agua_atual - agua_anterior) > 0
    """, (mes_ano,))

    # 2. Prepara o próximo mês
    # Se foi 'lido', a atual vira anterior. Se foi 'pulado', mantém a anterior antiga.
    cursor.execute("""
        UPDATE leituras 
        SET agua_anterior = CASE WHEN status = 'lido' THEN agua_atual ELSE agua_anterior END,
            gas_anterior = CASE WHEN status = 'lido' THEN gas_atual ELSE gas_anterior END,
            agua_atual = 0.0,
            gas_atual = 0.0,
            status = 'pendente'
    """)
    
    conn.commit()
    conn.close()

def calcular_media_anual(unidade, tipo="agua"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT AVG(consumo) FROM historico_consumo 
        WHERE unidade = ? AND tipo = ? AND consumo > 0
        ORDER BY id DESC LIMIT 12
    """, (unidade, tipo))
    media = cursor.fetchone()[0]
    conn.close()
    return media if media else 0.0
