import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

class Database:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")
    
    @classmethod
    @contextmanager
    def get_db(cls):
        """Gerencia a conexão com o banco local com proteção contra travamentos."""
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        # Timeout de 30s e isolamento de thread para evitar 'database is locked'
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row 
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    async def init_db(cls):
        """Inicializa as tabelas e garante a estrutura para Água e Gás."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                # Tabela de Leituras - Versão 1.0.2 (Inclui coluna tipo)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leituras (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        unidade TEXT NOT NULL,
                        leitura_agua REAL NOT NULL,
                        leitura_gas REAL DEFAULT 0,
                        tipo TEXT,
                        data_hora_coleta TEXT,
                        sincronizado INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
                print("✅ Banco de dados SQLite pronto para gravação.")
                return True
        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {e}")
            return False

    @classmethod
    def salvar_leitura_local(cls, unidade, agua, gas, tipo):
        """Grava a medição respeitando a regra Duplex do Vivere."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                
                # Regra Duplex: Unifica 163/164 e 23/24
                mapeamento = {
                    "163": "163/164", "164": "163/164",
                    "23": "23/24", "24": "23/24"
                }
                unidade_final = mapeamento.get(unidade, unidade)

                # INSERT unificado com a coluna 'tipo'
                cursor.execute("""
                    INSERT INTO leituras (unidade, leitura_agua, leitura_gas, tipo, data_hora_coleta)
                    VALUES (?, ?, ?, ?, ?)
                """, (unidade_final, agua, gas, tipo, datetime.now().isoformat()))
                
                conn.commit()
                print(f"💾 Sucesso: Unidade {unidade_final} ({tipo}) gravada.")
                return True
        except Exception as e:
            print(f"❌ Falha ao gravar no SQLite: {e}")
            return False

    @classmethod
    def get_medidores(cls, filtro_tipo="AMBOS"):
        """Retorna lista de medidores lidos ou a lista mestre."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT unidade FROM leituras")
                rows = cursor.fetchall()
                unidades = [row["unidade"] for row in rows] if rows else cls._gerar_lista_unidades()
                
                medidores = []
                for u in unidades:
                    if filtro_tipo in ["Água", "AMBOS"]:
                        medidores.append({"unidade": u, "tipo": "Água"})
                    if filtro_tipo in ["Gás", "AMBOS"]:
                        medidores.append({"unidade": u, "tipo": "Gás"})
                return medidores
        except Exception as e:
            print(f"❌ Erro ao buscar medidores: {e}")
            return []

    @classmethod
    def buscar_ultima_unidade_lida(cls):
        """Auxilia na sequência inteligente da interface de medição."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT unidade FROM leituras ORDER BY id DESC LIMIT 1")
                res = cursor.fetchone()
                return res["unidade"] if res else None
        except:
            return None

    @classmethod
    def _gerar_lista_unidades(cls):
        """Gera a lista de unidades do condomínio (16 andares)."""
        lista = []
        for andar in range(1, 17):
            for apto in range(1, 7):
                u = f"{andar}{apto}"
                if u in ["163", "164"]: u = "163/164"
                if u in ["23", "24"]: u = "23/24"
                if u not in lista: lista.append(u)
        return lista