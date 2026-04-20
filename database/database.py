import os
import sqlite3
import time
import logging
from contextlib import contextmanager
from datetime import datetime, date  # ✅ Adicionado 'date' aqui
# Importação da versão centralizada do projeto
try:
    from utils.updater import VERSION
except ImportError:
    VERSION = "1.1.0"

# Logger para erros de validação
logger = logging.getLogger(__name__)

class Database:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")
    
    @classmethod
    @contextmanager
    def get_db(cls):
        """Gerencia a conexão com o SQLite garantindo o fechamento seguro."""
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row 
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    async def init_db(cls):
        """Inicializa o banco de dados e as tabelas necessárias."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leituras (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        unidade TEXT NOT NULL,
                        leitura_agua REAL NOT NULL,
                        leitura_gas REAL DEFAULT 0,
                        tipo TEXT,
                        sincronizado INTEGER DEFAULT 0,
                        data_leitura TEXT
                    )
                """)
                # Garante que colunas extras existam para compatibilidade
                for col in ["data_leitura", "tipo"]:
                    try:
                        cursor.execute(f"ALTER TABLE leituras ADD COLUMN {col} TEXT")
                    except sqlite3.OperationalError:
                        pass

                # Tabela de log de sincronização para rastrear falhas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        leitura_id INTEGER NOT NULL,
                        unidade TEXT NOT NULL,
                        status TEXT NOT NULL,
                        erro_mensagem TEXT,
                        tentativas INTEGER DEFAULT 1,
                        ultima_tentativa TEXT,
                        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sync_log_unidade
                    ON sync_log(unidade)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_sync_log_status
                    ON sync_log(status)
                """)

                conn.commit()
                print("✅ Banco de dados local SQLite inicializado com sucesso.")
        except Exception as e:
            print(f"❌ [ERRO DB] Falha na inicialização: {e}")

    @classmethod
    def _gerar_lista_unidades(cls):
        """
        Gera a lista de unidades do Edifício Vivere:
        1. Remove finais inexistentes: 7, 8, 9 e 0.
        2. Agrupa Duplex: 163/164 e 23/24.
        """
        lista_final = []
        
        # Percorre de 166 até 11 (decrescente)
        for i in range(166, 10, -1):
            final = i % 10
            
            # FILTRO: Pula finais que não existem no prédio
            if final in [7, 8, 9, 0]:
                continue
                
            unidade_str = str(i)
            
            # REGRA: Unidades Duplex
            if unidade_str == "164":
                lista_final.append("163/164")
            elif unidade_str == "163":
                continue # Pula pois já está no par acima
            elif unidade_str == "24":
                lista_final.append("23/24")
            elif unidade_str == "23":
                continue # Pula pois já está no par acima
            else:
                lista_final.append(unidade_str)

        # Adiciona medidores de serviço
        lista_final += ["Gás Lazer", "Geral Água"]
        return lista_final

    @classmethod
    def salvar_leitura(cls, unidade, agua, gas, tipo=None, permitir_forcagem=False):
        """
        Salva a medição com validações de integridade.

        Validações implementadas:
        1. Bloqueia leitura duplicada no mesmo dia
        2. Valida se leitura atual >= anterior (detecta erro de OCR)
        3. Retry automático para 'database is locked'

        Args:
            unidade: Número da unidade/apartamento
            agua: Leitura de água em m³
            gas: Leitura de gás em m³
            tipo: Versão do app
            permitir_forcagem: Se True, permite salvar mesmo com validação falhando

        Returns:
            dict: {'sucesso': bool, 'mensagem': str, 'codigo': str}
        """
        # Captura o momento exato do salvamento (Dinâmico)
        agora = datetime.now()
        data_hora_txt = agora.strftime("%Y-%m-%d %H:%M:%S") # Para o campo data_leitura
        data_hoje_txt = agora.strftime("%Y-%m-%d")           # Para verificação de duplicidade

        max_retries = 3
        retry_delay = 0.5  # segundos

        for tentativa in range(max_retries):
            try:
                if tipo is None:
                    tipo = VERSION

                with cls.get_db() as conn:
                    cursor = conn.cursor()

                    # VALIDAÇÃO 1: Verificar leitura duplicada no mesmo dia
                    if not permitir_forcagem:
                        hoje = date.now().strftime("%Y-%m-%d")
                        cursor.execute("""
                            SELECT id, leitura_agua FROM leituras
                            WHERE unidade = ? AND DATE(data_leitura) = ?
                            ORDER BY data_leitura DESC LIMIT 1
                        """, (unidade, hoje))

                        leitura_existente = cursor.fetchone()

                        if leitura_existente:
                            msg = f"Já existe leitura para unidade {unidade} hoje ({hoje})"
                            logger.warning(f"⚠️ DUPLICADA: {msg}")
                            return {
                                'sucesso': False,
                                'mensagem': msg,
                                'codigo': 'DUPLICADA'
                            }

                    # VALIDAÇÃO 2: Verificar se leitura atual >= anterior
                    try:
                        agua_float = float(agua.replace(',', '.'))
                    except (ValueError, AttributeError):
                        return {
                            'sucesso': False,
                            'mensagem': 'Valor de água inválido',
                            'codigo': 'INVALIDO'
                        }

                    if not permitir_forcagem:
                        cursor.execute("""
                            SELECT leitura_agua, data_leitura FROM leituras
                            WHERE unidade = ?
                            ORDER BY data_leitura DESC LIMIT 1
                        """, (unidade,))

                        ultima_leitura = cursor.fetchone()

                        if ultima_leitura:
                            leitura_anterior = ultima_leitura['leitura_agua']

                            if agua_float < leitura_anterior:
                                msg = (f"Leitura atual ({agua_float}m³) é MENOR que a anterior "
                                       f"({leitura_anterior}m³). Possível erro de OCR!")
                                logger.warning(f"⚠️ DECREMENTO: {msg}")
                                return {
                                    'sucesso': False,
                                    'mensagem': msg,
                                    'codigo': 'DECREMENTO',
                                    'leitura_anterior': leitura_anterior,
                                    'leitura_atual': agua_float
                                }

                    # VALIDAÇÕES PASSED: Prosseguir com INSERT
                    data_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        INSERT INTO leituras (unidade, leitura_agua, leitura_gas, tipo, data_leitura, sincronizado)
                        VALUES (?, ?, ?, ?, ?, 0)
                    """, (unidade, agua_float, gas, tipo, data_agora))
                    conn.commit()

                    # Log de sucesso
                    print(f"💾 [GRAVANDO] Unidade: {unidade} | Água: {agua_float}m³ | Gás: {gas}m³ | OK")
                    return {
                        'sucesso': True,
                        'mensagem': f'Leitura salva com sucesso',
                        'codigo': 'SUCESSO'
                    }

            except sqlite3.OperationalError as e:
                erro_str = str(e)
                if "database is locked" in erro_str and tentativa < max_retries - 1:
                    logger.warning(f"⚠️ DB LOCKED: Tentativa {tentativa + 1}/{max_retries}. Aguardando {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"❌ ERRO DB: {e}")
                    return {
                        'sucesso': False,
                        'mensagem': f'Erro no banco de dados: {e}',
                        'codigo': 'ERRO_DB'
                    }

            except Exception as e:
                logger.error(f"❌ ERRO GERAL: {e}")
                return {
                    'sucesso': False,
                    'mensagem': f'Erro ao salvar: {e}',
                    'codigo': 'ERRO_GERAL'
                }

        # Esgotou tentativas de retry
        return {
            'sucesso': False,
            'mensagem': 'Banco de dados bloqueado após múltiplas tentativas',
            'codigo': 'DB_LOCKED'
        }

    @classmethod
    def get_dados_para_relatorio(cls):
        """
        Recupera os dados para o Menu Relatórios.
        Usa GROUP BY para garantir que o total de unidades lidas 
        não conte duplicatas (resolvendo o erro das 153 unidades).
        """
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT unidade, leitura_agua, leitura_gas, data_leitura 
                    FROM leituras 
                    GROUP BY unidade 
                    ORDER BY id DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ [ERRO RELATÓRIO] {e}")
            return []

    @classmethod
    def get_historico_unidade(cls, unidade):
        """Recupera as últimas 6 leituras para os gráficos do Dashboard."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT data_leitura, leitura_agua 
                    FROM leituras 
                    WHERE unidade = ? 
                    ORDER BY data_leitura DESC LIMIT 6
                """, (unidade,))
                rows = cursor.fetchall()
                historico = []
                for row in reversed(rows):
                    dt = datetime.strptime(row['data_leitura'], "%Y-%m-%d %H:%M:%S")
                    historico.append({"mes": dt.strftime("%d/%m"), "valor": row['leitura_agua']})
                return historico if historico else [{"mes": "Vazio", "valor": 0}]
        except:
            return [{"mes": "Erro", "valor": 0}]

    @classmethod
    def buscar_ultima_unidade_lida(cls):
        """Auxilia a interface a sugerir a próxima unidade na sequência."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT unidade FROM leituras ORDER BY id DESC LIMIT 1")
                res = cursor.fetchone()
                return res['unidade'] if res else None
        except:
            return None

    @classmethod
    def get_medidores(cls, filtro="AMBOS"):
        """Retorna medidores formatados para o gerador de QR Codes."""
        try:
            unidades = cls._gerar_lista_unidades()
            return [{"unidade_id": u, "id_qrcode": f"QR_{u}", "tipo": filtro} for u in unidades]
        except Exception as e:
            print(f"❌ [ERRO QR] {e}")
            return []

    @classmethod
    def get_leituras_mes_atual(cls):
        """
        Recupera todas as leituras do mês atual.
        Retorna lista de dicionários com unidade, leitura_agua, leitura_gas e data_leitura.
        """
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                mes_atual = datetime.now().strftime("%Y-%m")
                cursor.execute("""
                    SELECT unidade, leitura_agua, leitura_gas, data_leitura
                    FROM leituras
                    WHERE data_leitura LIKE ?
                    ORDER BY data_leitura DESC
                """, (f"{mes_atual}%",))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ [ERRO] Falha ao buscar leituras do mês: {e}")
            return []

    @classmethod
    def verificar_leitura_duplicada(cls, unidade, data=None):
        """
        Verifica se já existe leitura para a unidade na data especificada.

        Args:
            unidade: Número da unidade
            data: Data no formato YYYY-MM-DD (padrão: hoje)

        Returns:
            dict: {'duplicada': bool, 'leitura': dict ou None}
        """
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                data_busca = data or date.now().strftime("%Y-%m-%d")

                cursor.execute("""
                    SELECT id, unidade, leitura_agua, leitura_gas, data_leitura
                    FROM leituras
                    WHERE unidade = ? AND DATE(data_leitura) = ?
                    ORDER BY data_leitura DESC LIMIT 1
                """, (unidade, data_busca))

                resultado = cursor.fetchone()

                if resultado:
                    return {
                        'duplicada': True,
                        'leitura': dict(resultado)
                    }
                return {'duplicada': False, 'leitura': None}
        except Exception as e:
            logger.error(f"Erro ao verificar duplicada: {e}")
            return {'duplicada': False, 'leitura': None}

    @classmethod
    def validar_leitura_decremento(cls, unidade, nova_leitura):
        """
        Valida se a nova leitura não é menor que a última registrada.

        Args:
            unidade: Número da unidade
            nova_leitura: Valor da nova leitura (float ou string)

        Returns:
            dict: {'valid': bool, 'erro': str ou None, 'leitura_anterior': float ou None}
        """
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()

                # Converte para float
                try:
                    nova_leitura_float = float(str(nova_leitura).replace(',', '.'))
                except ValueError:
                    return {
                        'valid': False,
                        'erro': 'Valor de leitura inválido',
                        'leitura_anterior': None
                    }

                cursor.execute("""
                    SELECT leitura_agua FROM leituras
                    WHERE unidade = ?
                    ORDER BY data_leitura DESC LIMIT 1
                """, (unidade,))

                resultado = cursor.fetchone()

                if resultado:
                    leitura_anterior = resultado['leitura_agua']

                    if nova_leitura_float < leitura_anterior:
                        return {
                            'valid': False,
                            'erro': f'Leitura {nova_leitura_float}m³ é menor que anterior ({leitura_anterior}m³)',
                            'leitura_anterior': leitura_anterior
                        }

                return {
                    'valid': True,
                    'erro': None,
                    'leitura_anterior': None
                }

        except Exception as e:
            logger.error(f"Erro ao validar decremento: {e}")
            return {
                'valid': False,
                'erro': str(e),
                'leitura_anterior': None
            }
    @classmethod
    def registrar_sync_log(cls, unidade, status, erro=None):
        try:
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sync_log (unidade, status, erro, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (unidade, status, erro, agora))
                conn.commit()
        except Exception as e:
            logger.error(f"Falha ao registrar log de sync: {e}")

    @classmethod
    def get_historico_completo_unidade(cls, unidade, limite=12):
        """
        Recupera histórico completo para auditoria.

        Args:
            unidade: Número da unidade
            limite: Quantidade máxima de registros (padrão: 12 meses)

        Returns:
            list: Lista de leituras ordenadas por data
        """
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, unidade, leitura_agua, leitura_gas, tipo, data_leitura, sincronizado
                    FROM leituras
                    WHERE unidade = ?
                    ORDER BY data_leitura DESC LIMIT ?
                """, (unidade, limite))

                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            return []