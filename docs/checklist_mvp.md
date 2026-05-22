# Checklist de Prontidão para APK - AguaFlow v1.2.0

> Atualizado em: 2026-05-22 — teste integrado 9 fases: ciclo, cobertura, refs, relatórios, backup, e-mail, RAM, offline e sync mockado — tudo ✅.

---

## Arquitetura e UI
- [x] **Boot Sequencial**: Rota inicial `/` dispara o router e carrega a tela de login.
- [x] **Tratamento de Erros**: Bloco `try/except` no `route_change` com feedback visual ao usuário.
- [x] **RAM Management**: `gc.collect()` ativo nas trocas de view e geração de PDFs.
- [x] **Non-Blocking**: Sincronização em background task via `asyncio`.
- [x] **Assets Dir**: Definido como `"assets"` em `ft.run()`.
- [x] **Estabilidade UI**: Uso de strings literais para `alignment` e `icons` (compatível com Flet 0.82).
- [x] **Heartbeat**: Task periódica mantém sessão viva (evita timeout de proxy/firewall).

## Autenticação
- [x] **Login Supabase**: Autenticação via `/auth/v1/token` retornando HTTP 200.
- [x] **Proteção de Rota**: `validar_sessao()` bloqueia acesso sem login em todas as views.
- [x] **Logout com Confirmação**: Diálogo de confirmação antes de limpar `page.user_data`.
- [x] **Recuperação de Senha**: Fluxo por e-mail funcional (`/esqueci_senha`, `/recuperar-email`).
- [x] **Registro de Novo Usuário**: Cadastro via Supabase Auth funcional (corrigido `on_change` → `on_select` no Flet 0.82).

## Persistência Offline-First
- [x] **DB Init**: Tabelas SQLite criadas antes da primeira interação do usuário.
- [x] **Leitura Local**: Leituras salvas no SQLite imediatamente (`database.database: Leitura salva localmente`).
- [x] **Esquema Sync**: Uso de `unidade_id` e `valor_leitura` compatível com Supabase.
- [x] **Auto-Cleanup**: `os.remove` de fotos após confirmação de upload.
- [x] **Timezone**: Auditoria via `pytz` (America/Sao_Paulo).
- [x] **Fila de Sync**: `SyncService.processar_fila()` sincroniza pendentes em background.
- [x] **Sync Manual Offline→Online**: `executar_sincronismo_manual()` envia 190 leituras locais ao Supabase; falha de rede mantém rows em `sincronizado=0` sem perda de dados.
- [x] **DB Path Mobile**: `Database.configurar_db_path(page)` define caminho seguro no sandbox Android (`FLET_APP_STORAGE_DATA`) antes de `inicializar_tabelas()`.

## Ciclo Completo de Leituras (revalidado em 2026-05-22)
- [x] **Registro de Leituras**: 95 ÁGUA + 95 GÁS registradas (todos os andares 1–16, LAZER GÁS, TERREO GERAL ÁGUA).
- [x] **Iniciar Novo Ciclo**: 96 referências de leitura salvas para o próximo ciclo.
- [x] **Geração de PDF**: Relatório PDF gerado via ReportLab sem erros de `NoneType` (corrigido `d.get() or 0`).
- [x] **Backup ZIP**: 6 relatórios incluídos no arquivo ZIP de backup.
- [x] **Envio por E-mail**: `E-mail enviado com sucesso!` — SMTP autenticado e funcional.
- [x] **Sincronização Supabase**: Todas as unidades sincronizadas via HTTP 201 Created em tempo real.
- [x] **Fluxo GÁS andares 1-9**: `_extrair_andar()` corrigido — andares de 2 chars (ex: `"96"`, `"16"`) agora recebem leitura GÁS corretamente.
- [x] **Navegação scanner → medicao**: `on_view_pop` contextualizado — botão voltar Android no scanner retorna para `/medicao` preservando modo GÁS/ÁGUA.
- [x] **Restauração de modo**: condição `if modo_retorno in ("AGUA", "GAS")` independente — modo GÁS nunca mais perdido ao voltar do scanner.
- [x] **LAZER GÁS**: unidade sem hidrômetro ÁGUA; leitura GÁS feita manualmente pelo leiturista (sem diálogo automático — por design).
- [x] **TERREO GERAL ÁGUA**: unidade sem medidor de GÁS; apenas ÁGUA registrada (ignorado no ciclo GÁS).

## Cloud Sync
- [x] **Conexão Segura**: Cliente Supabase validado com SSL/HTTPS (HTTP/2).
- [x] **Mapping 1:1**: JSON de upload compatível com as colunas da tabela `leituras` em produção.
- [x] **Auth Check**: Validação de credenciais via Supabase Auth antes de qualquer operação.
- [x] **Sync Log**: Tabela `sync_log` rastreia cada tentativa de envio ao Supabase.

## Relatórios e Exportacao
- [x] **PDF de Consumo**: Gerado com cabeçalho, tabela e rodapé de data.
- [x] **CSV de Consumo**: Exportado com headers corretos via `csv.DictWriter`.
- [x] **Etiquetas QR (Agua)**: PDF 50 etiquetas/folha com QR codes RGB, separadores horizontais e verticais, filtro de "LAZER GAS".
- [x] **Etiquetas QR (Gas)**: PDF 50 etiquetas/folha, filtro de "TERREO GERAL AGUA", labels com auto-ajuste de fonte.
- [x] **Botoes QR visiveis**: Botões sempre exibidos; SnackBar orienta instalação do `reportlab` se ausente (mobile).
- [x] **Dashboard de Saude**: Telemetria com logs de sync e status do banco.
- [x] **Historico**: Consulta de leituras anteriores e geracao de PDF do historico.

## Modulo de Saude (Telemetria)
- [x] **Logs Locais**: Tabela `sync_log` rastreia cada tentativa de envio.
- [x] **Auditoria SMTP**: Teste de conexao SMTP no boot — logado como INFO.
- [x] **Auditoria Supabase**: Registro detalhado de mensagens de erro do Supabase.
- [x] **Filtragem de ruido HTTP/2**: `hpack`, `httpcore` e `httpx` silenciados para WARNING em `logger_config.py` — elimina centenas de linhas DEBUG por sessao sem valor diagnostico.

## Motor de Visão (OCR)
- [x] **Claude Vision API**: OCR primário via `claude-haiku-4-5-20251001` com payload Base64 otimizado.
- [x] **Compressão Pillow**: Imagem redimensionada (máx 1024×1024, JPEG q=88) antes do envio — reduz banda e RAM no Android.
- [x] **Detecção de Portrait**: Recorte automático da metade inferior da foto em modo retrato (foco no medidor).
- [x] **Prompt por Tipo**: Instruções distintas para hidrômetro de água (7 dígitos) e medidor de gás (8 dígitos, fundo vermelho).
- [x] **Resiliência Offline**: Detecta `APIConnectionError`/`APITimeoutError` e retorna `status="offline"` sem travar a UI.
- [x] **OpenCV removido**: `CV2_AVAILABLE = False` permanente — sem dependência de binário NDK não compilável.
- [x] **Tesseract removido**: `TESSERACT_AVAILABLE = False` permanente — sem binário Windows no APK.

## Caminhos de Storage Cross-Platform (`utils/platform_utils.py`)
- [x] **`get_storage_dir()`**: Android usa `$FLET_APP_STORAGE_DATA`; desktop usa `<raiz>/exports`.
- [x] **`get_relatorios_dir()`**: Android usa `$FLET_APP_STORAGE_DATA/relatorios`; desktop usa `<raiz>/relatorios`.
- [x] **`get_temp_dir()`**: Android usa `$FLET_APP_STORAGE_TEMP`; desktop usa `<raiz>/temp`.
- [x] **`export_manager`**: usa `get_storage_dir("etiquetas")` — sem path hardcoded.
- [x] **`relatorio_engine`**: usa `get_relatorios_dir()` — sem path hardcoded.
- [x] **`scanner_view`**: usa `get_temp_dir()` para salvar fotos temporárias.

## Build e Empacotamento APK
- [x] **`buildozer.spec`**: Criado com API 33, NDK 25b, `arm64-v8a + armeabi-v7a`, permissões `CAMERA, INTERNET, READ/WRITE_EXTERNAL_STORAGE`.
- [x] **`flet.yaml`**: Criado com `version: 1.2.0`, `build_number: 121`, `package_name: br.com.vivereprudente.aguaflow`.
- [x] **Scripts de build WSL**: `build_apk_wsl.sh` e `build_wsl.sh` criados para build em ambiente Linux.
- [x] **APK gerado**: `AguaFlow-1.2.0.apk` compilado com sucesso (excluído do repositório via `.gitignore`).
- [x] **Requirements APK**: `reportlab` excluído do `buildozer.spec`; dependências APK declaradas em linha única.

## Teste Integrado (9 fases — validado em 2026-05-22)
- [x] **Script `testes/test_ciclo_completo.py`**: 9 fases headless, DB SQLite isolado em temp — ✅ CICLO COMPLETO.
- [x] **Fase 1 — Ciclo de leituras**: 191 passos, ÁGUA→GÁS→ÁGUA por andar (andares 1-16), passo manual LAZER GÁS.
- [x] **Fase 2 — Cobertura**: 95/95 ÁGUA (LAZER GÁS excluído), 95/95 GÁS (TERREO GERAL ÁGUA excluído), 0 faltando.
- [x] **Fase 3 — Fim de ciclo**: 96 referências de ciclo gravadas no SQLite — base correta para próximo mês.
- [x] **Fase 4 — Relatórios**: 4/4 arquivos gerados via `RelatorioEngine.gerar_todos()`: PDF água (7 KB), PDF gás (7 KB), CSV água (5 KB), CSV gás (5 KB).
- [x] **Fase 5 — Backup ZIP**: banco + relatórios compactados (20 KB) via `BackupManager.executar_backup_seguranca()`.
- [x] **Fase 6 — Envio de e-mail**: 4 anexos entregues via SMTP/Gmail para clodoaldomaldonado112@gmail.com.
- [x] **Fase 7 — RAM**: pico tracemalloc = **1,38 MB** (limite 100 MB); gc coletou 208 objetos; delta +8.783 objetos estáveis.
- [x] **Fase 8 — Offline**: 190 rows (95 ÁGUA + 95 GÁS) em `sincronizado=0` com `supabase=None` — modo sem internet confirmado.
- [x] **Fase 9 — Sync mockado**: Sub-A: 190/190 rows marcados `sincronizado=1`, 190 entradas SUCESSO no `sync_log`; Sub-B: falha de rede simulada — 10 rows de 5 unidades mantidos em `sincronizado=0`, retorno `0` confirmado.

## Rastreabilidade e Documentacao
- [x] **STATUS_INTEGRIDADE.md**: Documento de status completo reescrito com a arquitetura atual (v1.2.0).
- [x] **Investigacao do log validada**: sistema saudavel, nenhum ERROR, OCR e uploads funcionais.
- [x] **`.gitignore` limpo**: `docs/*` com exceções apenas para `README.md` e `checklist_mvp.md`; scripts de teste e `testes/` excluídos do repositório.



## Pendencias Conhecidas (nao-bloqueantes)
- [x] **DeprecationWarning resolvido**: `page.go()` substituído por `page.push_route()` em todos os 14 arquivos do projeto.
- [ ] **Encoding UI**: Caracteres especiais (ex: "Condominio", "servico") aparecem com encoding errado no log interno do Flet — nao afeta o usuario final, apenas o log de debug.
- [ ] **Teste APK em dispositivo fisico**: APK gerado mas nao validado em hardware Android real — recomendado antes de distribuicao.
- [ ] **Icone e Splash**: `icon.filename` e `presplash.filename` comentados no `buildozer.spec` — usar assets finais antes da publicacao na Play Store.
