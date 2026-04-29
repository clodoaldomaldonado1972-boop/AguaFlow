import os
import sqlite3
import logging
import csv
from contextlib import contextmanager
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AguaFlow_DB")

class Database:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")
    
    # --- INICIALIZAÇÃO DO SUPABASE ---
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    # Definimos explicitamente como None para evitar AttributeError em outros arquivos
    supabase: Client = None 

    if url and key:
        try:
            supabase = create_client(url, key)
            logger.info("✅ Conexão com Supabase estabelecida.")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao Supabase: {e}")

    @classmethod
    @contextmanager
    def get_db(cls):
        """Abre a conexão garantindo o fechamento seguro."""
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False, timeout=20)
        conn.row_factory = sqlite3.Row 
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def inicializar_tabelas(cls):
        """Cria a estrutura e realiza migrações de colunas necessárias."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                
                # 1. Cria a tabela base
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leituras (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        unidade TEXT NOT NULL,
                        tipo TEXT NOT NULL,
                        sincronizado INTEGER DEFAULT 0,
                        data_leitura_atual TEXT
                    )
                """)

                # 2. Migrações Individuais (Adiciona colunas se não existirem)
                # Garante compatibilidade com o SyncService
                novas_colunas = [
                    "ALTER TABLE leituras ADD COLUMN leitura_agua REAL",
                    "ALTER TABLE leituras ADD COLUMN leitura_gas REAL",
                    "ALTER TABLE leituras ADD COLUMN data_leitura_atual TEXT"
                ]

                for comando in novas_colunas:
                    try:
                        cursor.execute(comando)
                    except sqlite3.OperationalError:
                        pass # Coluna já existe

                conn.commit()
                logger.info("🚀 Estrutura do banco de dados verificada.")
        except Exception as e:
            logger.error(f"Erro ao inicializar banco: {e}")

    @classmethod
    def buscar_historico(cls, unidade):
        """Recupera as últimas leituras para o gráfico."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT data_leitura_atual, leitura_agua, leitura_gas 
                    FROM leituras 
                    WHERE unidade = ? 
                    ORDER BY data_leitura_atual DESC 
                    LIMIT 6
                """, (unidade,))
                return [dict(row) for row in cursor.fetchall()][::-1]
        except Exception as e:
            logger.error(f"Erro no histórico: {e}")
            return []

    @classmethod
    def _gerar_lista_unidades(cls):
        """Gera a lista exata do Edifício Vivere com Duplex e Áreas Comuns."""
        try:
            unidades = []
            
            # ÁREAS COMUNS (As strings devem ser EXATAS)
            unidades.append("TERREO GERAL ÁGUA")
            unidades.append("LAZER GÁS")

            # APARTAMENTOS (16 andares, final 1 a 6)
            for andar in range(16, 0, -1):
                for final in range(1, 7):
                    u_id = f"{andar}{final}"
                    
                    # Regra dos Duplex
                    if u_id in ["163", "164"]:
                        if "163/164" not in unidades: unidades.append("163/164")
                        continue
                    if u_id in ["23", "24"]:
                        if "23/24" not in unidades: unidades.append("23/24")
                        continue
                        
                    unidades.append(u_id)
            
            # Segurança: Se a lista estiver vazia por algum motivo, não retorna None
            return unidades if unidades else ["ERRO_LISTA_VAZIA"]

        except Exception as e:
            print(f"Erro na lógica de unidades: {e}")
            return ["ERRO_PROCESSAMENTO"]

    @classmethod
    def get_leituras_mes_atual(cls):
        """Retorna todas as leituras realizadas no mês corrente."""
        try:
            mes_atual = datetime.now().strftime('%Y-%m')
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM leituras 
                    WHERE data_leitura_atual LIKE ? 
                    ORDER BY data_leitura_atual DESC
                """, (f"{mes_atual}%",))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro ao buscar leituras do mês: {e}")
            return []    

    @classmethod
    def exportar_csv_mes(cls):
        dados = cls.get_leituras_mes_atual()
        caminho = os.path.join(cls.BASE_DIR, "..", "storage", "relatorios", "relatorio_mes.csv")
        
        with open(caminho, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=dados[0].keys())
            writer.writeheader()
            writer.writerows(dados)
        return caminho

    @classmethod
    def buscar_leituras_periodo(cls, data_inicio, data_fim, unidade=None):
        """
        Busca leituras no SQLite entre duas datas.
        Formato esperado: 'YYYY-MM-DD'
        """
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM leituras WHERE date(data_leitura_atual) BETWEEN ? AND ?"
                params = [data_inicio, data_fim]
                
                if unidade and unidade != "Geral":
                    query += " AND unidade = ?"
                    params.append(unidade)
                
                query += " ORDER BY data_leitura_atual DESC"
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro ao buscar período: {e}")
            return []    
# --- FUNÇÃO GLOBAL DE ACESSO ---
# --- FUNÇÃO GLOBAL DE ACESSO ---
def get_supabase_client():
    try:
        # Garante que as chaves do .env foram lidas
        if not hasattr(Database, 'supabase') or Database.supabase is None:
            Database.inicializar_tabelas() # Força a carga das variáveis e tabelas
        
        if Database.supabase is None:
            print("ERRO: Supabase não pôde ser inicializado. Verifique seu arquivo .env")
            return None
            
        return Database.supabase
    except Exception as e:
        print(f"Erro fatal ao conectar ao banco: {e}")
        return None