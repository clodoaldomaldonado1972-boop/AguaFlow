# Checklist MVP — AguaFlow v1.2.0

Análise completa do sistema realizada em 16/05/2026. Atualizado em 16/05/2026 após sessão de correções.
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
- [x] Exibição do resultado para confirmação manual
- [x] `FilePicker` em `View(services=[])` — correção Flet 0.82 (não `page.overlay`)
- [x] Upload de foto em background via `asyncio.create_task`
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
- [ ] Compilação efetiva do APK no ambiente WSL2/Linux com Android NDK 25b
- [ ] Teste do APK em dispositivo físico Android

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
- [ ] Testes automatizados (unitários / integração)
- [ ] CI/CD pipeline

---

## Prioridades antes de compilar o APK

| # | Item | Prioridade | Status |
|---|------|-----------|--------|
| 1 | `await page.push_route()` — navegação corrigida | 🔴 Crítico | ✅ Feito |
| 2 | `FilePicker` como `services=[]` no scanner | 🔴 Crítico | ✅ Feito |
| 3 | `reportlab` import condicional (crash Android) | 🔴 Crítico | ✅ Feito |
| 4 | `asyncio.to_thread` no SyncService (UI freeze) | 🔴 Crítico | ✅ Feito |
| 5 | `asyncio.to_thread` em autenticacao.py e recuperar_senha | 🔴 Crítico | ✅ Feito |
| 6 | Compilar APK em WSL2 + Android NDK 25b | 🔴 Crítico | ⬜ Pendente |
| 7 | Teste em dispositivo físico Android | 🔴 Crítico | ⬜ Pendente |
| 8 | Relatório por unidade individual | 🟡 Importante | ✅ Feito |
| 9 | Restauração de backup pela UI | 🟡 Importante | ✅ Feito |
| 10 | Edição de leitura registrada | 🟡 Importante | ✅ Feito |
| 11 | Migrations de banco versionadas | 🟡 Importante | ✅ Feito |
| 12 | Exportação CSV/Excel | 🟢 Desejável | ✅ Feito (CSV via historico/relatorio) |
| 13 | Testes automatizados (pytest) | 🟢 Desejável | ⬜ Pendente |
| 14 | Tema claro/escuro | 🟢 Desejável | ⬜ Pendente |
| 15 | CI/CD (GitHub Actions) | 🟢 Desejável | ⬜ Pendente |

---

*Atualizado em 17/05/2026 — implementação dos itens essenciais 🟡 Importante.*
