import asyncio
import http.client
from database.database import Database
# No arquivo views/dashboard_saude.py


class DiagnosticoSistema:
    @staticmethod
    async def testar_banco():
        """Verifica se o banco de dados local responde."""
        try:
            # Tenta uma operação simples de leitura
            Database.init_db()
            return True, "Banco de Dados Local: OK"
        except Exception as e:
            return False, f"Erro no Banco: {str(e)}"

    @staticmethod
    async def testar_internet():
        """Verifica se há conexão com a internet (ping no Google)."""
        try:
            conn = http.client.HTTPSConnection("8.8.8.8", timeout=3)
            conn.request("HEAD", "/")
            return True, "Conexão Internet: OK"
        except:
            return False, "Sem acesso à Internet"

    @staticmethod
    async def executar_checkup_completo():
        """Executa todos os testes em sequência."""
        status_banco, msg_banco = await DiagnosticoSistema.testar_banco()
        status_net, msg_net = await DiagnosticoSistema.testar_internet()

        sucesso_geral = status_banco and status_net
        return sucesso_geral, f"{msg_banco} | {msg_net}"
