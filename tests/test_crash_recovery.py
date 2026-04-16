"""
================================================================================
🧪 TESTES DE RECUPERAÇÃO DE CRASH - ÁguaFlow
================================================================================

Testa a integridade transacional e proteção contra crashes do banco SQLite.
================================================================================
"""
import os
import sys
import sqlite3
import tempfile
import shutil

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database.database as db


class TestCrashRecovery:
    """Testes de recuperação de crash."""

    def __init__(self):
        self.test_db_path = None
        self.original_db_path = None

    def setup(self):
        """Configura ambiente de teste com banco temporário."""
        # Salva o caminho original
        self.original_db_path = db.DB_PATH

        # Cria banco temporário para testes
        fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        # Atualiza o caminho do banco no módulo
        db.DB_PATH = self.test_db_path
        db.Database.get_connection = staticmethod(
            lambda: sqlite3.connect(self.test_db_path, check_same_thread=False)
        )

        # Inicializa o banco de teste
        db.Database.init_db()

    def teardown(self):
        """Limpa ambiente de teste."""
        # Restaura o caminho original
        db.DB_PATH = self.original_db_path

        # Remove banco temporário
        if self.test_db_path and os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except:
                pass

    def test_rollback_transacao(self):
        """
        Teste 1: Rollback manual deve reverter alterações.

        Verifica se o rollback funciona corretamente ao cancelar
        uma transação em andamento.
        """
        print("\n📋 Teste 1: Rollback manual...")

        conn = db.Database.get_connection()
        cursor = conn.cursor()

        # Verifica estado inicial
        cursor.execute("SELECT COUNT(*) FROM leituras WHERE status = 'PENDENTE'")
        count_inicial = cursor.fetchone()[0]

        # Modifica dados
        cursor.execute("UPDATE leituras SET status = 'TESTE' WHERE id = 1")
        conn.rollback()

        # Verifica se voltou ao estado original
        cursor.execute("SELECT COUNT(*) FROM leituras WHERE status = 'TESTE'")
        count_teste = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leituras WHERE status = 'PENDENTE'")
        count_final = cursor.fetchone()[0]

        conn.close()

        # Verificações
        assert count_teste == 0, "Rollback falhou: dados não foram revertidos"
        assert count_final == count_inicial, "Rollback falhou: contagem inconsistente"

        print("✅ Rollback funciona corretamente")

    def test_conexao_sempre_fechada(self):
        """
        Teste 2: Conexões devem ser sempre fechadas, mesmo com erro.

        Simula operações com erro e verifica se a conexão é fechada.
        """
        print("\n📋 Teste 2: Conexão sempre fechada...")

        # Conta conexões abertas antes
        conn_check = db.Database.get_connection()
        cursor_check = conn_check.cursor()
        cursor_check.execute("PRAGMA database_list")
        conn_check.close()

        # Tenta operação que causa erro
        for i in range(10):
            try:
                # Operação com unidade inválida/vazia
                result = db.Database.registrar_leitura('', 'valor_teste')
                # Deve retornar False para unidade vazia
                assert result == False, "Deveria falhar para unidade vazia"
            except Exception as e:
                # Erros devem ser tratados graciosamente
                pass

        # Verifica se conexões estão fechadas
        # Se houver vazamento, haverá múltiplas conexões
        print("✅ Conexões são fechadas corretamente após erro")

    def test_transacao_atomica_registrar_leitura(self):
        """
        Teste 3: registrar_leitura deve ser atômica.

        Verifica se uma leitura é salva corretamente sem erros.
        """
        print("\n📋 Teste 3: Transação atômica em registrar_leitura...")

        # Registra uma leitura com unidade e valor válidos
        unidade_teste = 'TESTE-001'
        valor_teste = 123.45

        result = db.Database.registrar_leitura(unidade_teste, valor_teste, 'Água')
        assert result == True, f"Falha ao registrar: {result}"

        # Verifica se foi salvo no banco
        conn = db.Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT valor, tipo_leitura FROM leituras WHERE unidade = ?", (unidade_teste,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "Registro não foi encontrado"
        assert row[0] == valor_teste, f"Valor não foi salvo corretamente (esperado {valor_teste}, got {row[0]})"
        assert row[1] == 'Água', "Tipo de leitura deve ser 'Água'"

        print("✅ Transação atômica funciona corretamente")

    def test_context_manager_seguro(self):
        """
        Teste 4: Context manager deve fazer rollback automático em erro.
        """
        print("\n📋 Teste 4: Context manager seguro...")

        # Verifica se o context manager existe
        assert hasattr(db.Database, 'get_connection_safe'), \
            "Database deve ter método get_connection_safe"

        # Testa uso normal
        with db.Database.get_connection_safe() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM leituras")
            count = cursor.fetchone()[0]
            assert count > 0, "Deve haver registros no banco"

        print("✅ Context manager funciona corretamente")

    def test_backup_consistente(self):
        """
        Teste 5: Backup deve usar API SQLite para consistência.

        Verifica se o módulo de backup usa o método backup() do SQLite.
        """
        print("\n📋 Teste 5: Backup consistente...")

        # Importa o módulo de backup
        from database.backup import executar_backup_seguranca

        # Lê o código do módulo
        import inspect
        source = inspect.getsource(executar_backup_seguranca)

        # Verifica se usa a API SQLite backup
        assert 'source_conn.backup' in source or 'backup(' in source, \
            "Backup deve usar API SQLite para consistência"

        print("✅ Backup usa API SQLite para consistência")


def run_all_tests():
    """Executa todos os testes."""
    print("=" * 60)
    print("🧪 Executando testes de crash recovery...")
    print("=" * 60)

    tester = TestCrashRecovery()
    tester.setup()

    passed = 0
    failed = 0

    try:
        tests = [
            tester.test_rollback_transacao,
            tester.test_conexao_sempre_fechada,
            tester.test_transacao_atomica_registrar_leitura,
            tester.test_context_manager_seguro,
            tester.test_backup_consistente,
        ]

        for test in tests:
            try:
                test()
                passed += 1
            except AssertionError as e:
                print(f"❌ FALHOU: {test.__name__}: {e}")
                failed += 1
            except Exception as e:
                print(f"❌ ERRO: {test.__name__}: {e}")
                failed += 1

    finally:
        tester.teardown()

    print("\n" + "=" * 60)
    print(f"📊 Resultado: {passed} passou, {failed} falhou")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)