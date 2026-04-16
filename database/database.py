import os
import sqlite3
from contextlib import contextmanager
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
        """Inicializa as tabelas locais (exigido pelo main.py)."""
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
            print("[DATABASE] ✅ Banco local inicializado.")

    @staticmethod
    def get_medidores(filtro_tipo="AMBOS"):
        """Busca medidores no Supabase traduzindo os filtros da interface."""
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key: return []
            
            supabase: Client = create_client(url, key)
            query = supabase.table("medidores").select("id_qrcode, unidade_id, tipo")
            
            tipo_map = {"Água": "AGUA", "Gás": "GAS", "AGUA": "AGUA", "GAS": "GAS"}
            tipo_busca = tipo_map.get(filtro_tipo, filtro_tipo).upper()

            if tipo_busca != "AMBOS":
                query = query.eq("tipo", tipo_busca)
            
            response = query.order("unidade_id", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Erro Supabase em get_medidores: {e}")
            return []

    @staticmethod
    def _gerar_lista_unidades():
        """Formata dados para a tela de medição."""
        dados = Database.get_medidores()
        return [{"id": i['id_qrcode'], "unidade": i['unidade_id'], 
                 "tipo": "Água" if "AGUA" in i['tipo'] else "Gás"} for i in dados]

    @staticmethod
    def buscar_relatorio_geral():
        """Busca as últimas 50 leituras na nuvem."""
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            supabase: Client = create_client(url, key)
            
            response = supabase.table("leituras").select(
                "*, medidores(unidade_id, tipo)"
            ).order("data_hora_coleta", desc=True).limit(50).execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Erro ao buscar relatório: {e}")
            return []

    @staticmethod
    def buscar_historico_unidade(unidade_id, meses=6):
        """
        NOVO: Busca o histórico de uma unidade específica para cálculo de média.
        Exemplo: buscar_historico_unidade('166-AGUA', 6)
        """
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            supabase: Client = create_client(url, key)
            
            # Calcula a data de corte (hoje - 6 meses)
            data_corte = (datetime.now() - timedelta(days=meses*30)).isoformat()
            
            response = supabase.table("leituras")\
                .select("valor_leitura, data_hora_coleta")\
                .eq("unidade_id", unidade_id)\
                .gte("data_hora_coleta", data_corte)\
                .order("data_hora_coleta", desc=False)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Erro ao buscar histórico: {e}")
            return []

    @staticmethod
    def get_unidades(filtro_tipo="AMBOS"):
        return Database.get_medidores(filtro_tipo)