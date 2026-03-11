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

    # Tabela de Leituras (Espinha dorsal do sistema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            leitura_anterior REAL DEFAULT 0.0,
            data_anterior TEXT,
            leitura_atual REAL DEFAULT NULL, 
            status TEXT DEFAULT 'pendente',
            data_leitura TEXT
        )
    """)

    # Tabela de Histórico (Para análises futuras e evolução do Projeto Integrador)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT,
            mes_referencia TEXT,
            consumo REAL,
            leitura_final REAL
        )
    """)

    # População inicial (16º ao 1º andar + Áreas Comuns)
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        print("📁 Gerando unidades do Vivere (16º ao 1º)...")
        unidades = []
        # Ordem decrescente conforme regra de negócio definida pelo grupo
        for andar in range(16, 0, -1):
            for final in range(6, 0, -1):
                unidades.append((f"{andar}{final}", 0.0))
        unidades.append(('LAZER', 0.0))
        unidades.append(('GERAL', 0.0))

        cursor.executemany(
            "INSERT INTO leituras (unidade, leitura_anterior, status) VALUES (?, ?, 'pendente')",
            unidades
        )
        conn.commit()
    conn.close()

# =============================================================================
# 2. INTELIGÊNCIA DE NEGÓCIO E SEQUENCIAMENTO
# =============================================================================


def buscar_proximo_pendente():
    """Busca a próxima unidade na fila (Ordem por ID/Andar)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, unidade, leitura_anterior 
        FROM leituras 
        WHERE status = 'pendente'
        ORDER BY id ASC LIMIT 1
    """)
    res = cursor.fetchone()
    conn.close()
    return res


def verificar_esquecimento_superior(id_atual):
    """
    Verifica se existe alguma unidade com ID menor (andar superior) 
    que ainda está como 'pendente'. Retorna o nome da unidade esquecida.
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
# 3. MÓDULO DE ESTATÍSTICAS (Cálculo Separado do PDF)
# =============================================================================


def calcular_estatisticas_consumo():
    """
    Calcula totais e médias separando unidades residenciais de globais.
    Essencial para a modularidade: o relatório apenas pede esses dados.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unidade, leitura_atual, leitura_anterior FROM leituras")
    dados = cursor.fetchall()
    conn.close()

    total_condominio = 0
    total_residencial = 0
    cont_apartamentos = 0
    unidades_especiais = ['LAZER', 'GERAL']

    for row in dados:
        atu = float(row[1]) if row[1] is not None else 0.0
        ant = float(row[2]) if row[2] is not None else 0.0
        consumo = max(0, atu - ant)

        total_condominio += consumo

        # Filtra para cálculo de média residencial realista
        if row[0].upper() not in unidades_especiais:
            total_residencial += consumo
            if row[1] is not None:  # Só conta se foi lido (mesmo que seja 0.0)
                cont_apartamentos += 1

    media_res = total_residencial / cont_apartamentos if cont_apartamentos > 0 else 0

    return {
        "total_condominio": total_condominio,
        "media_residencial": media_res,
        "cont_apto": cont_apartamentos
    }

# =============================================================================
# 4. PERSISTÊNCIA E MANUTENÇÃO
# =============================================================================


def registrar_leitura(id_unidade, valor, status='concluido'):
    """Salva a leitura e registra o carimbo de data/hora."""
    conn = get_connection()
    cursor = conn.cursor()
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        UPDATE leituras 
        SET leitura_atual = ?, status = ?, data_leitura = ? 
        WHERE id = ?
    """, (valor, status, agora, id_unidade))
    conn.commit()
    conn.close()


def registrar_leitura_automatica_zero(nome_unidade):
    """Utilizado pelo alerta de esquecimento para limpar pendências com valor zero."""
    conn = get_connection()
    cursor = conn.cursor()
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        UPDATE leituras 
        SET leitura_atual = 0.0, status = 'esquecido', data_leitura = ? 
        WHERE unidade = ?
    """, (agora, nome_unidade))
    conn.commit()
    conn.close()


def resetar_mes_novo():
    """Realiza o 'fechamento' do mês e prepara o próximo ciclo."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE leituras 
            SET 
                leitura_anterior = IFNULL(leitura_atual, leitura_anterior),
                data_anterior = IFNULL(data_leitura, data_anterior),
                leitura_atual = NULL,
                status = 'pendente', 
                data_leitura = NULL
        """)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro no Reset: {e}")
        return False


def buscar_todas_leituras():
    """Retorna o dataset completo para o gerador de relatórios."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT unidade, leitura_atual, leitura_anterior, data_leitura, data_anterior 
        FROM leituras
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados
