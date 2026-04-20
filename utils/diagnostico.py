import asyncio
import http.client
from database.database import Database

class DiagnosticoSistema:
    """
    Realiza verificações de saúde no ecossistema AguaFlow.
    Garante que o zelador não inicie o trabalho com falhas críticas de sistema.
    """

    @staticmethod
    async def testar_banco():
        """
        Verifica se o SQLite local está acessível e funcional.
        IHC: Crucial para o funcionamento offline no subsolo.
        """
        try:
            # Executa a inicialização em thread separada para manter a fluidez da UI
            # Ajustado para usar 'inicializar' conforme definido no seu database.py
            await asyncio.to_thread(Database.inicializar) 
            return True, "Banco de Dados Local: OK"
        except Exception as e:
            return False, f"Erro no Banco: {str(e)}"

    @staticmethod
    async def testar_internet():
        """
        Realiza um 'ping' rápido nos servidores do Google (DNS) para checar o sinal.
        Útil para saber se o Sincronismo com o Supabase é possível no momento.
        """
        loop = asyncio.get_running_loop()
        try:
            # Teste de conexão leve com timeout de 3 segundos
            def check():
                conn = http.client.HTTPSConnection("8.8.8.8", timeout=3)
                conn.request("HEAD", "/")
                return True
            
            await loop.run_in_executor(None, check)
            return True, "Conexão Internet: OK"
        except Exception:
            return False, "Sem acesso à Internet (Modo Offline)"

    @staticmethod
    async def executar_checkup_completo():
        """
        Orquestra todos os testes e devolve um relatório simplificado.
        Utilizado na tela de Configurações e no Dashboard de Saúde.
        """
        status_banco, msg_banco = await DiagnosticoSistema.testar_banco()
        status_net, msg_net = await DiagnosticoSistema.testar_internet()
        
        # O sistema é considerado 'Saudável' se o banco local estiver 100%
        sucesso_geral = status_banco
        
        resumo = f"{msg_banco}\n{msg_net}"
        
        if status_banco and status_net:
            resumo += "\n\n🚀 Sistema operando com capacidade total (Nuvem + Local)."
        elif status_banco:
            resumo += "\n\n⚠️ Operando em Modo Offline. Sincronize quando houver sinal."
            
        return sucesso_geral, resumo