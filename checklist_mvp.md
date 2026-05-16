# Checklist MVP — AguaFlow v1.2.0

Análise completa do sistema realizada em 16/05/2026.
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
- [ ] Recuperação de senha (não implementada)
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
- [ ] Edição de leitura já registrada
- [ ] Cancelamento de leitura em lote

---

## 4. Scanner / OCR (`views/scanner_view.py`, `utils/ocr_service.py`)

- [x] Captura de imagem do medidor
- [x] OCR automático com Claude Haiku Vision
- [x] Fallback para Tesseract quando API indisponível
- [x] Exibição do resultado para confirmação manual
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
- [x] Contagem de registros pendentes vs sincronizados
- [x] Backup automático após sincronização bem-sucedida
- [x] SnackBar de feedback (sucesso / já atualizado / erro)
- [x] Ícone `ft.Icons.CLOUD_UPLOAD` (sem banner vermelho)
- [x] Cores de estado em hex (azul, verde, cinza, vermelho)
- [x] `SincronizadorUI` reutilizável em outras views
- [ ] Sincronização automática em background (periódica)
- [ ] Log detalhado de sincronizações com timestamps

---

## 7. Relatórios (`views/relatorios.py`)

- [x] Geração de relatório mensal em PDF
- [x] Envio de relatório por e-mail (SMTP Gmail)
- [x] Filtro por período e tipo (Água / Gás)
- [x] Acesso restrito a administradores
- [ ] Relatório por unidade individual
- [ ] Exportação em CSV/Excel

---

## 8. Histórico (`views/historico.py`)

- [x] Listagem de leituras com data, unidade e valor
- [x] Filtro por unidade e período
- [x] Indicador visual de sincronização
- [ ] Busca por texto livre
- [ ] Exclusão de leitura com confirmação

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
- [x] Typo `unidad` corrigido para `unidade` (linhas 27 e 33)
- [x] URL aberta via `ft.UrlLauncher().launch_url()` (não async)
- [x] Contato padrão via variável de ambiente `WHATSAPP_CONTATO`
- [ ] Integração com API oficial do WhatsApp Business
- [ ] Agendamento de alertas (não apenas on-demand)

---

## 15. Backup (`utils/backup.py`)

- [x] Geração de arquivo ZIP com banco SQLite
- [x] Backup automático pós-sincronização
- [x] Localização configurável via `.env`
- [ ] Restauração de backup pela interface
- [ ] Retenção automática (ex: manter últimos N backups)

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

---

## 17. Infraestrutura

- [x] SQLite local com tabelas: `usuarios`, `unidades`, `medidores`, `leituras`
- [x] Supabase como backend remoto (PostgreSQL + Auth)
- [x] `.env` para credenciais (não hardcoded)
- [x] `sync_service.py` — fila de sincronização offline-first
- [x] `database.py` — context manager `get_db()` com commit/rollback automático
- [x] `supabase_client.py` — abstrações de CRUD e deleção de usuário
- [x] `AppUpdater` — versão centralizada em `version.py`
- [ ] Migrations de banco (schema versionado)
- [ ] Testes automatizados (unitários / integração)
- [ ] CI/CD pipeline

---

## Pendências Prioritárias para v1.3.0

| # | Item | Prioridade | Complexidade |
|---|------|-----------|-------------|
| 1 | Sincronização automática em background | Alta | Média |
| 2 | Recuperação de senha | Alta | Baixa |
| 3 | Testes automatizados (pytest) | Alta | Alta |
| 4 | Restauração de backup pela UI | Média | Média |
| 5 | Relatório por unidade individual | Média | Baixa |
| 6 | Exportação CSV/Excel | Média | Baixa |
| 7 | Edição de leitura registrada | Média | Média |
| 8 | Migrations de banco versionadas | Alta | Média |
| 9 | CI/CD (GitHub Actions) | Baixa | Alta |
| 10 | Tema claro/escuro | Baixa | Baixa |

---

*Gerado automaticamente pela análise do código-fonte em 16/05/2026.*
