import os
import sqlite3
from datetime import datetime as dt
from contextlib import contextmanager
from dotenv import load_dotenv

# Carrega configurações do .env se existir
load_dotenv()

class Database:
    # AJUSTE 1: Caminho absoluto para evitar erro de "AttributeError" ou "File Not Found"
    # Isso garante que o SQLite sempre saiba onde criar o arquivo, independente de onde o app é iniciado.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")
    
    @classmethod
    @contextmanager
    def get_db(cls):
        """Gerencia a conexão SQLite de forma segura (Context Manager)."""
        # Garante que a pasta 'database' exista no computador
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        """Inicializa as tabelas e garante as colunas necessárias para o Dashboard."""
        with cls.get_db() as conn:
            cursor = conn.cursor()
            # Tabela de leituras sincronizada com 'leitura_agua' e 'leitura_gas'
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unidade TEXT NOT NULL,
                    leitura_agua REAL NOT NULL,
                    leitura_gas REAL,
                    data_leitura TEXT
                )
            """)
            # Tabela de unidades estáticas
            cursor.execute("CREATE TABLE IF NOT EXISTS unidades (id TEXT PRIMARY KEY)")
            conn.commit()

    @staticmethod
    def registrar_leitura(unidade, valor_agua, valor_gas=None):
        """Salva a medição no banco. Note que os nomes batem com os selects do Dashboard."""
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                data_agora = dt.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO leituras (unidade, leitura_agua, leitura_gas, data_leitura)
                    VALUES (?, ?, ?, ?)
                """, (unidade, valor_agua, valor_gas, data_agora))
                conn.commit()
                return {"sucesso": True, "mensagem": "Leitura salva!"}
        except Exception as e:
            return {"sucesso": False, "mensagem": f"Erro técnico: {e}"}

    @classmethod
    def buscar_ultima_unidade_lida(cls):
        """Busca a última unidade para o fluxo automático (166 -> 165)."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT unidade FROM leituras ORDER BY id DESC LIMIT 1")
                res = cursor.fetchone()
                return res['unidade'] if res else None
        except Exception:
            return None # Proteção caso a tabela ainda não exista

    @classmethod
    def buscar_todas_leituras(cls):
        """Alimenta o Dashboard. Usa os nomes de campos que o exportador e views esperam."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT unidade, leitura_agua, leitura_gas, data_leitura 
                    FROM leituras 
                    ORDER BY id DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Erro no Banco (Dashboard): {e}")
            return []

    @classmethod
    def buscar_relatorio_geral(cls):
        """Busca a leitura mais recente de cada unidade para o Relatório PDF/CSV."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                # GROUP BY garante que só pegamos a última leitura de cada apartamento
                cursor.execute("""
                    SELECT unidade, leitura_agua, leitura_gas, data_leitura 
                    FROM leituras 
                    GROUP BY unidade 
                    ORDER BY unidade ASC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Erro no Banco (Relatório): {e}")
            return []

    @staticmethod
    def _gerar_lista_unidades():
        """Gera a lista estática de unidades (Andares 16 ao 1, Apto 1 ao 6)."""
        lista = []
        for andar in range(16, 0, -1):
            for apto in range(1, 7):
                lista.append(f"Apto {andar}{apto}")
        return lista