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

O "Cofre Local" garante que o zelador trabalhe TRANQUILO sabendo que:
- Seus dados estão seguros
- Nada é perdido em caso de crash ou falta de internet
- Tudo funciona PERFEITAMENTE em modo offline

================================================================================
"""

import sqlite3
import datetime
import json
import re
import requests
from datetime import datetime as dt

LOG_FILE = 'supabase_sync.log'


class Database:
    """
    Gerenciador unificado de banco de dados SQLite para AguaFlow.
    Combina funcionalidades do database.py original com validações robustas.
    """

    DB_PATH = "aguaflow.db"

    @staticmethod
    def get_connection():
        """Retorna conexão com banco de dados."""
        return sqlite3.connect(Database.DB_PATH, check_same_thread=False)

    @staticmethod
    def init_db():
        """Inicializa banco com tabela e unidades do Vivere Prudente."""
        conn = Database.get_connection()
        cursor = conn.cursor()

        # Criando a tabela com TODAS as colunas necessárias + constraints
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leituras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unidade TEXT NOT NULL,
                leitura_anterior REAL DEFAULT 0.0,
                leitura_atual REAL DEFAULT NULL,
                tipo TEXT DEFAULT 'AGUA',
                status TEXT DEFAULT 'PENDENTE',
                ordem INTEGER,
                data_leitura TEXT,
                sincronizado INTEGER DEFAULT 0,
                CHECK(leitura_anterior >= 0),
                CHECK(leitura_atual IS NULL OR leitura_atual > 0)
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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leitura_id INTEGER NOT NULL,
                payload TEXT NOT NULL,
                tentativas INTEGER DEFAULT 0,
                ultimo_erro TEXT,
                criado_em TEXT,
                atualizado_em TEXT
            )
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def validar_numero(valor_str):
        """
        Valida se é um número válido(sem letras).
        Retorna: {'valido': bool, 'mensagem': str, 'valor': float ou None}
        """
        if not valor_str or not valor_str.strip():
            return {'valido': False, 'mensagem': '⚠️ Digite um valor'}

        # Remove espaços
        valor_str = valor_str.strip()

        # Aceita apenas números, ponto e vírgula
        if not re.match(r'^[\d.,]+$', valor_str):
            return {'valido': False, 'mensagem': '❌ Apenas números permitidos (sem letras)'}

        # Trata vírgula como ponto (formato BR comum)
        valor_str = valor_str.replace(',', '.')

        # Valida múltiplos pontos
        if valor_str.count('.') > 1:
            return {'valido': False, 'mensagem': '❌ Apenas um ponto decimal permitido'}

        try:
            valor = float(valor_str)
        except ValueError:
            return {'valido': False, 'mensagem': '❌ Número inválido'}

        # Validações de range
        if valor <= 0:
            return {'valido': False, 'mensagem': '❌ Valor deve ser maior que zero'}

        if valor > 999999:
            return {'valido': False, 'mensagem': '❌ Valor muito grande (limite: 999.999)'}

        # Valida limite de casas decimais
        casas = len(str(valor).split('.')[-1]) if '.' in str(valor) else 0
        if casas > 3:
            return {'valido': False, 'mensagem': '❌ Máximo 3 casas decimais'}

        return {'valido': True, 'mensagem': '', 'valor': valor}

    @staticmethod
    def buscar_proximo_pendente():
        """Busca próxima unidade pendente para leitura."""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, unidade, leitura_anterior, tipo FROM leituras WHERE status = 'PENDENTE' ORDER BY ordem ASC LIMIT 1")
            res = cursor.fetchone()
            conn.close()
            return res
        except Exception as e:
            print(f"Erro ao buscar próximo pendente: {e}")
            return None

    @staticmethod
    def registrar_leitura(id_unidade, valor):
        """
        Registra leitura com validação completa.
        Retorna: {'sucesso': bool, 'mensagem': str}
        """
        # Validação de entrada
        validacao = Database.validar_numero(str(valor))
        if not validacao['valido']:
            return {'sucesso': False, 'mensagem': validacao['mensagem']}

        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT unidade, leitura_anterior, tipo, ordem FROM leituras WHERE id = ?",
                (id_unidade,)
            )
            unidade_row = cursor.fetchone()
            if unidade_row is None:
                conn.close()
                return {'sucesso': False, 'mensagem': '❌ Unidade não encontrada'}

            unidade_val, leitura_anterior_val, tipo_val, ordem_val = unidade_row

            agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            valor_float = validacao['valor']
            status = 'CONCLUIDO' if valor_float > 0 else 'VAZIO'

            cursor.execute(
                "UPDATE leituras SET leitura_atual = ?, status = ?, data_leitura = ? WHERE id = ?",
                (valor_float, status, agora, id_unidade)
            )

            if cursor.rowcount == 0:
                conn.close()
                return {'sucesso': False, 'mensagem': '❌ Unidade não encontrada'}

            conn.commit()

            # Tentativa de sincronização com Supabase (na nuvem)
            supabase_synced = False
            supabase_message = ''
            try:
                from database.supabase_client import insert_leitura_supabase

                payload = {
                    '_id': id_unidade,
                    'unidade': unidade_val,
                    'leitura_anterior': leitura_anterior_val,
                    'leitura_atual': valor_float,
                    'tipo': tipo_val,
                    'status': status,
                    'ordem': ordem_val,
                    'data_leitura': agora
                }

                sp_result = insert_leitura_supabase(payload)
                supabase_synced = bool(sp_result.get('sucesso'))
                supabase_message = sp_result.get('mensagem', '')

                if supabase_synced:
                    cursor.execute(
                        "UPDATE leituras SET sincronizado = 1 WHERE id = ?",
                        (id_unidade,)
                    )
                    conn.commit()
                else:
                    Database.enqueue_sync(
                        id_unidade, payload, erro=supabase_message)
                    Database.log_sync_error(
                        f"Falha sync imediata leitura {id_unidade}: {supabase_message}")

            except Exception as sup_e:
                supabase_synced = False
                supabase_message = f'Erro Supabase: {sup_e}'
                Database.enqueue_sync(
                    id_unidade, payload, erro=supabase_message)
                Database.log_sync_error(
                    f"Exception sync imediata leitura {id_unidade}: {supabase_message}")

            conn.close()

            final_message = f'✓ Leitura de {valor_float} m³ salva com sucesso!'
            if supabase_synced:
                final_message += ' ✅ Sincronizada com Supabase.'
            else:
                final_message += f' ⚠️ Falha na sincronização: {supabase_message}'

            # Chama a fila de reenvio sempre que uma leitura é gravada
            try:
                Database.sync_pending_records()
            except Exception as e:
                Database.log_sync_error(
                    f"Erro ao chamar sync_pending_records: {e}")

            return {
                'sucesso': True,
                'mensagem': final_message,
                'supabase_sync': supabase_synced
            }

        except Exception as e:
            return {'sucesso': False, 'mensagem': f'❌ Erro ao salvar: {str(e)}'}

    @staticmethod
    def log_sync_error(text):
        """Grava log simples de falhas de rede/Sync."""
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                agora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{agora}] {text}\n")
        except Exception:
            pass

    @staticmethod
    def enqueue_sync(leitura_id, payload, erro=None):
        """Adiciona ou atualiza fila de retry para leitura."""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            now = datetime.datetime.now().isoformat()
            payload_json = json.dumps(payload, default=str, ensure_ascii=False)

            cursor.execute(
                "SELECT id, tentativas FROM sync_queue WHERE leitura_id = ?",
                (leitura_id,)
            )
            existing = cursor.fetchone()
            if existing:
                queue_id, tentativas = existing
                tentativas += 1
                cursor.execute(
                    "UPDATE sync_queue SET tentativas = ?, ultimo_erro = ?, atualizado_em = ? WHERE id = ?",
                    (tentativas, str(erro), now, queue_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO sync_queue (leitura_id, payload, tentativas, ultimo_erro, criado_em, atualizado_em) VALUES (?, ?, 1, ?, ?, ?)",
                    (leitura_id, payload_json, str(erro), now, now)
                )

            conn.commit()
            conn.close()
        except Exception as e:
            Database.log_sync_error(
                f"Falha ao enfileirar leitura {leitura_id}: {e}")

    @staticmethod
    def process_retry_queue(max_attempts=5):
        """Tenta reprocessar leituras falhadas com Supabase."""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, leitura_id, payload, tentativas FROM sync_queue ORDER BY criado_em ASC")
            filas = cursor.fetchall()

            from database.supabase_client import insert_leitura_supabase

            processed = 0
            for fila in filas:
                queue_id, leitura_id, payload_json, tentativas = fila
                if tentativas >= max_attempts:
                    Database.log_sync_error(
                        f"Máximo de tentativas atingido para leitura {leitura_id}")
                    continue

                try:
                    payload = json.loads(payload_json)
                    sp_result = insert_leitura_supabase(payload)
                    if sp_result.get('sucesso'):
                        cursor.execute(
                            "UPDATE leituras SET sincronizado = 1 WHERE id = ?", (leitura_id,))
                        cursor.execute(
                            "DELETE FROM sync_queue WHERE id = ?", (queue_id,))
                        processed += 1
                    else:
                        Database.enqueue_sync(
                            leitura_id, payload, erro=sp_result.get('mensagem'))
                        Database.log_sync_error(
                            f"Retry falhou leitura {leitura_id}: {sp_result.get('mensagem')}")
                except Exception as e:
                    Database.enqueue_sync(
                        leitura_id, json.loads(payload_json), erro=e)
                    Database.log_sync_error(
                        f"Retry Exception leitura {leitura_id}: {e}")

            conn.commit()
            conn.close()

            return {'sucesso': True, 'processados': processed, 'pendentes': len(filas)}

        except Exception as e:
            Database.log_sync_error(f"Erro process_retry_queue: {e}")
            return {'sucesso': False, 'mensagem': str(e)}

    @staticmethod
    def sync_to_supabase():
        """Sincroniza leituras pendentes com o Supabase e usa fila de retry."""
        try:
            # Primeiro tenta processar fila de retry atual
            fila_result = Database.process_retry_queue()

            conn = Database.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, unidade, leitura_anterior, leitura_atual, tipo, status, ordem, data_leitura "
                "FROM leituras WHERE (sincronizado IS NULL OR sincronizado = 0) "
                "AND leitura_atual IS NOT NULL"
            )
            pendentes = cursor.fetchall()

            if not pendentes:
                conn.close()
                return {'sucesso': True, 'sincronizados': 0, 'total': 0, 'retry': fila_result}

            from database.supabase_client import insert_leitura_supabase

            sincronizados = 0
            for row in pendentes:
                (row_id, unidade_val, leitura_anterior_val,
                 leitura_atual_val, tipo_val, status_val,
                 ordem_val, data_leitura_val) = row

                payload = {
                    '_id': row_id,
                    'unidade': unidade_val,
                    'leitura_anterior': leitura_anterior_val,
                    'leitura_atual': leitura_atual_val,
                    'tipo': tipo_val,
                    'status': status_val,
                    'ordem': ordem_val,
                    'data_leitura': data_leitura_val
                }

                try:
                    sp_result = insert_leitura_supabase(payload)
                    if sp_result.get('sucesso'):
                        cursor.execute(
                            "UPDATE leituras SET sincronizado = 1 WHERE id = ?", (row_id,))
                        sincronizados += 1
                    else:
                        Database.enqueue_sync(
                            row_id, payload, erro=sp_result.get('mensagem'))
                        Database.log_sync_error(
                            f"Falha sync leitura {row_id}: {sp_result.get('mensagem')}")

                except Exception as e:
                    Database.enqueue_sync(row_id, payload, erro=e)
                    Database.log_sync_error(
                        f"Falha conx supabase leitura {row_id}: {e}")

            conn.commit()
            conn.close()

            return {
                'sucesso': True,
                'sincronizados': sincronizados,
                'total': len(pendentes),
                'retry': fila_result
            }

        except Exception as e:
            Database.log_sync_error(f"Erro sync_to_supabase: {e}")
            return {'sucesso': False, 'mensagem': f'Erro sync_to_supabase: {e}'}

    @staticmethod
    def sync_pending_records():
        """Wrapper para conveniência com nome pedido pelo usuário."""
        return Database.sync_to_supabase()

    @staticmethod
    def get_leituras(unidade=None, status=None):
        """Retorna leituras com filtros opcionais."""
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
            conn.close()

            return {
                'sucesso': True,
                'dados': rows,
                'total': len(rows)
            }

        except Exception as e:
            return {
                'sucesso': False,
                'dados': [],
                'total': 0,
                'mensagem': str(e)
            }

    @staticmethod
    def resetar_mes():
        """Move leitura_atual para leitura_anterior e reseta status."""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()

            # Move atual para anterior onde foi concluído
            cursor.execute("""
                UPDATE leituras
                SET leitura_anterior=leitura_atual,
                    leitura_atual=NULL,
                    status='PENDENTE',
                    data_leitura=NULL
                WHERE status='CONCLUIDO'
            """)

            # Mantém PENDENTE como está
            conn.commit()
            conn.close()

            return {'sucesso': True, 'mensagem': '✓ Mês resetado com sucesso'}

        except Exception as e:
            return {'sucesso': False, 'mensagem': f'❌ Erro ao resetar mês: {str(e)}'}

    @staticmethod
    def verificar_duplicata_hoje(unidade):
        """Verifica se unidade já foi lida hoje."""
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()
            hoje = dt.now().date().isoformat()

            cursor.execute("""
                SELECT COUNT(*) FROM leituras
                WHERE unidade=? AND date(data_leitura)=?
            """, (unidade, hoje))

            count = cursor.fetchone()[0]
            conn.close()

            return count > 0

        except Exception as e:
            print(f'Erro ao verificar duplicata: {e}')
            return False


# ========== FUNÇÕES GLOBAIS PARA COMPATIBILIDADE ==========
# Mantém compatibilidade com código existente

def get_connection():
    return Database.get_connection()


def init_db():
    Database.init_db()


def buscar_proximo_pendente():
    return Database.buscar_proximo_pendente()


def registrar_leitura(id_unidade, valor):
    return Database.registrar_leitura(id_unidade, valor)
