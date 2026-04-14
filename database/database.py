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
        """Gerencia a conexão SQLite de forma segura."""
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        """Inicializa as tabelas necessárias para o ÁguaFlow."""
        with cls.get_db() as conn:
            cursor = conn.cursor()
            # Tabela de leituras (histórico)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unidade TEXT NOT NULL,
                    leitura_agua REAL NOT NULL,
                    leitura_gas REAL,
                    data_leitura TEXT
                )
            """)
            # Tabela de unidades (referência)
            cursor.execute("CREATE TABLE IF NOT EXISTS unidades (id TEXT PRIMARY KEY)")
            conn.commit()

    @classmethod
    def get_unidades(cls):
        """Retorna a lista completa para o Gerador com a chave 'id' inclusa."""
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
        """Busca a última unidade lida incluindo o campo id."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, unidade FROM leituras ORDER BY id DESC LIMIT 1")
                res = cursor.fetchone()
                return dict(res) if res else None
        except Exception:
            return None

    @classmethod
    def buscar_todas_leituras(cls):
        """Alimenta o Dashboard."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, unidade, leitura_agua, leitura_gas, data_leitura FROM leituras ORDER BY id DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []

    @staticmethod
    def _gerar_lista_unidades():
        """
        Gera a lista para o Vivere Prudente:
        - Cada apto gera dois registros (Água e Gás) com IDs únicos.
        """
        lista = []
        condominio = "Vivere Prudente"
        
        # Unidades dos Apartamentos (96 aptos x 2 medidores cada = 192 QR Codes)
        for andar in range(16, 0, -1):
            for apto in range(1, 7):
                numero_unidade = f"{andar}{apto}"
                
                # Item Água: O ID é essencial para o Gerador não travar
                lista.append({
                    "id": f"{numero_unidade}_agua",
                    "unidade": numero_unidade,
                    "tipo": "Água",
                    "condominio": condominio
                })
                
                # Item Gás
                lista.append({
                    "id": f"{numero_unidade}_gas",
                    "unidade": numero_unidade,
                    "tipo": "Gás",
                    "condominio": condominio
                })
        
        # Unidades Especiais com seus IDs únicos
        lista.append({
            "id": "GERAL_AGUA",
            "unidade": "GERAL",
            "tipo": "Água",
            "condominio": condominio
        })
        lista.append({
            "id": "LAZER_GAS",
            "unidade": "LAZER",
            "tipo": "Gás",
            "condominio": condominio
        })
        
        return lista