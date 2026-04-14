import os
import sqlite3
from datetime import datetime as dt
from contextlib import contextmanager
from dotenv import load_dotenv

# Carrega configurações do .env se existir
load_dotenv()

class Database:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")
    
    @classmethod
    @contextmanager
    def get_db(cls):
        """Gerencia a conexão SQLite com suporte a multi-threading e timeout."""
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        # Timeout de 30s evita erros de 'Event loop is closed' no Flet
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        """Inicializa as tabelas para o Dashboard e Etiquetas."""
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
        """Salva a medição no banco de dados."""
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
        """Alimenta o Dashboard com o histórico completo."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT unidade, leitura_agua, leitura_gas, data_leitura FROM leituras ORDER BY id DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    @classmethod
    def buscar_relatorio_geral(cls):
        """Busca a leitura mais recente de cada unidade para Relatórios."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT unidade, leitura_agua, leitura_gas, data_leitura 
                    FROM leituras 
                    GROUP BY unidade 
                    ORDER BY unidade ASC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    @staticmethod
    def _gerar_lista_unidades():
        """
        Gera a lista otimizada para o Vivere Prudente (96 aptos + especiais).
        Remove permanentemente o prefixo 'UNID'.
        """
        lista = []
        condominio = "Vivere Prudente"
        
        # Unidades dos Apartamentos (96 total)
        for andar in range(16, 0, -1):
            for apto in range(1, 7):
                numero = f"{andar}{apto}" # Apenas o número puro
                
                lista.append({
                    "id": f"{numero}_A",
                    "unidade": numero,
                    "tipo": "Água",
                    "condominio": condominio
                })
                lista.append({
                    "id": f"{numero}_G",
                    "unidade": numero,
                    "tipo": "Gás",
                    "condominio": condominio
                })
        
        # Unidades Especiais
        lista.append({"id": "GERAL_A", "unidade": "GERAL", "tipo": "Água", "condominio": condominio})
        lista.append({"id": "LAZER_G", "unidade": "LAZER", "tipo": "Gás", "condominio": condominio})
        
        return lista