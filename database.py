import sqlite3
import datetime

# =============================================================================
# 1. INFRAESTRUTURA DE CONEXÃO
# =============================================================================


def get_connection():
    """Conexão única padronizada para todo o sistema."""
    return sqlite3.connect("aguaflow.db", check_same_thread=False)


def init_db():
    """Inicializa o banco, tabelas e população inicial do Vivere Prudente."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de Leituras: Adicionamos o campo 'tipo' para Água/Gás
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            leitura_anterior REAL DEFAULT 0.0,
            data_anterior TEXT,
            leitura_atual REAL DEFAULT NULL, 
            tipo TEXT DEFAULT 'AGUA',
            status TEXT DEFAULT 'pendente',
            data_leitura TEXT
        )
    """)

    # População inicial (Garante a ordem física das escadas: 16 -> 1)
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        print("📁 Gerando unidades do Vivere (16º ao 1º)...")
        unidades = []
        for andar in range(16, 0, -1):
            for final in range(6, 0, -1):
                # Registramos Água e Gás para cada apartamento
                unidades.append((f"{andar}{final}", 0.0, 'AGUA'))
                unidades.append((f"{andar}{final}", 0.0, 'GAS'))

        unidades.append(('LAZER', 0.0, 'AGUA'))
        unidades.append(('GERAL', 0.0, 'AGUA'))

        cursor.executemany(
            "INSERT INTO leituras (unidade, leitura_anterior, tipo, status) VALUES (?, ?, ?, 'pendente')",
            unidades
        )
        conn.commit()
    conn.close()

# =============================================================================
# 2. INTELIGÊNCIA DE NEGÓCIO E SEQUENCIAMENTO
# =============================================================================


def buscar_proximo_pendente():
    """Busca a próxima unidade na fila (Ordem por ID que segue a descida)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, unidade, leitura_anterior, tipo 
        FROM leituras 
        WHERE status = 'pendente'
        ORDER BY id ASC LIMIT 1
    """)
    res = cursor.fetchone()
    conn.close()
    return res


def verificar_esquecimento_superior(id_atual):
    """
    O Coração do Alerta: Se o ID atual é 10, mas o ID 9 está pendente,
    significa que o leiturista pulou alguém no andar de cima.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT unidade FROM leituras 
        WHERE id < ? AND status = 'pendente' 
        ORDER BY id ASC LIMIT 1
    """, (id_atual,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

# =============================================================================
# 3. PERSISTÊNCIA E REGISTRO
# =============================================================================


def registrar_leitura(id_unidade, valor):
    """
    Salva a leitura. Se o valor for 0, marca como 'vazio'.
    """
    conn = get_connection()
    cursor = conn.cursor()
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

    # Define status inteligente
    novo_status = 'concluido' if valor > 0 else 'vazio'

    cursor.execute("""
        UPDATE leituras 
        SET leitura_atual = ?, status = ?, data_leitura = ? 
        WHERE id = ?
    """, (valor, novo_status, agora, id_unidade))
    conn.commit()
    conn.close()


def registrar_pulo_automatico(nome_unidade):
    """Registra valor zero para unidades ignoradas propositalmente."""
    conn = get_connection()
    cursor = conn.cursor()
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        UPDATE leituras 
        SET leitura_atual = 0.0, status = 'vazio', data_leitura = ? 
        WHERE unidade = ? AND status = 'pendente'
    """, (agora, nome_unidade))
    conn.commit()
    conn.close()

# =============================================================================
# 4. ESTATÍSTICAS E FECHAMENTO
# =============================================================================


def calcular_estatisticas_consumo():
    """Útil para o painel de controle e para o PDF final."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unidade, leitura_atual, leitura_anterior FROM leituras WHERE status != 'pendente'")
    dados = cursor.fetchall()
    conn.close()

    total = sum([max(0, (row[1] or 0) - (row[2] or 0)) for row in dados])
    cont = len(dados)

    return {
        "total_consumo": total,
        "media": total / cont if cont > 0 else 0,
        "lidos": cont
    }
