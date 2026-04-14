import os
import sqlite3
from datetime import datetime as dt
from contextlib import contextmanager
from dotenv import load_dotenv

# Carrega configurações do .env se existir
load_dotenv()

class Database:
    # Define o caminho para o banco de dados no diretório atual
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")
    
    @classmethod
    @contextmanager
    def get_db(cls):
        """Gerencia a conexão SQLite de forma segura (Context Manager)."""
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        """Inicializa as tabelas do Dashboard."""
        with cls.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unidade TEXT NOT NULL,
                    leitura_agua REAL NOT NULL,
                    leitura_gas REAL,
                    data_leitura TEXT
                )
            """)
            cursor.execute("CREATE TABLE IF NOT EXISTS unidades (id TEXT PRIMARY KEY)")
            conn.commit()

    @classmethod
    def get_unidades(cls):
        """Retorna a lista higienizada para o Gerador."""
        return cls._gerar_lista_unidades()

    @staticmethod
    def registrar_leitura(unidade, valor_agua, valor_gas=None):
        """Salva a medição no banco."""
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
        """Busca a última unidade para o fluxo automático."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT unidade FROM leituras ORDER BY id DESC LIMIT 1")
                res = cursor.fetchone()
                return res['unidade'] if res else None
        except Exception:
            return None

    @classmethod
    def buscar_todas_leituras(cls):
        """Alimenta o Dashboard."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT unidade, leitura_agua, leitura_gas, data_leitura FROM leituras ORDER BY id DESC")
                return [dict(row) for row in conn.cursor().fetchall()]
        except Exception:
            return []

    @staticmethod
    def _gerar_lista_unidades():
        """
        Gera a lista otimizada para o Vivere Prudente:
        - Removemos o 'UNID' e 'Apto' para deixar apenas o número.
        - Ajustado para evitar nomes duplicados como 'Agua Agua'.
        """
        lista = []
        condominio = "Vivere Prudente"
        
        # Unidades dos Apartamentos (96 aptos)
        for andar in range(16, 0, -1):
            for apto in range(1, 7):
                numero = f"{andar}{apto}"
                # Entrada para Água
                lista.append({
                    "id": f"{numero}_A",
                    "unidade": numero,
                    "tipo": "Água",
                    "condominio": condominio
                })
                # Entrada para Gás
                lista.append({
                    "id": f"{numero}_G",
                    "unidade": numero,
                    "tipo": "Gás",
                    "condominio": condominio
                })
        
        # Unidades Especiais (conforme imagem)
        lista.append({"id": "GERAL_A", "unidade": "GERAL", "tipo": "Água", "condominio": condominio})
        lista.append({"id": "LAZER_G", "unidade": "LAZER", "tipo": "Gás", "condominio": condominio})
        
        return lista