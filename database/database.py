import os
import sqlite3
from contextlib import contextmanager
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

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
        Inicializa o banco local SQLite.
        Garante a existência das colunas leitura_atual e sincronizado.
        """
        with cls.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unidade TEXT NOT NULL,
                    leitura_atual REAL NOT NULL,
                    leitura_anterior REAL,
                    consumo REAL,
                    tipo_leitura TEXT,
                    data_leitura TEXT,
                    sincronizado INTEGER DEFAULT 0
                )
            """)
            
            # Verificação de migração: garante que leitura_atual existe
            try:
                cursor.execute("SELECT leitura_atual FROM leituras LIMIT 1")
            except sqlite3.OperationalError:
                cursor.execute("DROP TABLE leituras") 
                Database.init_db()
                
            conn.commit()
            print("[DATABASE] ✅ Banco local inicializado com leitura_atual e sincronizado.")

    @staticmethod
    def registrar_leitura(unidade, valor, tipo_leitura="Manual"):
        """Registra a leitura localmente e calcula o consumo."""
        try:
            leitura_anterior = 0
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT leitura_atual FROM leituras WHERE unidade = ? ORDER BY data_leitura DESC LIMIT 1",
                    (unidade,)
                )
                row = cursor.fetchone()
                if row:
                    leitura_anterior = row['leitura_atual']

            consumo = valor - leitura_anterior
            
            with Database.get_db() as conn:
                conn.execute("""
                    INSERT INTO leituras (unidade, leitura_atual, leitura_anterior, consumo, tipo_leitura, data_leitura, sincronizado)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (unidade, valor, leitura_anterior, consumo, tipo_leitura, datetime.now().isoformat()))
                conn.commit()
            return True
        except Exception as e:
            print(f"❌ Erro ao registrar: {e}")
            return False

    @staticmethod
    def get_medidores(filtro_tipo="AMBOS"):
        """Busca medidores no Supabase."""
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
            print(f"❌ Erro Supabase: {e}")
            return []

    @staticmethod
    def buscar_relatorio_geral():
        """Busca dados na nuvem para a tela de relatórios."""
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            supabase: Client = create_client(url, key)
            response = supabase.table("leituras").select("*, medidores(unidade_id, tipo)").order("data_hora_coleta", desc=True).limit(50).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Erro ao buscar relatório: {e}")
            return []

    @staticmethod
    def get_unidades(filtro_tipo="AMBOS"):
        return Database.get_medidores(filtro_tipo)

    @staticmethod
    def _gerar_lista_unidades():
        """AJUSTADO: Formata a lista evitando redundâncias como 'GAS - GAS' no nome."""
        dados = Database.get_medidores()
        lista_formatada = []
        
        for i in dados:
            unidade_original = i['unidade_id'].upper()
            tipo_original = i['tipo'].upper()
            
            # Remove o sufixo técnico do nome para não repetir na tela
            nome_limpo = unidade_original.replace(f"-{tipo_original}", "").replace(tipo_original, "").strip("- ")
            
            tipo_rotulo = "Água" if "AGUA" in tipo_original else "Gás"
            
            lista_formatada.append({
                "id": i['id_qrcode'],
                "unidade": f"{nome_limpo} - {tipo_rotulo}",
                "tipo": tipo_rotulo
            })
            
        return lista_formatada