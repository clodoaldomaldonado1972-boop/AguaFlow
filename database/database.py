import os
import sqlite3
from contextlib import contextmanager
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

class Database:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")
    
    @classmethod
    @contextmanager
    def get_db(cls):
        """Gerencia a conexão SQLite local."""
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        """
        RESOLVE O ERRO: Inicializa as tabelas locais se necessário.
        Mantido para compatibilidade com a chamada no main.py.
        """
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
            conn.commit()
            print("[DATABASE] ✅ Banco local inicializado com sucesso.")

    @staticmethod
    def get_medidores(filtro_tipo="AMBOS"):
        """Busca os medidores na nova tabela do Supabase (163/164, etc)."""
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            
            if not url or not key:
                print("❌ Erro: Credenciais do Supabase não encontradas no .env")
                return []

            supabase: Client = create_client(url, key)
            query = supabase.table("medidores").select("id_qrcode, unidade_id, tipo")
            
            if filtro_tipo != "AMBOS":
                query = query.eq("tipo", filtro_tipo.upper())
            
            response = query.order("unidade_id", desc=True).execute()
            return response.data
        except Exception as e:
            print(f"❌ Erro ao buscar no Supabase: {e}")
            return []

    @staticmethod
    def get_unidades(filtro_tipo="AMBOS"):
        """Apelido para get_medidores para manter compatibilidade com gerador_qr.py."""
        return Database.get_medidores(filtro_tipo)