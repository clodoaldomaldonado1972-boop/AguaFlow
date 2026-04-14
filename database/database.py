import os
import sqlite3
from datetime import datetime as dt
from contextlib import contextmanager
from dotenv import load_dotenv

# Carrega configurações sensíveis do .env.txt
load_dotenv()

class Database:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")

    @classmethod
    @contextmanager
    def get_db(cls):
        """Gerencia a conexão SQLite de forma segura (Context Manager)."""
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        """Inicializa tabelas e popula a lista estática de unidades (Andares 16 ao 1)."""
        with cls.get_db() as conn:
            cursor = conn.cursor()
            # Tabela de unidades estáticas
            cursor.execute("CREATE TABLE IF NOT EXISTS unidades (id TEXT PRIMARY KEY)")
            
            # Tabela de leituras (Água é obrigatória, Gás é opcional)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unidade TEXT,
                    leitura_agua REAL NOT NULL,
                    leitura_gas REAL,
                    data_leitura TEXT,
                    sincronizado INTEGER DEFAULT 0
                )
            """)

            # Popula as unidades seguindo a lógica: 166-161, 156-151... 16-11
            # Mais as unidades especiais: Lazer Gás e Geral Água
            unidades_projeto = cls._gerar_lista_unidades()
            
            cursor.executemany(
                "INSERT OR IGNORE INTO unidades (id) VALUES (?)",
                [(u,) for u in unidades_projeto]
            )
            conn.commit()

    @classmethod
    def _gerar_lista_unidades(cls):
        """
        Gera a lista fixa de unidades para o condomínio.
        Ordem: Andares 16 ao 1, Apartamentos 6 ao 1 por andar.
        """
        lista = []
        for andar in range(16, 0, -1):
            for apto in range(6, 0, -1):
                # Formato: 166, 165, 164, 163, 162, 161...
                lista.append(f"{andar}{apto}")
        
        # Unidades especiais de controle
        lista.append("Lazer Gás")
        lista.append("Geral Água")
        return lista

    @classmethod
    def registrar_leitura(cls, unidade, valor_agua, valor_gas=None):
        """
        Salva a leitura localmente. 
        REGRA: Água é obrigatória. Gás é opcional.
        """
        if not valor_agua:
            return {'sucesso': False, 'mensagem': "Erro: A leitura de Água é obrigatória."}

        agora = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Tratamento de string para float (vírgula para ponto)
            v_agua = float(str(valor_agua).replace(',', '.'))
            v_gas = float(str(valor_gas).replace(',', '.')) if valor_gas else None

            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO leituras (unidade, leitura_agua, leitura_gas, data_leitura) 
                    VALUES (?, ?, ?, ?)
                """, (unidade, v_agua, v_gas, agora))
                conn.commit()
                return {'sucesso': True, 'id': cursor.lastrowid}
        except Exception as e:
            return {'sucesso': False, 'mensagem': f"Erro ao gravar banco: {str(e)}"}

    @classmethod
    def buscar_ultima_unidade_lida(cls):
        """Retorna o ID da última unidade registrada para validar o 'pulo' de hall."""
        with cls.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT unidade FROM leituras ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row['unidade'] if row else None

    @classmethod
    def buscar_todas_leituras(cls):
        """Busca histórico completo para alimentar os Dashboards."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT unidade, leitura_agua, leitura_gas, data_leitura 
                    FROM leituras 
                    ORDER BY id DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Erro Dashboard: {e}")
            return []

    @classmethod
    def buscar_relatorio_geral(cls):
        """Consolida dados para exportação (PDF/CSV)."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                # Busca a leitura mais recente de cada unidade
                cursor.execute("""
                    SELECT unidade, leitura_agua, leitura_gas, data_leitura 
                    FROM leituras 
                    GROUP BY unidade 
                    ORDER BY id ASC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Erro Relatório: {e}")
            return []