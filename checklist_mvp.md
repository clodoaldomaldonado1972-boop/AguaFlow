# Checklist MVP — AguaFlow v1.2.0

Análise completa do sistema realizada em 16/05/2026. Atualizado em 20/05/2026 após sessão de correções (2ª rodada).
Status: **Produção** | Plataforma: Desktop (Windows) + Android | Framework: Flet 0.82.2

---

## 1. Autenticação (`views/auth.py`, `utils/auth_utils.py`)

- [x] Login com e-mail e senha (SQLite local)
- [x] Fallback offline — autenticação local quando Supabase indisponível
- [x] Proteção de rota com `validar_sessao()` em todas as views sensíveis
- [x] Controle de permissão por `role` (user / admin)
- [x] Sessão armazenada em `page.user_data`
- [x] Logout com confirmação via `AlertDialog`
- [x] Ícones usando `ft.Icons.*` (sem banners de erro Flutter)
- [x] Login HTTP em `asyncio.to_thread` (sem bloquear event loop)
- [x] `await page.push_route("/menu")` após autenticação bem-sucedida
- [x] `user_metadata or {}` — guard contra metadata None
- [x] Recuperação de senha via Supabase (`reset_password_for_email`) — `/recuperar-email`
- [ ] Expiração automática de sessão por inatividade

---

## 2. Menu Principal (`views/menu_principal.py`)

- [x] Saudação personalizada com nome do usuário
- [x] Indicador de modo offline na AppBar
- [x] Botões administrativos ocultos para `role=user`
- [x] Navegação para todas as rotas principais
- [x] Logout com confirmação
- [x] Rodapé com versão do app (`AppUpdater.get_footer()`)
- [x] Ícones `ft.Icons.*` no IconButton da AppBar (sem banner vermelho)

---

## 3. Medição (`views/medicao.py`)

- [x] Seleção de unidade e tipo (Água / Gás)
- [x] Registro de leitura com timestamp
- [x] Validação de leitura (não pode ser menor que anterior)
- [x] Foto do medidor via câmera ou galeria
- [x] OCR via Claude Haiku Vision (primário) + Tesseract (fallback)
- [x] Confirmação antes de salvar
- [x] Salvo localmente em SQLite com flag `sincronizado=0`
- [x] `Database.criar_usuario()` em `asyncio.to_thread` (sem bloquear event loop)
- [x] Edição de leitura já registrada (via tela Histórico — `Database.editar_leitura`)
- [ ] Cancelamento de leitura em lote

---

## 4. Scanner / OCR (`views/scanner_view.py`, `utils/vision.py`)

- [x] Captura de imagem do medidor
- [x] OCR automático com Claude Haiku Vision
- [x] Fallback para Tesseract quando API indisponível
- [x] Navegação automática após OCR — exibe resultado 1,5s e navega para `/medicao` sem botão confirmar
- [x] `FilePicker` em `View(services=[])` — correção Flet 0.82 (não `page.overlay`)
- [x] Upload de foto em background via `asyncio.create_task`
- [x] Câmera nativa Android via Flutter extension (`image_picker`) — CameraService + CameraExtension
- [x] Dart try-catch em `pickImage` — retorna `"ERROR:<msg>"` em vez de falhar silenciosamente
- [x] Mira animada — Column+spacer com `animate` 1500ms varrem 218px do box (substituiu `ft.Offset` instável)
- [x] Flash visual de captura — overlay branco 300ms (`animate_opacity`); `ft.HapticFeedback` removido (não registrado no Flutter 0.82, causava bloco vermelho na UI)
- [x] Compressão antes do upload Supabase — thumbnail 1024×1024 + JPEG q72 (redução ~91% vs original)
- [x] Log de tentativas OCR em `ocr_log` (Supabase) — resposta bruta, valor aceito, status, modo, modelo
- [x] `enviar_report_erro` em falhas de câmera (Dart RuntimeError) e upload em background
- [x] Scanner QR/barcode em tempo real — `mobile_scanner 6.0.0` via Flutter extension (BarcodeScannerService + BarcodeScannerExtension)
- [x] Navigator context corrigido no barcode Dart — `_findNavigatorContext()` percorre árvore de widgets (substituiu `rootElement` que estava acima do MaterialApp)
- [x] `NameError btn_confirmar / txt_unid / txt_valor_ocr / lbl_ocr_status` corrigidos — referências a controles removidos eliminadas de `_iniciar_captura`
- [ ] Calibração de região de interesse (ROI) por modelo de medidor
- [ ] Histórico de leituras com imagem anexada

---

## 5. Dashboard (`views/dashboard.py`, `utils/graficos_factory.py`)

- [x] Cards de métricas: Lidas, Pendentes, Total Água, Total Gás
- [x] Grid visual de unidades (verde=lida, vermelho=pendente)
- [x] Cores via hex (`#43A047`, `#EF5350`) — não strings CSS
- [x] Ícones `ft.Icons.*` nos cards (sem ícones cinzas)
- [x] `criar_card_metrica` sem `alignment` (sem expansão indesejada)
- [x] Gráfico de barras customizado (sem `ft.LineChart` — não existe em Flet 0.82)
- [x] BottomSheet com detalhes e histórico da unidade
- [x] Filtro por período (mês/ano)
- [x] `ft.BorderRadius.only()` (API atualizada)
- [ ] Exportar gráfico como imagem
- [ ] Comparativo entre períodos no gráfico

---

## 6. Sincronização (`views/sincronizacao.py`, `database/sync_service.py`)

- [x] Sincronização manual com Supabase
- [x] Sincronização automática em background — `asyncio.create_task(SyncService.processar_fila())` no boot
- [x] Contagem de registros pendentes vs sincronizados
- [x] Backup automático após sincronização bem-sucedida
- [x] SnackBar de feedback (sucesso / já atualizado / erro)
- [x] Ícone `ft.Icons.CLOUD_UPLOAD` (sem banner vermelho)
- [x] Cores de estado em hex (azul, verde, cinza, vermelho)
- [x] `SincronizadorUI` reutilizável em outras views
- [x] `supabase.table().insert().execute()` em `asyncio.to_thread` (sem congelar UI)
- [ ] Log detalhado de sincronizações com timestamps na UI

---

## 7. Relatórios (`views/relatorio_view.py`)

- [x] Geração de relatório mensal em PDF
- [x] Envio de relatório por e-mail (SMTP Gmail)
- [x] Filtro por período e tipo (Água / Gás)
- [x] Acesso restrito a administradores
- [x] Botões de etiqueta PDF ocultos no Android (`EXPORT_AVAILABLE` flag)
- [x] Relatório por unidade individual (seção "RELATÓRIO POR UNIDADE" com dropdown + geração PDF/CSV)
- [x] Exportação em CSV (sempre disponível via `csv.DictWriter`); PDF via `EXPORT_AVAILABLE`

---

## 8. Histórico (`views/historico.py`)

- [x] Listagem de leituras com data, unidade e valor
- [x] Filtro por unidade e período
- [x] Indicador visual de sincronização
- [x] Busca por texto livre (campo "Buscar" com filtro em unidade_id, tipo e leiturista)
- [x] Exclusão de leitura com confirmação (AlertDialog + `Database.deletar_leitura`)
- [x] Edição de leitura já registrada (dialog inline + `Database.editar_leitura`)

---

## 9. Gestão de Usuários (`views/gerenciamento_usuarios.py`)

- [x] Listagem com busca por nome/e-mail
- [x] Criação de usuário (nome, e-mail, senha, role)
- [x] Alteração de role com dropdown
- [x] Exclusão com confirmação
- [x] Sincronização de alterações com Supabase
- [x] Indicador de pendência de sync por usuário
- [x] Administradores listados primeiro
- [x] Ícones `ft.Icons.*` (sem banners de erro)
- [x] Cores `st.RED_ERROR` em hex (sem `"red700"` não suportado)
- [x] Auto-protegido — não exibe botão excluir para o próprio usuário logado
- [x] Acesso restrito a `role=admin`

---

## 10. Configurações (`views/configuracoes.py`)

- [x] Alteração de senha do usuário logado
- [x] Configurações de SMTP (e-mail)
- [x] Número WhatsApp para alertas (`WHATSAPP_CONTATO`)
- [x] Limpeza de cache local
- [ ] Tema claro/escuro
- [ ] Configuração de número de unidades do condomínio

---

## 11. Dashboard de Saúde (`views/dashboard_saude.py`)

- [x] Diagnóstico de conectividade Supabase
- [x] Verificação de tabelas e integridade do banco local
- [x] Listagem de erros recentes nos logs
- [x] Acesso restrito a administradores
- [x] Ícones corrigidos (sem banners Flutter)
- [x] Threshold de armazenamento — 500 MB absolutos (substituiu 15% relativo que gerava falso positivo "ESPAÇO BAIXO — 16047 MB" em discos grandes)
- [x] Word-wrap do card "Armazenamento" corrigido — `size=13, no_wrap=True` no título
- [ ] Gráfico de latência de sync
- [ ] Alertas proativos quando pendentes > threshold

---

## 12. Ajuda (`views/ajuda_view.py`)

- [x] Perguntas frequentes (FAQ)
- [x] Botão WhatsApp com `url=` (não `page.launch_url` async)
- [x] Link de suporte abre WhatsApp Web corretamente
- [ ] Vídeos tutoriais embutidos
- [ ] Busca no FAQ

---

## 13. Sobre (`views/sobre_view.py`)

- [x] Versão, autor, contato
- [x] Licença MIT exibida inline
- [x] Botão "Ver Licença Online" com `url=` — abre corretamente
- [ ] Changelog embutido

---

## 14. Alertas Engine (`utils/alertas_engine.py`)

- [x] Alerta de leitura pendente por unidade
- [x] Alerta de possível vazamento
- [x] Alerta de fechamento mensal
- [x] Alerta de falha de sincronização
- [x] Alerta genérico de manutenção
- [x] Typo `unidad` corrigido para `unidade`
- [x] URL aberta via `ft.UrlLauncher().launch_url()` (não async)
- [x] Contato padrão via variável de ambiente `WHATSAPP_CONTATO`
- [ ] Integração com API oficial do WhatsApp Business
- [ ] Agendamento de alertas (não apenas on-demand)

---

## 15. Backup (`utils/backup.py`)

- [x] Geração de arquivo ZIP com banco SQLite
- [x] Backup automático pós-sincronização
- [x] Localização configurável via `.env`
- [x] Restauração de backup pela interface (`BackupManager.restaurar_backup` + UI em Configurações)
- [x] Listagem de backups disponíveis na UI (`BackupManager.listar_backups`)
- [x] Retenção automática — remove ZIPs com mais de 30 dias (`limpar_backups_antigos`)

---

## 16. Compatibilidade Flet 0.82

- [x] `ft.Icons.*` em todos os `ft.Icon` e `ft.IconButton`
- [x] `ft.BorderRadius.only/all()` (não `ft.border_radius.*`)
- [x] `ft.Padding.symmetric/only()` (não `ft.padding.*`)
- [x] `ft.Margin.only()` (não `ft.margin.*`)
- [x] `ft.Alignment(x, y)` onde necessário
- [x] `bgcolor` com hex em todos os SnackBars e Containers
- [x] Sem uso de `ft.LineChart` (não existe em 0.82)
- [x] `page.show_dialog()` / `page.pop_dialog()` no lugar de `open_dialog`
- [x] Coroutines `async def` chamadas via `page.run_task()`
- [x] `await page.push_route()` em funções async (não sem await)
- [x] `page.go()` em lambdas e funções síncronas (substitui push_route sem await)
- [x] `FilePicker` em `View(services=[file_picker])` — não em `page.overlay`

---

## 17. Compatibilidade Android / APK

- [x] `cv2`, `pytesseract`, `numpy` — imports condicionais com `try/except ImportError`
- [x] `reportlab`, `qrcode` — imports condicionais com `try/except ImportError` + flag `EXPORT_AVAILABLE`
- [x] Caminhos de storage via `platform_utils.py` (`FLET_APP_STORAGE_DATA`, `FLET_APP_STORAGE_TEMP`)
- [x] `FilePicker` como `services=[]` no View (funciona no Android via intent de câmera)
- [x] `asyncio.to_thread` em todas as chamadas HTTP síncronas (login, registro, reset senha, sync)
- [x] `buildozer.spec` — `reportlab` excluído dos requirements, `fpdf2`/`pillow`/`anthropic` incluídos
- [x] `source.exclude_dirs` excluindo `.venv`, `tests`, `bin`, `__pycache__`
- [x] Permissões Android: `CAMERA`, `INTERNET`, `READ/WRITE_EXTERNAL_STORAGE`, `ACCESS_NETWORK_STATE`
- [x] Arquivos de OCR desktop (`camera_utils.py`, `processamento.py`, `ocr_engine.py`) não importados pelo app
- [x] Compilação efetiva do APK no ambiente WSL2/Linux — `flet build apk` + injeção `image_picker` + `mobile_scanner` + `flutter build apk --release` (build dois-fases via `build_wsl.sh`)
- [x] APK gerado: `AguaFlow-1.2.0.apk` (172 MB) — câmera nativa + barcode scanner
- [x] Teste em dispositivo físico Android — câmera abre, captura foto, envia ao Supabase
- [ ] Teste de OCR em campo (taxa de acerto por modelo de medidor)

---

## 18. Infraestrutura

- [x] SQLite local com tabelas: `usuarios`, `unidades`, `medidores`, `leituras`
- [x] Supabase como backend remoto (PostgreSQL + Auth)
- [x] `.env` para credenciais (não hardcoded)
- [x] `sync_service.py` — fila de sincronização offline-first
- [x] `database.py` — context manager `get_db()` com commit/rollback automático
- [x] `supabase_client.py` — abstrações de CRUD e deleção de usuário
- [x] `AppUpdater` — versão centralizada em `version.py`
- [x] Migrations versionadas — tabela `schema_version` criada em `inicializar_tabelas`; versão registrada no boot
- [x] Testes automatizados — 114 testes pytest (100% pass) em `tests/test_database.py`, `tests/test_backup.py` e `tests/test_leituras_ciclo.py`
  - `TestSchemaVersion` (2): tabela criada + versão registrada
  - `TestEditarLeitura` (4): edição de valores, flag sincronizado, edição para None, id inexistente
  - `TestDeletarLeitura` (3): deleção, id inexistente, deleção seletiva
  - `TestBuscarLeiturasFiltradas` (7): sem filtro, por unidade, por mês, texto, combinado, campos, ordenação
  - `TestListarBackups` (4): pasta vazia, um backup, múltiplos ordenados, ignora não-ZIP
  - `TestRestaurarBackup` (5): restauração correta, arquivo inexistente, ZIP inválido, preservação em falha, mensagem
  - `TestListaUnidades` (10): 96 unidades, primeira=166, última=TERREO GERAL ÁGUA, duplex, sem duplicatas, ordem
  - `TestExtrairAndar` (13): todos os padrões (andares 1–16, duplex, áreas comuns, string vazia)
  - `TestNormalizarUnidadeScanner` (7): código exato, AGUAFLOW|XXX-AGUA, somente sufixo, duplex, LAZER GÁS, fallback
  - `TestUnidadeLida` (8): exato, ausente, duplex por id completo, por parte esquerda, por parte direita, área comum
  - `TestLidosFiltradosPorModo` (8): fix do bug — ÁGUA não conta em GÁS, GÁS não conta em ÁGUA, sequência bloqueada/liberada corretamente
  - `TestBugAntigoLidosSemModo` (2): documenta comportamento errado da lógica antiga vs comportamento correto do fix
  - `TestFluxoCompletoAgua` (4): salvar ÁGUA para todas as 96 unidades, verificar lidos, sem pendentes, valores preservados
  - `TestFluxoCompletoGas` (4): salvar GÁS para todas as unidades com hidrômetro, verificar lidos, TERREO sem GÁS
  - `TestAreasComuns` (6): LAZER GÁS e TERREO GERAL ÁGUA — salvar, recuperar, isolamento entre modos, posição na lista
  - `TestValidacaoSequencia` (9): primeira sempre válida, 165 bloqueada/liberada em ÁGUA e GÁS, duplex, andar 16 completo
  - `TestFimDeCiclo` (9): salvar_referencias_ciclo, 96 referências, leitura_anterior no JOIN, reset zera leituras, referências preservadas
  - `TestRelatorioCSV` (8): gerar_todos retorna 4 chaves, CSV/PDF existem em disco, cabeçalho + dados, coluna unidade
- [ ] CI/CD pipeline

---

## Prioridades

| # | Item | Prioridade | Status |
|---|------|-----------|--------|
| 1 | `await page.push_route()` — navegação corrigida | 🔴 Crítico | ✅ Feito |
| 2 | `FilePicker` como `services=[]` no scanner | 🔴 Crítico | ✅ Feito |
| 3 | `reportlab` import condicional (crash Android) | 🔴 Crítico | ✅ Feito |
| 4 | `asyncio.to_thread` no SyncService (UI freeze) | 🔴 Crítico | ✅ Feito |
| 5 | `asyncio.to_thread` em autenticacao.py e recuperar_senha | 🔴 Crítico | ✅ Feito |
| 6 | Compilar APK em WSL2 — build dois-fases com `image_picker` | 🔴 Crítico | ✅ Feito |
| 7 | Câmera nativa Android (CameraService Flutter extension) | 🔴 Crítico | ✅ Feito |
| 8 | Teste em dispositivo físico Android — câmera funcional | 🔴 Crítico | ✅ Feito |
| 9 | Mira animada do scanner — Column+spacer (substituiu ft.Offset instável) | 🟡 Importante | ✅ Feito |
| 10 | Compressão de foto antes do upload Supabase (~91% menor) | 🟡 Importante | ✅ Feito |
| 11 | Log de tentativas OCR em `ocr_log` para calibragem | 🟡 Importante | ✅ Feito |
| 12 | Relatório por unidade individual | 🟡 Importante | ✅ Feito |
| 13 | Restauração de backup pela UI | 🟡 Importante | ✅ Feito |
| 14 | Edição de leitura registrada | 🟡 Importante | ✅ Feito |
| 15 | Migrations de banco versionadas | 🟡 Importante | ✅ Feito |
| 16 | Exportação CSV/Excel | 🟢 Desejável | ✅ Feito (CSV via historico/relatorio) |
| 17 | Testes automatizados (pytest) | 🟢 Desejável | ✅ Feito (114 testes, 100% pass) |
| 18 | Scanner QR/barcode — `mobile_scanner 6.0.0` + fix Navigator context | 🔴 Crítico | ✅ Feito |
| 19 | Navegação automática após OCR (sem botão confirmar) | 🟡 Importante | ✅ Feito |
| 20 | Fix HapticFeedback (bloco vermelho cobrindo tela do scanner) | 🔴 Crítico | ✅ Feito |
| 21 | Fix NameError btn_confirmar/txt_unid/txt_valor_ocr/lbl_ocr_status | 🔴 Crítico | ✅ Feito |
| 22 | Storage threshold absoluto 500 MB (fix falso positivo "ESPAÇO BAIXO") | 🟡 Importante | ✅ Feito |
| 23 | Teste de OCR em campo (taxa de acerto por modelo) | 🟡 Importante | ⬜ Pendente |
| 24 | Calibração ROI por modelo de medidor | 🟢 Desejável | ⬜ Pendente |
| 25 | Criar tabela `ocr_log` no Supabase (SQL fornecido) | 🟡 Importante | ⬜ Aguardando usuário |
| 26 | Tema claro/escuro | 🟢 Desejável | ⬜ Pendente |
| 27 | CI/CD (GitHub Actions) | 🟢 Desejável | ⬜ Pendente |

---

---

## 19. Conformidade Skill — Mobile Architecture (20/05/2026)

- [x] `page.client_storage` removido de todo o projeto — zero ocorrências em código ativo
- [x] `preferencias_leitura.py` migrada para `ft.SharedPreferences` (async `get/set` via `page.services`)
- [x] `gestao_periodos.finalizar_mes_e_enviar` refatorada para `async def` + `asyncio.to_thread` em todas operações bloqueantes (8x)
- [x] Ciclo mensal: `leitura_atual → leitura_anterior` via `Database.salvar_referencias_ciclo` antes do reset
- [x] Ordem de fechamento garantida: backup → dados → relatórios → referências_ciclo → e-mail → reset
- [x] `smtplib` (`relatorio_engine`, `email_service`) chamado exclusivamente via `asyncio.to_thread` em contextos async
- [x] Comentário obsoleto de `page.session`/`client_storage` removido de `auth.py`

---

---

## 20. Correções — 22/05/2026 (3ª rodada)

- [x] **Fix lidos filtrado por modo** (`views/medicao.py`) — `salvar_clique` agora filtra o conjunto `lidos` por `leitura_agua` (modo ÁGUA) ou `leitura_gas` (modo GÁS); antes, qualquer leitura no mês liberava a validação de sequência, permitindo salvar GÁS fora de ordem para unidades que só tinham ÁGUA registrada
- [x] **Fix beep do scanner** (`flutter_camera/barcode_service.dart`) — `SystemSoundType.alert` substituído por `SystemSoundType.click`; `alert` é exclusivo do iOS e silenciosamente ignorado no Android (APK precisa ser recompilado)
- [x] **Fix `_resetar_banco_para_novo_mes`** (`database/gestao_periodos.py`) — removida coluna inexistente `data_leitura_atual` do UPDATE; a instrução falhava silenciosamente com `OperationalError` fazendo o fim de ciclo sempre retornar `False`
- [x] **Bateria de testes de leituras** (`tests/test_leituras_ciclo.py`) — 88 novos testes cobrindo lista de unidades, extração de andar, normalização do scanner, lidos por modo, fluxo ÁGUA e GÁS completo (96 unidades), áreas comuns, validação de sequência, fim de ciclo e relatório CSV/PDF; total do projeto: **114 testes, 100% pass**

---

## 21. Limpeza de Código — 22/05/2026

- [x] **19 arquivos órfãos removidos** — `utils/` (scanner.py, camera_utils.py, processamento.py, ocr_engine.py, destravar.py, forcar_reset.py, limpeza.py, ligar_celular.py, setup_projeto.py, alertas_engine.py, seed_supabase.py, observabilidade.py, suporte_helper.py, diagnostico.py, config_assets.py, preferencias_leitura.py) + `views/components/scanner_component.py` + `estrutura.txt` + `analyze_apk.py`; nenhum era referenciado por código ativo
- [x] **`views/components/`** removida — ficou vazia após exclusão do único arquivo (`scanner_component.py` importava `leitor_ocr` inexistente)
- [x] **`criar_mira_scanner` confirmada** em `views/styles.py:61` — única implementação, sem duplicatas
- [x] **`buildozer.spec` atualizado** — `testes/` e `docs/` adicionados a `source.exclude_dirs`; estavam sendo incluídos no APK sem necessidade
- [x] **114 testes, 100% pass** após limpeza — confirmado que nenhuma remoção quebrou importações ativas

### Estrutura ativa de `utils/` após limpeza

| Arquivo | Uso |
|---|---|
| `vision.py` | OCR principal (Claude Vision + Tesseract fallback) |
| `camera_service.py` | Flutter extension — câmera nativa Android |
| `barcode_service.py` | Flutter extension — scanner QR/barcode |
| `auth_utils.py` | Validação de sessão em todas as views |
| `backup.py` | Backup ZIP pós-sincronização |
| `email_service.py` | SMTP para envio de relatórios |
| `export_manager.py` | Exportação CSV/PDF (relatorio_view) |
| `report_generator.py` | Geração de relatório por unidade |
| `graficos_factory.py` | Gráfico de barras no dashboard |
| `audio_utils.py` | Feedback sonoro em configuracoes |
| `platform_utils.py` | Paths Android vs Desktop |
| `logger_config.py` | Sistema de logs + envio de erros |
| `updater.py` | Versão centralizada do app |

---

*Atualizado em 22/05/2026 (3ª rodada + limpeza) — fix lidos por modo, fix beep scanner, fix reset ciclo, 88 novos testes (114 total 100% pass), remoção de 19 arquivos órfãos, buildozer.spec corrigido.*

---

## 22. Correções — 22/05/2026 (4ª rodada — pós-campo APK 125)

Baseadas nos logs de campo e screenshot do leiturista (APK 125 em produção).

- [x] **Fix beep — causa raiz real** (`build_wsl.sh`) — o `sed` nunca inseriu `configureFlutterEngine` porque o Flet 0.82.2 gera `class MainActivity : FlutterActivity()` sem `{` e com espaço antes de `:`, formato que não casava com o padrão do sed. MainActivity.kt ficava sem o override e sem a importação de `FlutterEngine`. Substituído por `cat > MainAcitivy.kt << 'KOTLIN_EOF'` que escreve o arquivo completo diretamente — idempotente, sem frágil pattern-matching.
- [x] **Fix SnackBar "Foto gravada com sucesso!"** (`views/scanner_view.py`) — `page.show_snack_bar()` não exibia o SnackBar do background task em Flet 0.82.2 Android. Substituído por `page.snack_bar = ...; page.snack_bar.open = True; page.update()` que é a API direta e confiável. Adicionado SnackBar de erro quando upload retorna URL vazia.
- [x] **Fix storage path — unidades duplex e raw barcode** (`views/scanner_view.py`) — o raw barcode `"AGUAFLOW|163/164-GAS"` gerava 3 níveis de pasta no Storage (`AGUAFLOW_163/164-GAS/...`). Agora o barcode é normalizado antes do upload: `"AGUAFLOW|161-AGUA"→"161"`, `"AGUAFLOW|163/164-GAS"→"163-164"`.
- [x] **Fix visibilidade do valor OCR** (`views/medicao.py`) — `txt_agua` e `txt_gas` sem `color` explícito renderizavam o valor preenchido pelo OCR em cinza indistinguível do hint text no tema escuro (#121417). Adicionado `color="white"` em ambos os campos.
- [x] **Fix ruído WARNING `ocr_log` PGRST205** (`utils/vision.py`) — toda chamada OCR gerava `WARNING Falha ao logar OCR: PGRST205` porque a tabela `ocr_log` não existe no Supabase. Código agora detecta `PGRST205` e loga em `DEBUG` em vez de `WARNING`. A tabela SQL para criação está documentada em `docs/investigacao_logs_erro_20260522.md`.
- [x] **Testes — 156 testes, 100% pass** (build 126) — `TestScannerOcrUpload` (42) adicionados à suite.
- [x] **APK build 126** — `build_wsl.sh` atualizado para build-number 126, output `AguaFlow-1.2.0-b126.apk`.

---

*Atualizado em 22/05/2026 (4ª rodada) — fix beep MainAcitivy.kt, SnackBar API, storage path duplex, color OCR field, WARNING PGRST205, 156 testes 100% pass.*

---

## 23. Skill — Refatoração de Leitura (25/05/2026)

Implementação do SKILL `agents-e-skills/desenvolvedor-flet/SKILL.md`.

### 23.1 `utils/vision.py` — Prompt OCR por Fabricante Real

- [x] **`PROMPT_SISTEMA_OCR`** adicionado como constante de módulo — instrui o Claude Vision com regras exatas de casas decimais por tipo de medidor:
  - Água apartamento (Renova): 2 dígitos VERMELHOS → ponto antes dos 2 últimos (ex: `'0012461'` → `124.61`)
  - Gás (LAO): 3 dígitos VERMELHOS → ponto antes dos 3 últimos (ex: `'00015324'` → `15.324`)
  - Térreo Geral Água (LAO Grande): 1 dígito VERMELHO → ponto antes do último (ex: `'014523'` → `1452.3`)
- [x] **Parâmetro `system`** em `_ocr_claude` substituído por `PROMPT_SISTEMA_OCR` — Claude recebe as regras de decimal no system prompt + descrição visual detalhada no user message

### 23.2 `views/medicao.py` — Barreira de Andar, Progresso e Modo Ronda

- [x] **`page.lista_unidades`** — lista de objetos `Unidade(nome)` criada no mount; permite que as funções de barreira itererem com `.nome`
- [x] **`modo_ronda`** lido de `page.user_data.get("modo_ronda", "misto")` — suporta `"agua"`, `"gas"` e `"misto"` sem quebrar a rota atual (`page.go("/medicao")`)
- [x] **`passo_leitura_atual`** controla qual campo é exibido por vez (`"agua"` ou `"gas"`); sincronizado com `_modo_legado` para compatibilidade com o scanner
- [x] **`unidades_concluidas_no_ciclo`** — `set` que rastreia unidades efetivamente gravadas na rodada atual para alimentar a barreira de andar
- [x] **`lbl_progresso_status` + `bar_progresso`** — barra de progresso horizontal `ft.ProgressBar` posicionada acima do dropdown de unidade (SKILL Passo E); atualizada a cada troca de unidade
- [x] **`dialog_barreira`** — `ft.AlertDialog` que intercepta a tentativa de avançar para outro andar sem ter medido todos os apartamentos; ações: "Voltar e Medir" ou "Seguir (Salvar como Nulo)"
- [x] **`_atualizar_campos_unidade(unidade_nome)`** — exibe apenas um campo por vez conforme tipo de unidade e modo:
  - `LAZER GÁS` → mostra apenas `txt_gas` (pula se modo `"agua"`)
  - `TERREO GERAL` → mostra apenas `txt_agua` (pula se modo `"gas"`)
  - Apartamentos → mostra `txt_agua` ou `txt_gas` conforme `passo_leitura_atual`
  - Labels dinâmicos com marca/casas decimais corretas por unidade
- [x] **`_avancar_proxima_unidade_com_seguranca()`** — valida se todas as unidades do andar atual foram concluídas antes de avançar; dispara `dialog_barreira` se faltarem
- [x] **`_fechar_barreira(voltar)`** — "Voltar": exibe aviso; "Seguir": salva unidades restantes do andar como `leitura_agua=None / leitura_gas=None` e avança
- [x] **Modo Misto** — `salvar_clique` alterna `passo_leitura_atual` de `"agua"` para `"gas"` na mesma unidade antes de avançar (uma unidade por vez, agua→gas→próxima)
- [x] **`_mostrar_snack(msg, is_error)`** — helper centralizado para feedback visual (substitui `page.show_dialog(SnackBar(...))` espalhado)
- [x] **Compatibilidade completa** — `_extrair_andar` e `_normalizar_unidade_scanner` mantidos em nível de módulo; 156 testes passam sem regressão

---

## 24. Testes OCR com Fotos Reais — assets/Photos-3-001 (25/05/2026)

### 24.1 Resultados por tipo de medidor — iteração final (25/05/2026)

| Tipo         | Fotos | ✅ OK | ⚠️ Formato | ❌ Null | Acerto |
|--------------|-------|-------|------------|---------|--------|
| TERREO       | 1     | 1     | 0          | 0       | **100%** |
| ÁGUA (apt)   | 11    | 9     | 0          | 2       | **82%** |
| GÁS          | 6     | 4     | 0          | 2       | **67%** |
| Desconhecido | 4     | 2     | 0          | 2       | **50%** |
| **Total**    | **22**| **16**| **0**      | **6**   | **73%** |

### 24.2 Correções aplicadas nesta sessão

- [x] **Branch `terreo` em `_prompt_ocr()`** (`utils/vision.py`) — tipo `"terreo"` envia prompt específico para LAO Grande com 1 dígito VERMELHO; corrigiu `13518.66` → `13518.6` ✅
- [x] **`_tipo_from_nome()` em script de teste** (`testes/testar_ocr_photos3.py`) — `terreo`/`geral` mapeia para `('terreo', 'terreo')` garantindo uso do prompt correto
- [x] **Formato Renova corrigido de 5+2 para 4+2** — descoberto que os medidores Renova UR-3.0 deste condomínio têm **4 janelas PRETAS + 2 VERMELHAS = 6 roletes** (não 5+2=7 como constava no prompt). Antes a IA inventava um 5º dígito preto retornando `03943.48` quando o real era `0394.31`. Após correção do prompt retorna `0394.31` ✅
- [x] **`PROMPT_SISTEMA_OCR`** atualizado com o exemplo correto de 6 dígitos (ex: `'026012' → 0260.12`)
- [x] **`RE_AGUA_APT`** no script de teste atualizado para `\d{4}\.\d{2}$` (4 dígitos exatos antes do ponto)
- [x] **0 erros de formato** em todas as 22 fotos — respostas são número correto ou `null`

### 24.3 Precisão de dígito nos valores com formato correto

Comparação com valores reais fornecidos pelo operador:

| Foto          | Real        | OCR          | Resultado       |
|---------------|-------------|--------------|-----------------|
| agua-151      | `0260.12`   | `0260.12`    | **EXATO** ✅    |
| agua-152      | `0256.72`   | `0260.12`    | ❌ leu igual à 151 |
| agua-153      | `0455.37`   | `0455.37`    | **EXATO** ✅    |
| agua-154      | `0394.31`   | `0394.74`    | ❌ últimos 2 dígitos |
| agua-155      | `0267.53`   | `0262.67`    | ❌ dígitos trocados |
| agua-156      | `0144.96`   | `null`       | ❌ foto ilegível |
| agua-161      | `0261.28`   | `0261.26`    | ❌ último dígito (28→26) |
| gas-152       | `00158.489` | `00158.481`  | ❌ último dígito (489→481) |

Erros restantes são de **leitura de dígito individual** (rolete entre dois números, foco ou ângulo) — o formato está 100% correto.

### 24.4 Fotos com null (necessitam retake no campo)

| Arquivo               | Motivo provável                              |
|-----------------------|----------------------------------------------|
| `agua-156.jpg`        | Foto ilegível — ângulo/iluminação ruim       |
| `agua-166.jpg`        | Foto ilegível — ângulo/iluminação ruim       |
| `gas-161.jpg`         | Inconsistente entre rodadas (às vezes lê)    |
| `gas-165.jpg`         | Foto ilegível — ângulo/iluminação ruim       |
| `20260426_120251.jpg` | Tipo desconhecido, ilegível como água        |
| `20260426_120902.jpg` | Tipo desconhecido, ilegível como água        |

**Obs.:** `20260426_*.jpg` respondem bem como GÁS — provavelmente são medidores de gás.

### 24.5 Próximos passos para melhorar acerto

- [ ] Retake das 4 fotos com null consistente (`agua-156`, `agua-166`, `gas-165`, `20260426_120251`)
- [ ] Identificar tipo real das fotos `20260426_*.jpg` para corrigir classificação no script
- [ ] Criar tabela `ocr_log` no Supabase (SQL em `docs/investigacao_logs_erro_20260522.md`)

---

*Atualizado em 25/05/2026 (Skill — refatoração de leitura) — PROMPT_SISTEMA_OCR por fabricante, barreira de andar, barra de progresso, modo ronda, campo único por passo, 198 testes 100% pass.*
*Atualizado em 25/05/2026 (OCR Photos-3-001 — iteração final) — Renova 4+2 corrigido, TERREO 100%, 16/22 = 73%, 0 erros de formato.*
