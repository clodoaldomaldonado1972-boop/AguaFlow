import asyncio
import http.client
from database.database import Database

class DiagnosticoSistema:
    @staticmethod
    async def testar_banco():
        # Humanizando: "Ei Python, rode o banco em uma thread separada para não congelar a tela"
        try:
            await asyncio.to_thread(Database.init_db) 
            return True, "Banco de Dados Local: OK"
        except Exception as e:
            return False, f"Erro no Banco: {str(e)}"

    @staticmethod
    async def testar_internet():
        loop = asyncio.get_running_loop()
        try:
            # Humanizando: Criamos uma pequena tarefa de teste rápida (timeout de 3s)
            def check():
                conn = http.client.HTTPSConnection("8.8.8.8", timeout=3)
                conn.request("HEAD", "/")
                return True
            
            await loop.run_in_executor(None, check)
            return True, "Conexão Internet: OK"
        except:
            return False, "Sem acesso à Internet"

    @staticmethod
    async def executar_checkup_completo():
        # Humanizando: Espera o resultado de um, depois do outro, sem pressa.
        status_banco, msg_banco = await DiagnosticoSistema.testar_banco()
        status_net, msg_net = await DiagnosticoSistema.testar_internet()
        sucesso_geral = status_banco and status_net
        return sucesso_geral, f"{msg_banco} | {msg_net}"