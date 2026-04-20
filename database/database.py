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
        # Mantém o timeout de 30s para evitar erros de banco travado
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row 
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    async def init_db(cls):
        """Inicializa as tabelas da Versão 1.0.2 com suporte a Água e Gás."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                # Tabela de Leituras - Garantindo a coluna 'tipo'
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
                print("✅ Banco de dados SQLite v1.0.2 inicializado.")
                return True
        except Exception as e:
            print(f"❌ Erro crítico na inicialização: {e}")
            return False

    @classmethod
    def salvar_leitura_local(cls, unidade, agua, gas, tipo):
        """Grava a medição respeitando a regra Duplex (v1.0.2)."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                
                # Regra Duplex: Unifica 163/164 e 23/24
                mapeamento = {
                    "163": "163/164", "164": "163/164",
                    "23": "23/24", "24": "23/24"
                }
                unidade_final = mapeamento.get(unidade, unidade)

                # INSERT unificado com 5 parâmetros (unidade, agua, gas, tipo, data)
                cursor.execute("""
                    INSERT INTO leituras (unidade, leitura_agua, leitura_gas, tipo, data_hora_coleta)
                    VALUES (?, ?, ?, ?, ?)
                """, (unidade_final, agua, gas, tipo, datetime.now().isoformat()))
                
                conn.commit()
                print(f"💾 Unidade {unidade_final} ({tipo}) salva localmente.")
                return True
        except Exception as e:
            print(f"❌ Falha ao gravar no SQLite: {e}")
            return False

    @classmethod
    def buscar_ultima_unidade_lida(cls):
        """Recupera a última unidade para sequência inteligente."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT unidade FROM leituras ORDER BY id DESC LIMIT 1")
                res = cursor.fetchone()
                return res["unidade"] if res else None
        except Exception as e:
            print(f"Erro ao buscar última unidade: {e}")
            return None

    @classmethod
    def get_medidores(cls, filtro_tipo="AMBOS"):
        """Retorna lista de medidores lidos ou a lista mestre padrão."""
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
    def _gerar_lista_unidades(cls):
        """Gera a lista de unidades do condomínio em ordem decrescente."""
        lista = []
        # Invertemos o range para começar do 16 e ir até o 1
        for andar in range(16, 0, -1): 
            # Invertemos o apto para começar do 6 e ir até o 1
            for apto in range(6, 0, -1):
                u = f"{andar}{apto}"
                # Regras Duplex do Vivere
                if u in ["163", "164"]: u = "163/164"
                if u in ["23", "24"]: u = "23/24"
                if u not in lista: 
                    lista.append(u)
        return lista

    # --- Métodos de Sincronização (Preservando sua lógica de 184 linhas) ---
    
    @classmethod
    def get_leituras_pendentes(cls):
        """Busca leituras que ainda não foram enviadas para o Supabase."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM leituras WHERE sincronizado = 0")
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []

    @classmethod
    def marcar_como_sincronizado(cls, leitura_id):
        """Atualiza o status após sucesso no Supabase."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE leituras SET sincronizado = 1 WHERE id = ?", (leitura_id,))
                conn.commit()
                return True
        except:
            return False