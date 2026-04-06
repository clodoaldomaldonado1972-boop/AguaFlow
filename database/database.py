import os
import sqlite3
from datetime import datetime as dt
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


class Database:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")

    @classmethod
    @contextmanager
    def get_db(cls):
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        with cls.get_db() as conn:
            cursor = conn.cursor()
            # 1. Cria tabelas essenciais
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS unidades (id TEXT PRIMARY KEY)")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unidade TEXT,
                    valor REAL,
                    tipo_leitura TEXT,
                    data_leitura TEXT,
                    sincronizado INTEGER DEFAULT 0
                )
            """)

            # 2. Popula unidades (98 registros do Vivere Prudente)
            todas_unidades = [f"Apto {a}{f}" for a in range(
                16, 0, -1) for f in range(6, 0, -1)]

            # PRESERVAÇÃO DE DADOS: Usa INSERT OR IGNORE para não apagar o que já existe
            cursor.executemany(
                "INSERT OR IGNORE INTO unidades (id) VALUES (?)",
                [(u,) for u in todas_unidades]
            )
            conn.commit()

    @classmethod
    def buscar_proximo_pendente(cls, tipo_filtro="Água"):
        """Busca a próxima unidade pendente de forma segura."""
        with cls.get_db() as conn:
            cursor = conn.cursor()

            # Lógica de filtro para "Ambos" ou individual
            if tipo_filtro == "Ambos":
                query = """
                    SELECT id FROM unidades 
                    WHERE (id NOT IN (SELECT unidade FROM leituras WHERE tipo_leitura = 'Água')
                    OR id NOT IN (SELECT unidade FROM leituras WHERE tipo_leitura = 'Gás'))
                    AND id NOT IN ('Lazer Gás', 'Geral Água')
                """
                cursor.execute(query)
            else:
                # Prevenção contra SQL Injection usando parâmetros '?'
                query = """
                    SELECT id FROM unidades 
                    WHERE id NOT IN (SELECT unidade FROM leituras WHERE tipo_leitura = ?) 
                    AND id NOT IN ('Lazer Gás', 'Geral Água')
                """
                cursor.execute(query, (tipo_filtro,))

            # Correção de Typos: 'pndentes' e 'peendentes'
            pendentes = [row[0] for row in cursor.fetchall()]

            if not pendentes:
                return None

            # Ordenação Vivere Prudente (166...11)
            def order_vivere(u):
                num_str = u.replace("Apto ", "")
                # Ordena decrescente pelo andar e pelo final
                return (-int(num_str[:-1]), -int(num_str[-1]))

            pendentes.sort(key=order_vivere)
            escolhido = pendentes[0]

            # Retorna a tupla esperada pela view de medição
            return (escolhido, escolhido, tipo_filtro)

    @classmethod
    def registrar_leitura(cls, unidade, valor, tipo_leitura):
        """Salva a leitura no banco de dados local com tratamento de erros."""
        agora = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Limpeza de input para garantir que o valor seja float
            valor_limpo = float(str(valor).replace(',', '.'))
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO leituras (unidade, valor, tipo_leitura, data_leitura, sincronizado) VALUES (?, ?, ?, ?, 0)",
                    (unidade, valor_limpo, tipo_leitura, agora)
                )
                conn.commit()
                return {'sucesso': True}
        except Exception as e:
            return {'sucesso': False, 'mensagem': str(e)}

    @classmethod
    def get_leituras(cls, status=None, sincronizado=None):
        """Busca leituras com filtros opcionais."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM leituras"
                params = []
                conditions = []
                if status:
                    conditions.append("status = ?")
                    params.append(status)
                if sincronizado is not None:
                    conditions.append("sincronizado = ?")
                    params.append(sincronizado)
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                cursor.execute(query, params)
                rows = cursor.fetchall()
                dados = [dict(row) for row in rows]
                return {'sucesso': True, 'dados': dados}
        except Exception as e:
            return {'sucesso': False, 'mensagem': str(e)}

    @classmethod
    def get_connection(cls):
        """Retorna uma conexão para uso manual."""
        return sqlite3.connect(cls.DB_PATH, check_same_thread=False)

    @classmethod
    def buscar_todas_leituras(cls):
        """Busca todas as leituras."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM leituras")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Erro ao buscar leituras: {e}")
            return []

    @classmethod
    def buscar_relatorio_geral(cls):
        """Retorna dados consolidados para geração de relatório mensal."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT unidade, valor, data_leitura FROM leituras "
                    "ORDER BY unidade, data_leitura DESC"
                )
                linhas = cursor.fetchall()

                relatorio = {}
                for linha in linhas:
                    unidade = linha[0]
                    if unidade not in relatorio:
                        relatorio[unidade] = [linha[1], 0.0, linha[2], ""]
                    elif relatorio[unidade][1] == 0.0:
                        relatorio[unidade][1] = linha[1]
                        relatorio[unidade][3] = linha[2]

                resultados = []
                for unidade, valores in sorted(relatorio.items()):
                    atual, anterior, data_atual, data_anterior = valores
                    resultados.append(
                        (unidade, atual, anterior, data_atual, data_anterior))

                return resultados
        except Exception as e:
            print(f"Erro ao buscar relatório geral: {e}")
            return []
