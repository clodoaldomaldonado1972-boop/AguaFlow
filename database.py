import sqlite3
from datetime import datetime


def criar_banco():
    """Cria o arquivo do banco e a tabela se não existirem."""
    conn = sqlite3.connect("medicoes.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leituras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unidade TEXT NOT NULL,
        leitura_agua REAL,
        leitura_gas TEXT,
        data TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()


def checar_leitura_existente(unidade):
    """Verifica se a unidade já foi lida no dia de hoje."""
    criar_banco()  # Garante que a tabela existe
    hoje = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("medicoes.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM leituras WHERE unidade = ? AND data = ?", (
            unidade, hoje)
    )
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None


def salvar_leitura(unidade, agua, gas):
    """Grava a leitura no banco de dados."""
    criar_banco()
    hoje = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("medicoes.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leituras (unidade, leitura_agua, leitura_gas, data) VALUES (?, ?, ?, ?)",
        (unidade, agua, gas, hoje)
    )
    conn.commit()
    conn.close()
    print(f"Dados salvos: {unidade} - Água: {agua}")


def listar_todas_leituras():
    """Retorna tudo o que foi lido para mostrar na tela de relatório."""
    conn = sqlite3.connect("medicoes.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unidade, leitura_agua, leitura_gas, data FROM leituras ORDER BY id DESC")
    dados = cursor.fetchall()
    conn.close()
    return dados


def zerar_historico():
    conn = sqlite3.connect("medicoes.db")
    cursor = conn.cursor()
    # Este comando apaga todos os registros da tabela, mas mantém a estrutura
    cursor.execute("DELETE FROM leituras")
    conn.commit()
    conn.close()
    print("Banco de dados resetado!")


if __name__ == "__main__":
    # Isso só roda se você executar o database.py diretamente
    print("Testando conexão...")
    criar_banco()
    leituras = listar_todas_leituras()
    print(f"Total de registros encontrados: {len(leituras)}")
    for l in leituras:
        print(l)
