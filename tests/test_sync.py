import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# --- FORÇA O PYTHON A ENXERGAR A RAIZ DO PROJETO ---
# Isso permite que ele encontre a pasta 'utils' e 'database'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import Database
# IMPORT CORRIGIDO: Apontando para a pasta utils
from utils.sync_engine import SyncEngine 

class TestSync(unittest.TestCase):

    def setUp(self):
        """Prepara o banco local antes de cada teste."""
        Database.init_db()
        with Database.get_db() as conn:
            conn.execute("DELETE FROM leituras")
            conn.commit()

    @patch('utils.sync_engine.get_supabase_client') # Ajustado para o novo caminho
    def test_registrar_leitura_online_success(self, mock_get_client):
        """Simula sucesso no envio para o Supabase."""
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        
        # Simula uma leitura guardada localmente
        with Database.get_db() as conn:
            conn.execute(
                "INSERT INTO leituras (unidade, leitura_atual, data_leitura, sincronizado) VALUES (?, ?, ?, 0)",
                ("166-AGUA", 150.5, "2026-04-16T15:00:00")
            )
            conn.commit()

        # Chama o motor que está em utils
        status = SyncEngine.sincronizar_tudo()
        self.assertTrue("🚀" in status or "✅" in status)

    @patch('utils.sync_engine.get_supabase_client')
    def test_registrar_leitura_offline_failure(self, mock_get_client):
        """Simula falha de internet (Nuvem Offline)."""
        mock_get_client.return_value = None
        
        with Database.get_db() as conn:
            conn.execute(
                "INSERT INTO leituras (unidade, leitura_atual, data_leitura, sincronizado) VALUES (?, ?, ?, 0)",
                ("166-AGUA", 200.0, "2026-04-16T16:00:00")
            )
            conn.commit()
        
        status = SyncEngine.sincronizar_tudo()
        self.assertEqual(status, "❌ Erro: Nuvem não configurada")

if __name__ == "__main__":
    unittest.main()