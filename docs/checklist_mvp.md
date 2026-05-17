# Checklist de Prontidão para APK - AguaFlow v1.2.0

> Atualizado em: 2026-05-16 — validado por ciclo completo de leituras com envio de relatório por e-mail.

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

## Ciclo Completo de Leituras (validado em 2026-05-16)
- [x] **Registro de Leituras**: Múltiplas unidades registradas (151–166) sem erros.
- [x] **Iniciar Novo Ciclo**: 96 referências de leitura salvas para o próximo ciclo.
- [x] **Geração de PDF**: Relatório PDF gerado via ReportLab sem erros de `NoneType` (corrigido `d.get() or 0`).
- [x] **Backup ZIP**: 6 relatórios incluídos no arquivo ZIP de backup.
- [x] **Envio por E-mail**: `E-mail enviado com sucesso!` — SMTP autenticado e funcional.
- [x] **Sincronização Supabase**: Todas as unidades sincronizadas via HTTP 201 Created em tempo real.

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
- [x] **Dashboard de Saude**: Telemetria com logs de sync e status do banco.
- [x] **Historico**: Consulta de leituras anteriores e geracao de PDF do historico.

## Modulo de Saude (Telemetria)
- [x] **Logs Locais**: Tabela `sync_log` rastreia cada tentativa de envio.
- [x] **Auditoria SMTP**: Teste de conexao SMTP no boot — logado como INFO.
- [x] **Auditoria Supabase**: Registro detalhado de mensagens de erro do Supabase.

## Pendencias Conhecidas (nao-bloqueantes)
- [x] **DeprecationWarning resolvido**: `page.go()` substituído por `page.push_route()` em todos os 14 arquivos do projeto (auth, menu, medicao, scanner, historico, relatorios, configuracoes, sincronizacao, sobre, autenticacao, gerenciamento_usuarios, recuperar_senha_email, auth_utils, main).
- [ ] **Encoding UI**: Caracteres especiais (ex: "Condominio", "servico") aparecem com encoding errado no log interno do Flet — nao afeta o usuario final, apenas o log de debug.
