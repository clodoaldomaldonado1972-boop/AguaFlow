import asyncio
import logging
import os
from database.database import Database
from utils.backup import executar_backup_seguranca
from relatorio_engine import RelatorioEngine
from utils.email_service import enviar_relatorios_por_email

logger = logging.getLogger(__name__)


async def finalizar_mes_e_enviar(email_destino: str = None) -> bool:
    """
    Executa o ciclo de fechamento mensal de forma assíncrona:
      1. Backup de segurança
      2. Busca leituras do mês corrente
      3. Gera relatórios (PDF/CSV)
      4. Salva leituras atuais como referência do próximo ciclo (leitura_atual → leitura_anterior)
      5. Envia relatórios por e-mail
      6. Reseta banco para o novo mês
    Todas as operações bloqueantes são executadas via asyncio.to_thread.
    """
    try:
        # 1. Backup antes de qualquer modificação
        sucesso_backup = await asyncio.to_thread(executar_backup_seguranca)
        if not sucesso_backup:
            logger.error("Falha no backup de segurança — operação de fechamento cancelada.")
            return False

        # 2. Leituras do mês corrente
        dados = await asyncio.to_thread(Database.get_leituras_mes_atual)
        if not dados:
            logger.warning("Nenhuma leitura encontrada para o mês atual.")
            return False

        # 3. Gera arquivos de relatório (bloqueante — PDF/CSV em disco)
        arquivos = await asyncio.to_thread(RelatorioEngine.gerar_todos, dados, "Sistema")
        if not arquivos:
            logger.error("Falha ao gerar relatórios para o fechamento mensal.")
            return False

        # 4. Transfere leitura_atual → leitura_anterior (referência do próximo ciclo)
        await asyncio.to_thread(Database.salvar_referencias_ciclo, dados)
        logger.info("Referências de ciclo salvas — leitura_atual transferida para leitura_anterior.")

        # 5. Envia relatórios por e-mail (SMTP — bloqueante)
        lista_caminhos = list(arquivos.values())
        enviou = await asyncio.to_thread(enviar_relatorios_por_email, lista_caminhos)
        if not enviou:
            logger.error("Falha no envio de e-mail. Ciclo não resetado.")
            return False

        # 6. Reseta banco para o novo ciclo mensal
        resetado = await asyncio.to_thread(_resetar_banco_para_novo_mes)
        return resetado

    except Exception as e:
        logger.error(f"Erro ao finalizar mês: {e}", exc_info=True)
        return False


def _resetar_banco_para_novo_mes() -> bool:
    """
    Limpa leituras do período mantendo referências (leitura_anterior já salva).
    Chamado exclusivamente via asyncio.to_thread.
    """
    try:
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE leituras SET
                    leitura_agua       = NULL,
                    leitura_gas        = NULL,
                    sincronizado       = 0,
                    data_leitura_atual = NULL,
                    tipo               = COALESCE(tipo, 'manual')
            """)
            conn.commit()
        logger.info("Banco preparado para o novo ciclo mensal.")
        return True
    except Exception as e:
        logger.error(f"Erro no reset do banco: {e}", exc_info=True)
        return False
