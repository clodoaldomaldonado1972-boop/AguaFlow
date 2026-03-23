from database.database import Database
import unittest
import sqlite3
import sys
import os
from unittest.mock import MagicMock, patch

# --- PATH SETUP ---
# Adjust path to import from database module relative to this test file
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class TestSync(unittest.TestCase):
    def setUp(self):
        # Create an in-memory database for isolated testing
        self.mock_db = sqlite3.connect(':memory:')
        self.cursor = self.mock_db.cursor()

        # Create the table schema expected by the method
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS leituras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unidade TEXT NOT NULL,
                leitura_anterior REAL DEFAULT 0.0,
                leitura_atual REAL DEFAULT NULL,
                tipo TEXT DEFAULT 'AGUA',
                status TEXT DEFAULT 'PENDENTE',
                ordem INTEGER,
                data_leitura TEXT,
                sincronizado INTEGER DEFAULT 0,
                CHECK(leitura_anterior >= 0),
                CHECK(leitura_atual IS NULL OR leitura_atual > 0)
            )
        """)

        # Insert a sample pending record
        self.cursor.execute(
            "INSERT INTO leituras (id, unidade, leitura_anterior, status, ordem) VALUES (?, ?, ?, ?, ?)",
            (1, '101', 100.0, 'PENDENTE', 1)
        )
        self.mock_db.commit()

    def tearDown(self):
        self.mock_db.close()

    @patch('database.database.sqlite3.connect')
    def test_registrar_leitura_online_success(self, mock_connect):
        """
        Testa o 'Caminho Feliz': Banco conecta e Supabase sincroniza.
        Verifica se 'sincronizado' é atualizado para 1.
        """
        mock_connect.return_value = self.mock_db

        # Mock do objeto Supabase
        mock_supabase = MagicMock()
        # Simula resposta de sucesso do Supabase
        mock_supabase.table.return_value.insert.return_value.execute.return_value = {
            "data": [], "count": 1}

        # Injeta o mock no lugar da propriedade estática Database.supabase
        with patch.object(Database, 'supabase', mock_supabase):
            # Act
            resultado = Database.registrar_leitura(id_db=1, valor=150.5)

            # Assert - Retorno da função
            self.assertTrue(resultado['sucesso'], "Deve retornar sucesso=True")
            self.assertTrue(resultado['supabase_sync'],
                            "Deve indicar sync com Supabase")

            # Assert - Banco de Dados Local
            self.cursor.execute(
                "SELECT leitura_atual, status, sincronizado FROM leituras WHERE id=1")
            row = self.cursor.fetchone()
            self.assertEqual(row[0], 150.5, "Valor da leitura deve ser salvo")
            self.assertEqual(row[1], 'CONCLUIDO',
                             "Status deve mudar para CONCLUIDO")
            self.assertEqual(row[2], 1, "Flag sincronizado deve ser 1")

            # Assert - Chamada Supabase
            mock_supabase.table.assert_called_with("leituras")
            mock_supabase.table().insert.assert_called_once()

    @patch('database.database.sqlite3.connect')
    def test_registrar_leitura_offline_failure(self, mock_connect):
        """
        Testa o 'Caminho Offline': Falha na conexão com Supabase ou chave ausente.
        Verifica se salva localmente mas mantém 'sincronizado' como 0.
        """
        mock_connect.return_value = self.mock_db

        # Cenário 1: Supabase é None (chaves não configuradas ou erro de init)
        with patch.object(Database, 'supabase', None):
            resultado = Database.registrar_leitura(id_db=1, valor=150.5)

            self.assertTrue(
                resultado['sucesso'], "Deve salvar localmente mesmo sem Supabase")
            self.assertFalse(
                resultado['supabase_sync'], "Não deve indicar sync")

            # Verifica banco local
            self.cursor.execute("SELECT sincronizado FROM leituras WHERE id=1")
            self.assertEqual(self.cursor.fetchone()[
                             0], 0, "Flag sincronizado deve continuar 0")

        # Cenário 2: Supabase lança exceção (ex: sem internet)
        mock_supabase_error = MagicMock()
        mock_supabase_error.table.return_value.insert.side_effect = Exception(
            "Connection Refused")

        with patch.object(Database, 'supabase', mock_supabase_error):
            # Reset do status para teste
            self.cursor.execute(
                "UPDATE leituras SET status='PENDENTE', sincronizado=0 WHERE id=1")

            resultado = Database.registrar_leitura(id_db=1, valor=160.0)

            self.assertTrue(
                resultado['sucesso'], "Deve salvar localmente mesmo com erro de rede")
            self.assertFalse(resultado['supabase_sync'])


if __name__ == '__main__':
    unittest.main()
