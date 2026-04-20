import time
import asyncio
import logging
from datetime import datetime as dt
from pathlib import Path
from .database import Database

# Configuração de log dedicado para sincronização
LOG_DIR = Path(__file__).parent.parent / "storage" / "logs_sync"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "sync_errors.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SyncService:

    @classmethod
    async def init_sync_log_table(cls):
        """
        Inicializa a tabela de log de sincronização para rastrear falhas.
        Deve ser chamado durante a inicialização do aplicativo.
        """
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        leitura_id INTEGER NOT NULL,
                        unidade TEXT NOT NULL,
                        status TEXT NOT NULL,
                        erro_mensagem TEXT,
                        tentativas INTEGER DEFAULT 1,
                        ultima_tentativa TEXT,
                        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Garante índice para consultas rápidas
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sync_log_unidade
                    ON sync_log(unidade)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sync_log_status
                    ON sync_log(status)
                """)
                conn.commit()
                print("✅ Tabela sync_log inicializada para rastreamento de erros.")
        except Exception as e:
            logger.error(f"❌ Falha ao criar tabela sync_log: {e}")

    @classmethod
    async def processar_fila(cls):
        """
        Varre o SQLite local em busca de leituras não sincronizadas
        e tenta enviá-las para o Supabase (Nuvem).

        GARANTIAS ATÔMICAS:
        - Se upload falhar: sincronizado permanece 0 (não há commit parcial)
        - Se upload succeeded: marca sincronizado = 1 E registra log de sucesso
        - Erros são registrados em sync_log para diagnóstico
        """
        logger.info("🔄 AguaFlow: Iniciando ciclo de sincronização...")
        print("🔄 AguaFlow: Iniciando ciclo de sincronização...")

        total_enviados = 0
        total_sucessos = 0
        total_falhas = 0

        # 1. Busca no Banco Local apenas o que ainda não subiu para a nuvem (sincronizado = 0)
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, unidade, leitura_agua, leitura_gas, tipo, data_leitura
                FROM leituras
                WHERE sincronizado = 0
                ORDER BY id ASC
            """)
            pendentes = cursor.fetchall()

            if not pendentes:
                logger.info("✅ Tudo em dia: Nada para sincronizar.")
                print("✅ Tudo em dia: Nada para sincronizar.")
                return {"total": 0, "sucessos": 0, "falhas": 0}

            total_enviados = len(pendentes)
            logger.info(f"📦 {total_enviados} leituras pendentes encontradas para sincronização.")

            for item in pendentes:
                leitura_id = item['id']
                unidade = item['unidade']
                leitura_agua = item['leitura_agua']
                leitura_gas = item.get('leitura_gas', 0)
                data_leitura = item.get('data_leitura', '')

                logger.info(f"📡 Tentando enviar Unidade {unidade} (ID: {leitura_id}) para a nuvem...")
                print(f"📡 Enviando Unidade {unidade} para a nuvem...")

                # 2. Tenta enviar para o Supabase - TRANSAtOMICA
                # A transação só faz commit se o upload confirmar sucesso
                resultado = await cls._enviar_para_nuvem_transacao(
                    conn, cursor, item
                )

                if resultado['sucesso']:
                    # 3. UPLOAD CONFIRMOU: marca como sincronizado (COMMIT ATÔMICO)
                    cursor.execute(
                        "UPDATE leituras SET sincronizado = 1 WHERE id = ?",
                        (leitura_id,)
                    )
                    conn.commit()  # Commit SÓ após confirmação da nuvem

                    cls._registrar_log_sync(
                        cursor, conn, leitura_id, unidade,
                        "SUCESSO", None
                    )

                    total_sucessos += 1
                    logger.info(f"✔️ Unidade {unidade} sincronizada com sucesso!")
                    print(f"✔️ Unidade {unidade} sincronizada com sucesso!")
                else:
                    # 4. UPLOAD FALHOU: mantém sincronizado = 0 (ROLLBACK IMPLÍCITO)
                    # NÃO faz commit - o status permanece 0 para próxima tentativa
                    erro_msg = resultado.get('erro', 'Erro desconhecido')

                    # Registra falha no log de sincronização
                    cls._registrar_log_sync(
                        cursor, conn, leitura_id, unidade,
                        "FALHA", erro_msg
                    )

                    total_falhas += 1
                    logger.warning(
                        f"❌ FALHA na sincronização da Unidade {unidade} (ID: {leitura_id}): {erro_msg}"
                    )
                    print(f"❌ Falha ao sincronizar {unidade}. Tentará novamente depois.")
                    print(f"   → Erro: {erro_msg}")

            # Commit final apenas para garantir consistência dos logs
            # As atualizações de 'sincronizado' já foram commitadas individualmente
            conn.commit()

        resultado_final = {
            "total": total_enviados,
            "sucessos": total_sucessos,
            "falhas": total_falhas
        }

        logger.info(
            f"📊 Ciclo de sincronização concluído: "
            f"{total_sucessos} sucessos, {total_falhas} falhas de {total_enviados} total."
        )
        print(f"📊 Sincronização concluída: {total_sucessos}/{total_enviados} enviadas com sucesso.")

        return resultado_final

    @classmethod
    async def _enviar_para_nuvem_transacao(cls, conn, cursor, dados_leitura):
        """
        Envia leitura para Supabase com garantia atômica.

        RETORNA:
            dict com {'sucesso': bool, 'erro': str ou None}

        GARANTIA:
            - Se retornar {'sucesso': True}: dados estão no Supabase E no SQLite
            - Se retornar {'sucesso': False}: SQLite mantém sincronizado = 0
        """
        leitura_id = dados_leitura['id']
        unidade = dados_leitura['unidade']
        leitura_agua = dados_leitura['leitura_agua']
        leitura_gas = dados_leitura.get('leitura_gas', 0)
        data_leitura = dados_leitura.get('data_leitura', '')

        try:
            # Importa cliente Supabase
            from .supabase_client import get_supabase_client

            cliente = get_supabase_client()

            if not cliente:
                return {
                    'sucesso': False,
                    'erro': 'Sem conexão com Supabase (verifique credenciais/rede)'
                }

            # Prepara dados para UPSERT no Supabase
            dados_payload = {
                "id_unidade": unidade,
                "valor": leitura_agua,
                "valor_gas": leitura_gas,
                "tipo": "agua",
                "data_leitura": data_leitura,
                "sincronizado_em": dt.now().isoformat()
            }

            # Executa UPSERT no Supabase (pode lançar exceção de rede)
            response = cliente.table('medicoes').upsert(dados_payload).execute()

            # Verifica se o Supabase confirmou o recebimento
            if response and response.data:
                logger.debug(f"Supabase confirmou recebimento da unidade {unidade}")
                return {'sucesso': True, 'erro': None}
            else:
                return {
                    'sucesso': False,
                    'erro': 'Supabase não confirmou recebimento (response vazio)'
                }

        except Exception as e:
            erro_str = str(e)
            logger.error(f"Exceção ao enviar unidade {unidade} para Supabase: {erro_str}")
            return {'sucesso': False, 'erro': erro_str}

    @classmethod
    def _registrar_log_sync(cls, cursor, conn, leitura_id, unidade, status, erro_mensagem):
        """
        Registra entrada na tabela sync_log para auditoria e diagnóstico.

        Se já existir log para esta leitura e for FALHA, incrementa tentativas.
        """
        try:
            data_atual = dt.now().strftime("%Y-%m-%d %H:%M:%S")

            # Verifica se já existe log de falha para esta leitura
            cursor.execute(
                "SELECT id, tentativas FROM sync_log WHERE leitura_id = ? AND status = 'FALHA' ORDER BY id DESC LIMIT 1",
                (leitura_id,)
            )
            log_existente = cursor.fetchone()

            if status == "FALHA" and log_existente:
                # Incrementa tentativas de falha
                novas_tentativas = log_existente['tentativas'] + 1
                cursor.execute("""
                    UPDATE sync_log
                    SET tentativas = ?, ultima_tentativa = ?, erro_mensagem = ?
                    WHERE id = ?
                """, (novas_tentativas, data_atual, erro_mensagem, log_existente['id']))
            else:
                # Cria novo registro de log
                cursor.execute("""
                    INSERT INTO sync_log (leitura_id, unidade, status, erro_mensagem, ultima_tentativa)
                    VALUES (?, ?, ?, ?, ?)
                """, (leitura_id, unidade, status, erro_mensagem, data_atual))

            conn.commit()

        except Exception as e:
            logger.error(f"Falha ao registrar log de sincronização: {e}")

    @classmethod
    def adicionar_a_fila(cls, leitura_id):
        """
        Método de apoio para marcar manualmente uma leitura para re-envio se necessário.
        Útil para retry manual após correção de problemas de rede.
        """
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE leituras SET sincronizado = 0 WHERE id = ?", (leitura_id,)
            )
            conn.commit()
            logger.info(f"Leitura ID {leitura_id} marcada para re-sincronização manual.")

    @classmethod
    def get_relatorio_sync(cls, limite_dias=7):
        """
        Retorna relatório de sincronizações (sucessos e falhas) dos últimos N dias.
        Útil para diagnóstico de problemas recorrentes.
        """
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        unidade,
                        status,
                        COUNT(*) as quantidade,
                        MAX(ultima_tentativa) as ultima_ocorrencia,
                        GROUP_CONCAT(DISTINCT erro_mensagem) as erros
                    FROM sync_log
                    WHERE datetime(criado_em) >= datetime('now', ?)
                    GROUP BY unidade, status
                    ORDER BY quantidade DESC
                """, (f'-{limite_dias} days',))

                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de sync: {e}")
            return []

    @classmethod
    def limpar_logs_antigos(cls, dias_reter=30):
        """
        Remove logs de sincronização com mais de N dias para economizar espaço.
        Mantém histórico para diagnóstico recente.
        """
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM sync_log
                    WHERE datetime(criado_em) < datetime('now', ?)
                """, (f'-{dias_reter} days',))
                conn.commit()
                logger.info(f"Logs de sincronização com mais de {dias_reter} dias removidos.")
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Erro ao limpar logs antigos: {e}")
            return 0