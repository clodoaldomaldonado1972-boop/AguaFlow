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
    """Verifica se a unidade já foi lida no dia de hoje para evitar duplicados."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("medicoes.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM leituras WHERE unidade = ? AND data = ?", (
            unidade, hoy)
    )
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None


def salvar_leitura(unidade, agua, gas):
    """Grava a leitura no banco de dados."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("medicoes.db")
    cursor = conn.cursor()

    # Tratamento: se o gás vier vazio do app, vira "0"
    valor_gas = str(gas) if gas else "0"

    cursor.execute(
        "INSERT INTO leituras (unidade, leitura_agua, leitura_gas, data) VALUES (?, ?, ?, ?)",
        (unidade, agua, valor_gas, hoje)
    )

    conn.commit()
    conn.close()
    print(
        f"✅ Banco de Dados -> Unidade: {unidade} | Água: {agua} | Gás: {valor_gas}")


def listar_todas_leituras():
    """Retorna todos os registros ordenados do mais recente para o mais antigo."""
    conn = sqlite3.connect("medicoes.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unidade, leitura_agua, leitura_gas, data FROM leituras ORDER BY id DESC"
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def zerar_historico():
    """Apaga todos os dados da tabela (Cuidado!)."""
    conn = sqlite3.connect("medicoes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leituras")
    conn.commit()
    conn.close()
    print("⚠️ Histórico do banco de dados foi resetado!")


# Bloco de teste: roda apenas se você executar este arquivo diretamente
if __name__ == "__main__":
    print("--- Testando conexão com o Banco de Dados ---")
    criar_banco()
    leituras = listar_todas_leituras()
    print(f"Total de registros: {len(leituras)}")
