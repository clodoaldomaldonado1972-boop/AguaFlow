import asyncio
from datetime import datetime
from .database import Database

class SyncService:
    """
    Serviço de Background responsável por gerir a fila de sincronização.
    Garante que o upload para o Supabase ocorra de forma organizada e sem duplicidade.
    """

    @classmethod
    async def sincronizar_leituras_pendentes(cls):
        """
        Varre o banco local em busca de registos com 'sincronizado = 0'
        e tenta realizar o upload para a nuvem.
        """
        print("🔄 SyncService: Iniciando verificação de pendências...")

        # 1. Busca os dados no banco local
        # IHC: Operação rápida para não consumir bateria se não houver dados
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, unidade, leitura_agua, leitura_gas, operador, data_hora_coleta 
                FROM leituras 
                WHERE sincronizado = 0
            """)
            pendentes = cursor.fetchall()

            if not pendentes:
                print("✅ SyncService: Nuvem já está atualizada.")
                return 0

            print(f"📡 SyncService: {len(pendentes)} leituras encontradas para upload.")

        # 2. Chama o motor de sincronismo do Database
        # Centralizamos a lógica de API no Database para facilitar a manutenção
        try:
            sucessos = await asyncio.to_thread(Database.sincronizar_com_nuvem)
            
            if sucessos > 0:
                print(f"✔️ SyncService: {sucessos} registos subiram para o Supabase.")
            
            return sucessos
            
        except Exception as e:
            print(f"⚠️ SyncService: Falha na comunicação com a nuvem: {e}")
            return 0

    @classmethod
    def marcar_para_reprocessamento(cls, leitura_id=None):
        """
        Caso um relatório precise ser reenviado, este método reseta o status de sincronia.
        Se leitura_id for None, reseta toda a tabela (Cuidado: uso administrativo).
        """
        with Database.get_db() as conn:
            cursor = conn.cursor()
            if leitura_id:
                cursor.execute("UPDATE leituras SET sincronizado = 0 WHERE id = ?", (leitura_id,))
            else:
                cursor.execute("UPDATE leituras SET sincronizado = 0")
            conn.commit()
            print("🔄 SyncService: Registos marcados para nova sincronização.")

    @classmethod
    async def verificar_status_nuvem(cls):
        """
        Verifica a latência ou disponibilidade do Supabase antes de iniciar grandes uploads.
        """
        # Futura implementação de telemetria para o Dashboard de Saúde
        pass