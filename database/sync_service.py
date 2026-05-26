import asyncio
import logging
import os  # Necessário para remover arquivos físicos
from datetime import datetime as dt
import traceback
import pytz
from .database import Database

logger = logging.getLogger(__name__)


class SyncService:
    # Fuso horário para garantir que o servidor (EUA) não mude a data da leitura
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
                        unidade_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        erro_mensagem TEXT,
                        tentativas INTEGER DEFAULT 1,
                        ultima_tentativa TEXT,
                        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar tabela sync_log: {e}", exc_info=True)

    @classmethod
    async def processar_fila(cls):
        """
        Versão Consolidada: Varre o SQLite local e envia metadados e fotos para a nuvem.
        Gerencia a limpeza de arquivos temporários após o sucesso.
        """
        while True:
            try:
                logger.info("🔄 AguaFlow: Iniciando ciclo de sincronização...")

                with Database.get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT
                            id,
                            unidade_id,
                            leitura_agua,
                            leitura_gas,
                            tipo,
                            data_hora_coleta,
                            path_foto,
                            leiturista,
                            foto_url
                        FROM leituras
                        WHERE sincronizado = 0
                        ORDER BY id ASC
                        LIMIT 50
                    """)
                    pendentes = [dict(r) for r in cursor.fetchall()]

                    if not pendentes:
                        logger.info("✅ Tudo em dia: Nada para sincronizar.")
                        # Limpeza de manutenção de logs antigos (ex: 30 dias)
                        cls.limpar_logs_antigos(30)
                        await asyncio.sleep(60)
                        continue

                    for item in pendentes:
                        data_sp = dt.now(cls.TZ_SP).isoformat()

                        # 1. Tenta o envio para o Supabase
                        # Garantia: Tenta enviar Água e Gás separadamente se existirem no mesmo registro
                        sucesso_sync = True

                        if item['leitura_agua'] is not None:
                            res_agua = await cls._upload_individual(item, item['leitura_agua'], "Água", data_sp)
                            if not res_agua['sucesso']:
                                sucesso_sync = False

                        if item['leitura_gas'] is not None:
                            res_gas = await cls._upload_individual(item, item['leitura_gas'], "Gás", data_sp)
                            if not res_gas['sucesso']:
                                sucesso_sync = False

                        # O registro local só é marcado como sincronizado se ambos subirem com sucesso
                        resultado = {'sucesso': sucesso_sync}

                        if resultado['sucesso']:
                            # 2. Sucesso: Marca localmente e registra log
                            cursor.execute(
                                "UPDATE leituras SET sincronizado = 1 WHERE id = ?", (item['id'],))
                            cls._registrar_log_sync(
                                cursor, conn, item['id'], item['unidade_id'], "SUCESSO")
                            conn.commit()

                            # --- LIMPEZA DE ARQUIVO TEMPORÁRIO (Implementado Agora) ---
                            # Remove a foto do celular para liberar espaço
                            path_foto = item.get('path_foto')
                            if path_foto and os.path.exists(path_foto):
                                try:
                                    os.remove(path_foto)
                                    logger.info(
                                        f"🗑️ Espaço liberado: Foto removida ({path_foto})")
                                except Exception as err_os:
                                    logger.error(
                                        f"Falha ao apagar arquivo: {err_os}")

                            logger.info(
                                f"✔️ Unidade {item['unidade_id']} sincronizada.")
                        else:
                            # 3. Falha: conta tentativas e desiste após 5
                            cursor.execute(
                                "SELECT COUNT(*) FROM sync_log WHERE leitura_id = ? AND status = 'FALHA'",
                                (item['id'],))
                            n_falhas = cursor.fetchone()[0]
                            cls._registrar_log_sync(
                                cursor, conn, item['id'], item['unidade_id'], "FALHA", resultado.get('erro'))
                            if n_falhas >= 4:
                                cursor.execute(
                                    "UPDATE leituras SET sincronizado = -1 WHERE id = ?", (item['id'],))
                                logger.warning(
                                    f"⛔ Unidade {item['unidade_id']}: 5 falhas consecutivas, marcado como ignorado.")
                            else:
                                logger.warning(
                                    f"❌ Falha na unidade {item['unidade_id']} ({n_falhas + 1}/5): {resultado.get('erro')}")
                            conn.commit()

                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"❌ ERRO CRÍTICO NO SYNC SERVICE: {str(e)}", exc_info=True)
                # Gatilho de E-mail para crash do serviço de sincronia
                from utils.logger_config import enviar_report_erro
                enviar_report_erro(traceback.format_exc(), unidade="SYNC LOOP")
                await asyncio.sleep(30)

    @classmethod
    async def _upload_individual(cls, item, valor, tipo_reg, data_iso):
        """Lógica de upload individual para cada tipo de leitura (Água ou Gás)"""
        try:
            from database.database import get_supabase_client
            supabase = get_supabase_client()
            if not supabase:
                return {'sucesso': False, 'erro': 'Sem conexão com Supabase'}

            # Mapeamento para as novas colunas específicas do Supabase (v1.2.0)
            dados = {
                "unidade_id": item['unidade_id'],
                "tipo_registro": tipo_reg,
                "leiturista": item.get('leiturista') or 'Zelador',
                "data_hora_coleta": item['data_hora_coleta'] or data_iso
            }

            # Envia o valor para as colunas correspondentes
            # valor_leitura = leitura manual; OCR pode sobrescrever depois
            dados["valor_leitura"] = valor or 0
            if "Água" in tipo_reg or "AGUA" in tipo_reg:
                dados["leitura_agua"] = valor
            elif "Gás" in tipo_reg or "GAS" in tipo_reg:
                dados["leitura_gas"] = valor

            # Associa a foto ao registro se disponível
            foto_url = item.get('foto_url')
            if foto_url:
                dados["foto_url"] = foto_url

            # Realiza a inserção no Supabase (em thread para não bloquear o event loop)
            await asyncio.to_thread(
                lambda: supabase.table("leituras").insert(dados).execute()
            )
            return {'sucesso': True}
        except Exception as e:
            err_str = str(e).lower()
            # Trata violação de unicidade como sucesso — registro já existe no Supabase
            if any(k in err_str for k in ("duplicate", "unique", "registro_unico", "23505")):
                logger.info(
                    f"Sync idempotente ({item['unidade_id']}): registro já existe no Supabase.")
                return {'sucesso': True}
            logger.error(f"Erro no upload individual ({item['unidade_id']}): {e}")
            return {'sucesso': False, 'erro': str(e)}

    @classmethod
    def _registrar_log_sync(cls, cursor, conn, leitura_id, unidade, status, erro=None):
        """Registra a auditoria da tentativa de sincronização[cite: 6]"""
        try:
            cursor.execute("""
                INSERT INTO sync_log (leitura_id, unidade_id, status, erro_mensagem, ultima_tentativa)
                VALUES (?, ?, ?, ?, ?)
            """, (leitura_id, unidade, status, erro, dt.now(cls.TZ_SP).isoformat()))
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")

    @classmethod
    async def executar_sincronismo_manual(cls):
        """Executa uma rodada de sincronização e retorna a quantidade de itens processados."""
        total_sincronizado = 0
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, unidade_id, leitura_agua, leitura_gas, tipo, data_hora_coleta, path_foto, leiturista, foto_url
                    FROM leituras WHERE sincronizado = 0
                """)
                pendentes = [dict(r) for r in cursor.fetchall()]

                for item in pendentes:
                    data_sp = dt.now(cls.TZ_SP).isoformat()
                    sucesso_item = True
                    
                    if item['leitura_agua'] is not None:
                        res = await cls._upload_individual(item, item['leitura_agua'], "Água", data_sp)
                        if not res['sucesso']: sucesso_item = False
                        
                    if item['leitura_gas'] is not None:
                        res = await cls._upload_individual(item, item['leitura_gas'], "Gás", data_sp)
                        if not res['sucesso']: sucesso_item = False

                    if sucesso_item:
                        cursor.execute(
                            "UPDATE leituras SET sincronizado = 1 WHERE id = ?", (item['id'],))
                        cls._registrar_log_sync(
                            cursor, conn, item['id'], item['unidade_id'], "SUCESSO")

                        path_foto = item.get('path_foto')
                        if path_foto and os.path.exists(path_foto):
                            try:
                                os.remove(path_foto)
                            except:
                                pass
                        total_sincronizado += 1
                conn.commit()
            return total_sincronizado
        except Exception as e:
            logger.error(f"Erro no sincronismo manual: {e}")
            return 0

    @classmethod
    def limpar_leituras_locais(cls):
        """Remove todas as leituras sincronizadas para iniciar um novo ciclo."""
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                # Removemos apenas o que já foi enviado para a nuvem
                cursor.execute("DELETE FROM leituras WHERE sincronizado = 1")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Erro ao limpar banco local: {e}")
            return False

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
                    logger.info(
                        f"🧹 Manutenção: {cursor.rowcount} logs antigos removidos.")
        except Exception as e:
            logger.error(f"Erro na limpeza de logs: {e}")

    @classmethod
    def gerar_relatorio_sync(cls, limite_dias=7):
        """Gera resumo de sucessos e falhas para o Dashboard[cite: 6]"""
        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT unidade_id, status, COUNT(*) as quantidade, MAX(ultima_tentativa) as ultima 
                    FROM sync_log WHERE datetime(criado_em) >= datetime('now', ?)
                    GROUP BY unidade_id, status
                """, (f'-{limite_dias} days',))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro no relatório: {e}")
            return []
