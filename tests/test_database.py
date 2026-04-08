from database.database import Database
import unittest
import sqlite3
import sys
import os
from unittest.mock import patch

# Adiciona a pasta raiz ao caminho de busca do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ... restante do código da classe TestDatabase ...


class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Create an in-memory database for isolated testing
        self.mock_db = sqlite3.connect(':memory:')
        self.cursor = self.mock_db.cursor()

        # Create the table schema expected by the method
        # Note: Keeping schema in sync with database.py
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
        self.mock_db.commit()

    def tearDown(self):
        self.mock_db.close()

    @patch('database.database.sqlite3.connect')
    def test_buscar_proximo_pendente_tuple_structure(self, mock_connect):
        # Mock the connection to use our in-memory DB
        mock_connect.return_value = self.mock_db

        # Insert a sample record
        self.cursor.execute(
            "INSERT INTO leituras (unidade, leitura_anterior, status, ordem) VALUES (?, ?, ?, ?)",
            ('101', 500.0, 'PENDENTE', 1)
        )
        self.mock_db.commit()

        # Act
        result = Database.buscar_proximo_pendente()

        # Assert: Expecting (id, unidade, leitura_anterior)
        self.assertIsNotNone(result, "Should return a record")
        self.assertIsInstance(result, tuple)
        self.assertEqual(
            len(result), 3, "Tuple must have 3 elements: id, unit, previous_reading")
        # Check values
        self.assertIsInstance(result[0], int)  # id
        self.assertEqual(result[1], '101')    # unidade
        self.assertEqual(result[2], 500.0)    # anterior


if __name__ == '__main__':
    unittest.main()
