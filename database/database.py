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
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        # Timeout de 30s para evitar erro de 'Event loop is closed'
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
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
        """Retorna a lista de 96 unidades + extras sem o prefixo UNID."""
        return cls._gerar_lista_unidades()

    @staticmethod
    def _gerar_lista_unidades():
        lista = []
        condominio = "Vivere Prudente"
        
        # Gera 96 unidades (16 andares x 6 aptos)
        for andar in range(16, 0, -1):
            for apto in range(1, 7):
                numero = f"{andar}{apto}" # Apenas o número puro
                
                # Item para Água
                lista.append({
                    "id": f"{numero}_A",
                    "unidade": numero,
                    "tipo": "Água",
                    "condominio": condominio
                })
                # Item para Gás
                lista.append({
                    "id": f"{numero}_G",
                    "unidade": numero,
                    "tipo": "Gás",
                    "condominio": condominio
                })
        
        # Unidades Especiais (Geral e Lazer)
        lista.append({"id": "GERAL_A", "unidade": "GERAL", "tipo": "Água", "condominio": condominio})
        lista.append({"id": "LAZER_G", "unidade": "LAZER", "tipo": "Gás", "condominio": condominio})
        
        return lista

    @staticmethod
    def registrar_leitura(unidade, valor_agua, valor_gas=None):
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                data_agora = dt.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO leituras (unidade, leitura_agua, leitura_gas, data_leitura)
                    VALUES (?, ?, ?, ?)
                """, (unidade, valor_agua, valor_gas, data_agora))
                conn.commit()
                return {"sucesso": True}
        except Exception as e:
            return {"sucesso": False, "mensagem": str(e)}