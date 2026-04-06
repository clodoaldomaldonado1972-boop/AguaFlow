# CHECKLIST_STATUS.md — Faxina Técnica AguaFlow
> Engenheiro de Software Sênior · Revisão Completa · Data: 2026-06

---

## LEGENDA
- `[V]` Concluído e funcional
- `[ ]` Em andamento / parcialmente implementado
- `[!]` Crítico — bloqueia produção ou causa perda de dados

---

## 1. FUNCIONALIDADES PRINCIPAIS (README vs Código)

| # | Funcionalidade | Status | Arquivo | Observação |
|---|---|---|---|---|
| 1.1 | Sequenciamento inteligente (16→térreo) | `[V]` | `database/database.py` | 96 unidades + 2 especiais carregadas |
| 1.2 | Cálculo de consumo (subtração automática) | `[ ]` | `views/utils/gerador_pdf.py` | Cálculo existe no PDF, mas `registrar_leitura()` não recebe `leitura_anterior` |
| 1.3 | Gestão de ciclo / virada de mês | `[ ]` | `database/gestao_periodos.py` | Lógica implementada, **não está conectada a nenhum botão na UI** |
| 1.4 | Alertas sonoros (bipe) | `[V]` | `views/audio_utils.py` | Funcional via `flet_audio` |
| 1.5 | Identificação por QR Code | `[V]` | `views/utils/gerador_qr.py` | Geração de etiquetas OK |
| 1.6 | Relatórios PDF mensais | `[ ]` | `views/utils/gerador_pdf.py` | PDF gerado, mas botão em `relatorios.py` chama `print("Gerando PDF...")` — **não executa o gerador real** |
| 1.7 | Leitura OCR via câmera | `[!]` | `views/leitor_ocr.py` | `ler_qr_code()` e `extrair_dados_fluxo()` são **chamadas mas não definidas** no arquivo — `NameError` em runtime |
| 1.8 | Operação offline-first | `[V]` | `database/database.py` | SQLite local funcional |
| 1.9 | Sincronização com Supabase | `[ ]` | `sync_engine.py` | Funciona para push básico, sem retry, sem pull, sem fila robusta |

---

## 2. SEGURANÇA E CONFIGURAÇÃO

| # | Item | Status | Arquivo | Observação |
|---|---|---|---|---|
| 2.1 | Credenciais Supabase no `.env` | `[V]` | `.env` | Variáveis lidas via `os.environ.get()` |
| 2.2 | `.env` no `.gitignore` | `[V]` | `.gitignore` | Verificado |
| 2.3 | Credenciais de e-mail no `.env` | `[V]` | `.env` | `EMAIL_USER` e `EMAIL_PASS` presentes |
| 2.4 | `EMAIL_DESTINATARIO` ausente no `.env` | `[!]` | `views/utils/email_service.py` L15 | `os.getenv("EMAIL_DESTINATARIO")` retorna `None` — e-mail nunca é enviado sem travar |
| 2.5 | Caminho Tesseract hardcoded | `[!]` | `views/leitor_ocr.py` L5 | `r'C:\Program Files\Tesseract-OCR\tesseract.exe'` — quebra em qualquer outra máquina; deve ir para `.env` |
| 2.6 | Credenciais de login hardcoded | `[!]` | `views/auth.py` L17-18 | `"admin@vivere.com"` / `"ADMIN123"` em texto puro no código — crítico para produção |
| 2.7 | Chave Supabase exposta em log de debug | `[!]` | `database/supabase_client.py` L15-16 | `print(f"DEBUG: URL encontrada: {bool(SUPABASE_URL)}")` — remover antes de produção |

---

## 3. QUALIDADE DE CÓDIGO — IMPORTS E VARIÁVEIS

| # | Item | Status | Arquivo | Observação |
|---|---|---|---|---|
| 3.1 | Import `from supabase import create_client` sem uso direto | `[ ]` | `database/database.py` L6 | `create_client` é usado, mas `Client` não é importado — inconsistência com `supabase_client.py` |
| 3.2 | Import `from . import styles as st` sem uso | `[ ]` | `views/medicao.py` L4 | `st.BTN_MAIN` importado mas não utilizado na função |
| 3.3 | Import `from fpdf2 import FPDF` e `from reportlab...` duplicados | `[ ]` | `views/utils/gerador_qr.py` vs `gerador_pdf.py` | Dois geradores de PDF com bibliotecas diferentes — consolidar |
| 3.4 | Variável `GREY` usada mas não definida em `styles.py` | `[!]` | `views/styles.py` | `campo_estilo()` usa `GREY` na `label_style` — `NameError` ao renderizar qualquer campo de texto |
| 3.5 | `ERROR_COLOR` usada mas não definida em `styles.py` | `[!]` | `views/auth.py` L13 | `st.ERROR_COLOR` — `AttributeError` ao carregar a tela de login |
| 3.6 | `TEXT_TITLE` usada mas não definida em `styles.py` | `[!]` | `views/menu_principal.py` L19 | `st.TEXT_TITLE` — `AttributeError` ao carregar o menu |
| 3.7 | Parâmetros `som_alerta`/`som_sucesso` recebidos e imediatamente sobrescritos | `[ ]` | `views/medicao.py` L10-11 | Parâmetros da assinatura são ignorados; `client_storage.get()` pode retornar `None` |
| 3.8 | Bloco de código fora de função em `main.py` | `[!]` | `main.py` L22-27 | `elif page.route == "/medicao":` está solto fora de qualquer função — `SyntaxError` |
| 3.9 | Docstrings ausentes em funções de view | `[ ]` | `views/relatorios.py`, `views/auth.py` | Funções públicas sem docstring |
| 3.10 | Arquivos de teste espalhados em `views/` | `[ ]` | `views/teste.py`, `views/testar_todos.py`, etc. | 6 arquivos de teste dentro da pasta de views — mover para `tests/` |

---

## 4. BANCO DE DADOS E CONSISTÊNCIA

| # | Item | Status | Arquivo | Observação |
|---|---|---|---|---|
| 4.1 | `get_db()` usa `contextmanager` — conexão sempre fechada | `[V]` | `database/database.py` L26-32 | `finally: conn.close()` garante fechamento |
| 4.2 | `gestao_periodos.py` usa `get_connection()` que não existe | `[!]` | `database/gestao_periodos.py` L40 | `Database.get_connection()` não está definido em `database.py` — `AttributeError` |
| 4.3 | `test_crash_recovery.py` referencia `db.DB_PATH` e `db.Database.get_connection` inexistentes | `[!]` | `tests/test_crash_recovery.py` L31-34 | Testes falham ao executar — estrutura do módulo mudou |
| 4.4 | `sync_service.py` referencia tabela `sync_queue` não criada | `[!]` | `database/sync_service.py` L16 | `SELECT ... FROM sync_queue` — tabela nunca é criada em `init_db()` |
| 4.5 | `sync_service.py` chama `insert_leitura_supabase(payload)` com dict, mas função espera 4 args posicionais | `[!]` | `database/sync_service.py` L42 | Assinatura incompatível — `TypeError` em runtime |
| 4.6 | Sem validação de duplicidade de leitura | `[!]` | `database/database.py` | Nenhuma constraint `UNIQUE` ou verificação impede registrar a mesma unidade duas vezes no mesmo ciclo |
| 4.7 | `backup.py` usa caminho relativo `"aguaflow.db"` | `[ ]` | `database/backup.py` L22 | Deve usar `Database.DB_PATH` para consistência |
| 4.8 | `conn.commit()` dentro do loop de sync sem rollback por item | `[ ]` | `sync_engine.py` L34 | Falha parcial pode deixar registros em estado inconsistente |
| 4.9 | Sem `WAL mode` no SQLite | `[ ]` | `database/database.py` | Sem `PRAGMA journal_mode=WAL` — risco de `database locked` com acesso concorrente (background sync + UI) |

---

## 5. UI/UX — FEEDBACK VISUAL DURANTE SINCRONIZAÇÃO

| # | Item | Status | Arquivo | Observação |
|---|---|---|---|---|
| 5.1 | `SnackBar` após sync manual | `[V]` | `main.py` L68-71 | Exibe resultado após conclusão |
| 5.2 | `SnackBar` no background sync (60s) | `[V]` | `main.py` L43-47 | Exibe apenas se houver envio ou erro |
| 5.3 | `ProgressRing` durante sync de 98 registros | `[!]` | `views/relatorios.py` | **Ausente** — botão "SINCRONIZAR COM NUVEM" não desabilita nem exibe loading; UI congela durante sync síncrono |
| 5.4 | Botão PDF chama `print()` em vez da função real | `[!]` | `main.py` L62 | `gerar_e_enviar_pdf=lambda _: print("Gerando PDF...")` — funcionalidade morta |
| 5.5 | Botão QR chama `print()` em vez da função real | `[!]` | `main.py` L63 | `gerar_qr=lambda _: print("Gerando QR...")` — funcionalidade morta |
| 5.6 | Tela de configurações (`/configuracoes`) não implementada | `[ ]` | `main.py` L55 | Rota registrada no menu mas sem `View` correspondente — navegação quebrada |
| 5.7 | Feedback de erro de câmera ausente | `[ ]` | `views/camera_utils.py` | Se `FilePicker` falhar ou usuário cancelar sem selecionar, nenhum feedback é dado |

---

## 6. OCR E CÂMERA

| # | Item | Status | Arquivo | Observação |
|---|---|---|---|---|
| 6.1 | `ler_qr_code()` não definida em `leitor_ocr.py` | `[!]` | `views/leitor_ocr.py` L17 | Chamada mas não implementada — `NameError` ao processar qualquer foto |
| 6.2 | `extrair_dados_fluxo()` não definida em `leitor_ocr.py` | `[!]` | `views/leitor_ocr.py` L18 | Idem — motor OCR real está ausente |
| 6.3 | `scanner_component.py` chama `extrair_dados_fluxo()` diretamente | `[!]` | `views/components/scanner_component.py` L18 | Mesma função inexistente — componente inutilizável |
| 6.4 | Caminho Tesseract não configurável via `.env` | `[!]` | `views/leitor_ocr.py` L5 | Hardcoded para `C:\Program Files\...` |
| 6.5 | `processar()` em `camera_utils.py` não é corrotina mas é chamada com `run_task` | `[ ]` | `views/camera_utils.py` L14 | `page.run_task(processar)` — `processar` é função síncrona; pode bloquear a UI |

---

## 7. TESTES

| # | Item | Status | Arquivo | Observação |
|---|---|---|---|---|
| 7.1 | `test_sync.py` testa assinatura `registrar_leitura(id_db, valor)` | `[!]` | `tests/test_sync.py` L57 | Assinatura real é `registrar_leitura(unidade, valor, tipo_leitura)` — testes não refletem o código atual |
| 7.2 | `test_crash_recovery.py` não usa `unittest` — não roda com `pytest` | `[ ]` | `tests/test_crash_recovery.py` | Classe manual sem herdar `unittest.TestCase` |
| 7.3 | Sem testes para `gestao_periodos.py` | `[ ]` | — | Virada de mês sem cobertura de teste |
| 7.4 | Sem testes para `gerador_pdf.py` e `email_service.py` | `[ ]` | — | Fluxo de relatório sem cobertura |

---

## RESUMO EXECUTIVO

| Categoria | Concluído `[V]` | Em andamento `[ ]` | Crítico `[!]` |
|---|---|---|---|
| Funcionalidades | 5 | 4 | 1 |
| Segurança | 3 | 0 | 4 |
| Qualidade de Código | 1 | 5 | 4 |
| Banco de Dados | 1 | 3 | 5 |
| UI/UX | 2 | 2 | 3 |
| OCR/Câmera | 0 | 1 | 4 |
| Testes | 0 | 2 | 1 |
| **TOTAL** | **12** | **17** | **22** |

---

## AÇÕES IMEDIATAS (Bloqueadores de Produção)

1. **`[!]` Definir `ler_qr_code()` e `extrair_dados_fluxo()` em `leitor_ocr.py`** — OCR completamente não funcional
2. **`[!]` Corrigir `styles.py`** — adicionar `GREY`, `ERROR_COLOR`, `TEXT_TITLE` — app não abre sem isso
3. **`[!]` Remover bloco solto em `main.py` (L22-27)** — `SyntaxError` impede execução
4. **`[!]` Mover credenciais de login para `.env`** — `admin@vivere.com` / `ADMIN123` hardcoded
5. **`[!]` Mover caminho do Tesseract para `.env`** — `TESSERACT_PATH=C:\Program Files\...`
6. **`[!]` Adicionar `EMAIL_DESTINATARIO` no `.env`** — e-mail nunca chega ao síndico
7. **`[!]` Criar tabela `sync_queue` em `init_db()`** — `sync_service.py` falha silenciosamente
8. **`[!]` Corrigir `Database.get_connection()` ou atualizar `gestao_periodos.py`** — virada de mês quebrada
9. **`[!]` Adicionar `ProgressRing` no botão de sync** — UI congela ao sincronizar 98 registros
10. **`[!]` Conectar botões PDF e QR às funções reais** — substituir `print()` por chamadas reais

---

*Gerado por revisão técnica completa — AguaFlow Grupo 8 · UNIVESPE*
