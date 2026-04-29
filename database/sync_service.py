import asyncio
import logging
from datetime import datetime as dt
from .database import Database

logger = logging.getLogger(__name__)

class SyncService:
    @classmethod
    async def init_sync_log_table(cls):
        """Inicializa a tabela de log de sincronização"""
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
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao iniciar tabela de logs: {e}")

    @classmethod
    async def processar_fila(cls):
        """
        Versão Consolidada: Varre o SQLite local e envia para a nuvem.
        Mantém o serviço vivo em loop infinito para o run_task do Flet.
        """
        while True:
            try:
                logger.info("🔄 AguaFlow: Iniciando ciclo de sincronização...")
                
                with Database.get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, unidade, leitura_agua, leitura_gas, tipo, data_leitura_atual
                        FROM leituras 
                        WHERE sincronizado = 0 
                        ORDER BY id ASC
                    """)
                    pendentes = cursor.fetchall()

                    if not pendentes:
                        logger.info("✅ Tudo em dia: Nada para sincronizar.")
                        await asyncio.sleep(60)
                        continue

                    logger.info(f"📦 {len(pendentes)} leituras pendentes encontradas.")

                    for item in pendentes:
                        # 1. Tenta o envio (Transação Atómica)
                        resultado = await cls._enviar_para_nuvem_transacao(conn, cursor, item)
                        
                        if resultado['sucesso']:
                            # 2. Sucesso: Marca localmente e regista log
                            cursor.execute("UPDATE leituras SET sincronizado = 1 WHERE id = ?", (item['id'],))
                            cls._registrar_log_sync(cursor, conn, item['id'], item['unidade'], "SUCESSO")
                            conn.commit()
                            logger.info(f"✔️ Unidade {item['unidade']} sincronizada.")
                        else:
                            # 3. Falha: Regista erro sem marcar como sincronizado
                            cls._registrar_log_sync(cursor, conn, item['id'], item['unidade'], "FALHA", resultado.get('erro'))
                            conn.commit()
                            logger.warning(f"❌ Falha na unidade {item['unidade']}: {resultado.get('erro')}")

                await asyncio.sleep(60) # Pausa entre ciclos
            except Exception as e:
                logger.error(f"Erro crítico no ciclo de sync: {e}")
                await asyncio.sleep(30)

    @classmethod
    async def _enviar_para_nuvem_transacao(cls, conn, cursor, item):
        """Simulação da lógica de upload (Substitui pela tua lógica Supabase)"""
        try:
            # await supabase.table('leituras').insert(...)
            return {'sucesso': True}
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

    @classmethod
    def _registrar_log_sync(cls, cursor, conn, leitura_id, unidade, status, erro=None):
        """Regista a auditoria da tentativa de sincronização"""
        try:
            cursor.execute("""
                INSERT INTO sync_log (leitura_id, unidade, status, erro_mensagem, ultima_tentativa)
                VALUES (?, ?, ?, ?, ?)
            """, (leitura_id, unidade, status, erro, dt.now().isoformat()))
        except Exception as e:
            logger.error(f"Erro ao registar log: {e}")

    @classmethod
    def gerar_relatorio_sync(cls, limite_dias=7):
        """Gera resumo de sucessos e falhas"""
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT unidade, status, COUNT(*) as quantidade, MAX(ultima_tentativa) as ultima 
                    FROM sync_log WHERE datetime(criado_em) >= datetime('now', ?)
                    GROUP BY unidade, status
                """, (f'-{limite_dias} days',))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro no relatório: {e}")
            return []

    @classmethod
    def limpar_logs_antigos(cls, dias_reter=30):
        """Limpeza de manutenção"""
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sync_log WHERE datetime(criado_em) < datetime('now', ?)", 
                             (f'-{dias_reter} days',))
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Erro na limpeza: {e}")
            return 0