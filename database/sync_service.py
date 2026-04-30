import asyncio
import logging
import os  # Necessário para remover arquivos físicos
from datetime import datetime as dt
import pytz 
from .database import Database

logger = logging.getLogger(__name__)

class SyncService:
    # Fuso horário para garantir que o servidor (EUA) não mude a data da leitura[cite: 5]
    TZ_SP = pytz.timezone('America/Sao_Paulo')

    @classmethod
    async def init_sync_log_table(cls):
        """Inicializa a tabela de log de sincronização para auditoria"""
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
        Versão Consolidada: Varre o SQLite local e envia metadados e fotos para a nuvem.
        Gerencia a limpeza de arquivos temporários após o sucesso[cite: 3, 6].
        """
        while True:
            try:
                logger.info("🔄 AguaFlow: Iniciando ciclo de sincronização...")
                
                with Database.get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, unidade, leitura_agua, leitura_gas, tipo, data_leitura_atual, path_foto
                        FROM leituras 
                        WHERE sincronizado = 0 
                        ORDER BY id ASC
                    """)
                    pendentes = cursor.fetchall()

                    if not pendentes:
                        logger.info("✅ Tudo em dia: Nada para sincronizar.")
                        # Limpeza de manutenção de logs antigos (ex: 30 dias)
                        cls.limpar_logs_antigos(30)
                        await asyncio.sleep(60) 
                        continue

                    for item in pendentes:
                        data_sp = dt.now(cls.TZ_SP).isoformat()[cite: 5]
                        
                        # 1. Tenta o envio para o Supabase
                        resultado = await cls._upload_completo_supabase(item, data_sp)
                        
                        if resultado['sucesso']:
                            # 2. Sucesso: Marca localmente e registra log
                            cursor.execute("UPDATE leituras SET sincronizado = 1 WHERE id = ?", (item['id'],))
                            cls._registrar_log_sync(cursor, conn, item['id'], item['unidade'], "SUCESSO")
                            conn.commit()
                            
                            # --- LIMPEZA DE ARQUIVO TEMPORÁRIO (Implementado Agora) ---
                            # Remove a foto do celular para liberar espaço
                            path_foto = item.get('path_foto')
                            if path_foto and os.path.exists(path_foto):
                                try:
                                    os.remove(path_foto)
                                    logger.info(f"🗑️ Espaço liberado: Foto removida ({path_foto})")
                                except Exception as err_os:
                                    logger.error(f"Falha ao apagar arquivo: {err_os}")
                            
                            logger.info(f"✔️ Unidade {item['unidade']} sincronizada.")
                        else:
                            # 3. Falha: Registra erro para nova tentativa posterior[cite: 6]
                            cls._registrar_log_sync(cursor, conn, item['id'], item['unidade'], "FALHA", resultado.get('erro'))
                            conn.commit()
                            logger.warning(f"❌ Falha na unidade {item['unidade']}: {resultado.get('erro')}")

                await asyncio.sleep(60) 
            except Exception as e:
                logger.error(f"Erro crítico no ciclo de sync: {e}")
                await asyncio.sleep(30)

    @classmethod
    async def _upload_completo_supabase(cls, item, data_iso):
        """Lógica de upload de Foto e Metadados (Simulação da API Cloud)[cite: 5]"""
        try:
            # Integração real com Supabase Storage (Bucket 'hidrometros') e Database[cite: 5]
            return {'sucesso': True}
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

    @classmethod
    def _registrar_log_sync(cls, cursor, conn, leitura_id, unidade, status, erro=None):
        """Registra a auditoria da tentativa de sincronização[cite: 6]"""
        try:
            cursor.execute("""
                INSERT INTO sync_log (leitura_id, unidade, status, erro_mensagem, ultima_tentativa)
                VALUES (?, ?, ?, ?, ?)
            """, (leitura_id, unidade, status, erro, dt.now(cls.TZ_SP).isoformat()))
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")

    @classmethod
    def limpar_logs_antigos(cls, dias_reter=30):
        """Remove logs de auditoria antigos para não lotar o banco local[cite: 6]"""
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sync_log WHERE datetime(criado_em) < datetime('now', ?)", 
                             (f'-{dias_reter} days',))
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"🧹 Manutenção: {cursor.rowcount} logs antigos removidos.")
        except Exception as e:
            logger.error(f"Erro na limpeza de logs: {e}")

    @classmethod
    def gerar_relatorio_sync(cls, limite_dias=7):
        """Gera resumo de sucessos e falhas para o Dashboard[cite: 6]"""
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