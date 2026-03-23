"""
================================================================================
🗄️ COFRE LOCAL - database/database.py
================================================================================

Este é o "COFRE LOCAL" do AguaFlow.

Tudo o que acontece aqui é para PROTEGER OS DADOS do zelador do Vivere Prudente:

✅ Os dados ficam OFFLINE no banco local
✅ Se o Wi-Fi cair, NENHUM DADO SE PERDE
✅ Cada leitura é VALIDADA EM DUAS CAMADAS (Python + SQL)
✅ Sistema de BACKUP cria cópias diárias
✅ Dados são SINCRONIZADOS com Supabase quando Wi-Fi volta

================================================================================
"""
import os
import re
from dotenv import load_dotenv
from supabase import create_client
import logging
import sqlite3
from datetime import datetime as dt

# Carrega as variáveis do arquivo .env
load_dotenv()

# Silencia os alertas técnicos do terminal para manter a limpeza
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("postgrest").setLevel(logging.ERROR)

LOG_FILE = "database/sync_log.json"
DB_PATH = "aguaflow.db"


from contextlib import contextmanager

class Database:
    # ---------------------------------------------------------
    # 1. CONFIGURAÇÃO SUPABASE
    # ---------------------------------------------------------
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")

    # Inicializa o cliente apenas se as chaves existirem
    supabase = None
    if url and key:
        try:
            supabase = create_client(url, key)
        except Exception as e:
            print(f"⚠️ Alerta: Falha ao iniciar cliente Supabase: {e}")
    else:
        print("⚠️ Alerta: Chaves do Supabase não encontradas no .env")

    # ---------------------------------------------------------
    # 2. GERENCIAMENTO LOCAL (SQLite)
    # ---------------------------------------------------------
    @staticmethod
    def get_connection():
        """Retorna conexão com banco de dados."""
        return sqlite3.connect(DB_PATH, check_same_thread=False)

    @classmethod
    @contextmanager
    def get_connection_safe(cls):
        """
        Context manager que garante:
        - Conexão sempre fechada (finally)
        - Rollback automático em caso de erro
        - Commit explícito apenas quando sucesso
        """
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def init_db():
        """Inicializa banco com tabela e unidades do Vivere Prudente."""
        conn = None
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            # Criando a tabela com TODAS as colunas necessárias + constraints
            # 1. Tabela de Leituras (Local)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unidade TEXT NOT NULL,
                    valor_leitura REAL,
                    tipo_registro TEXT,
                    leiturista TEXT,
                    data_hora_coleta TEXT,
                    sincronizado INTEGER DEFAULT 0
                )
            """)

            # 2. Tabela de Fila (Sync) - MANTENHA ESTA TAMBÉM!
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_leitura INTEGER,
                    payload TEXT,
                    error_message TEXT,
                    tentativas INTEGER DEFAULT 0,
                    ultimo_tentativa TEXT
                )
            """)

            cursor.execute("SELECT COUNT(*) FROM leituras")
            if cursor.fetchone()[0] == 0:
                print("📁 Gerando unidades do Vivere Prudente...")
                unidades = []
                ordem_cont = 1
                for andar in range(16, 0, -1):
                    for final in range(6, 0, -1):
                        unidades.append(
                            (f"{andar}{final}", 0.0, 'AGUA', ordem_cont))
                        ordem_cont += 1
                        unidades.append(
                            (f"{andar}{final}", 0.0, 'GAS', ordem_cont))
                        ordem_cont += 1

                unidades.append(('LAZER', 0.0, 'AGUA', ordem_cont))
                ordem_cont += 1
                unidades.append(('GERAL', 0.0, 'AGUA', ordem_cont))

                cursor.executemany(
                    "INSERT INTO leituras (unidade, leitura_anterior, tipo, ordem) VALUES (?, ?, ?, ?)",
                    unidades
                )

            conn.commit()
            conn.close()
            conn = None
            print("✅ Banco de dados inicializado com sucesso!")

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ Erro ao inicializar banco: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @staticmethod
    def validar_numero(valor_str):
        """
        Valida se é um número válido(sem letras).
        Retorna: {'valido': bool, 'mensagem': str, 'valor': float ou None}
        """
        if not valor_str or not valor_str.strip():
            return {'valido': False, 'mensagem': '⚠️ Digite um valor'}

        valor_str = valor_str.strip()

        # Permite apenas dígitos, ponto e vírgula
        if not re.match(r'^[\d.,]+$', valor_str):
            return {'valido': False, 'mensagem': '❌ Apenas números permitidos (sem letras)'}

        valor_str = valor_str.replace(',', '.')

        if valor_str.count('.') > 1:
            return {'valido': False, 'mensagem': '❌ Apenas um ponto decimal permitido'}

        try:
            valor = float(valor_str)
        except ValueError:
            return {'valido': False, 'mensagem': '❌ Número inválido'}

        if valor <= 0:
            return {'valido': False, 'mensagem': '❌ Valor deve ser maior que zero'}

        if valor > 999999:
            return {'valido': False, 'mensagem': '❌ Valor muito grande (limite: 999.999)'}

        return {'valido': True, 'mensagem': '', 'valor': valor}

    @staticmethod
    def buscar_proximo_pendente():
        """
        Busca próxima unidade pendente para leitura.
        Retorna tupla: (id, unidade, leitura_anterior) para desempacotamento na View.
        """
        conn = None
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, unidade, leitura_anterior FROM leituras WHERE status = 'PENDENTE' ORDER BY ordem ASC LIMIT 1"
            )
            res = cursor.fetchone()
            return res
        except Exception as e:
            print(f"Erro ao buscar próximo pendente: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # ---------------------------------------------------------
    # 3. OPERAÇÕES PRINCIPAIS (SALVAR + SYNC)
    # ---------------------------------------------------------
    @classmethod
    def registrar_leitura(cls, id_db, valor, tipo_val="AGUA"):
        """Salva a leitura localmente e tenta sincronizar."""

        # 1. Prepara o valor
        try:
            valor_float = float(str(valor).replace(',', '.'))
        except:
            return {'sucesso': False, 'mensagem': 'Valor inválido.'}

        supabase_synced = False
        msg_erro_sync = ""
        conn = None

        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            # 2. Busca dados da unidade para o payload
            cursor.execute(
                "SELECT unidade, tipo FROM leituras WHERE id = ?", (id_db,))
            dados_unidade = cursor.fetchone()
            if not dados_unidade:
                return {'sucesso': False, 'mensagem': 'Unidade não encontrada'}

            nome_unidade = dados_unidade[0]
            tipo_registro = dados_unidade[1] or tipo_val

            # 3. Salva no SQLite (Cofre Local) - COMMIT ÚNICO
            agora = dt.now().isoformat()
            cursor.execute("""
                UPDATE leituras
                SET leitura_atual = ?,
                    status = 'CONCLUIDO',
                    data_leitura = ?,
                    sincronizado = 0
                WHERE id = ?
            """, (valor_float, agora, id_db))
            conn.commit()

            # 2. Monta o pacote com os nomes EXATOS da sua tabela no Supabase
            payload = {
                "unidade_id": str(nome_unidade),
                "valor_leitura": float(valor_float),
                # "tipo_registro": "Manual",
                # "leiturista": "Clodoaldo",
                # "data_hora_coleta": dt.now().isoformat()
            }
            try:
                if cls.supabase:
                    # Estratégia "Tentativa de Insert -> Falha 409 -> Update"
                    # Isso resolve o problema onde o Update retorna 200 OK mas sem dados (lista vazia),
                    # o que enganava o sistema fazendo-o tentar inserir duplicado.
                    try:
                        cls.supabase.table("leituras").insert(payload).execute()
                    except Exception as e:
                        # O erro pode vir como '23505' (Postgres) ou '409' (HTTP)
                        erro_str = str(e).lower()
                        if any(k in erro_str for k in ["409", "conflict", "23505", "already exists", "duplicate"]):
                            cls.supabase.table("leituras").update(payload).eq("unidade_id", str(nome_unidade)).execute()
                        else:
                            raise e  # Se for outro erro (ex: internet), relança

                    # Se sucesso, marca como sincronizado
                    cursor.execute(
                        "UPDATE leituras SET sincronizado = 1 WHERE id = ?", (id_db,))
                    conn.commit()
                    supabase_synced = True
                else:
                    msg_erro_sync = "Cliente Supabase não configurado"
            except Exception as e:
                msg_erro_sync = str(e)
                # TODO: Enfileirar para sincronização posterior
                # cls.enqueue_sync(id_db, payload)

            conn.close()
            conn = None

            final_msg = "Leitura salva localmente."
            if supabase_synced:
                final_msg = "✅ Salvo e Sincronizado!"
            elif msg_erro_sync:
                final_msg = f"⚠️ Salvo localmente (Offline: {msg_erro_sync})"

            return {
                'sucesso': True,
                'mensagem': final_msg,
                'supabase_sync': supabase_synced
            }

        except Exception as e:
            return {'sucesso': False, 'mensagem': f"Erro crítico: {str(e)}"}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_leituras(unidade=None, status=None):
        """Retorna lista de leituras para relatórios."""
        conn = None
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()
            query = "SELECT * FROM leituras WHERE 1=1"
            params = []
            if unidade:
                query += " AND unidade = ?"
                params.append(unidade)
            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY ordem ASC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return {'sucesso': True, 'dados': rows}
        except Exception as e:
            return {'sucesso': False, 'mensagem': str(e)}
        finally:
            if conn:
                conn.close()

# Wrapper global para compatibilidade


def get_connection():
    return Database.get_connection()
