# ✅ Checklist de Prontidão para APK - AguaFlow

## 🚀 Arquitetura e UI
- [x] **Boot Sequencial**: Rota inicial definida como `/splash` para forçar disparo do router.
- [x] **Tratamento de Erros**: Bloco `try/except` no `route_change` com feedback visual.
- [x] **RAM Management**: `gc.collect()` ativo em todas as trocas de view.
- [x] **Non-Blocking**: Sincronização em background task (Asyncio).
- [x] **Assets Dir**: Definido como "assets" em `ft.app`.
- [x] **Estabilidade UI**: Uso de strings literais para `alignment` e `icons`.

## 💾 Persistência Offline-First
- [x] **Esquema Sync**: Uso de `unidade_id` e `valor_leitura` padrão Supabase.
- [x] **Auto-Cleanup**: `os.remove` de fotos após confirmação de upload.
- [x] **Timezone**: Auditoria via `pytz` (America/Sao_Paulo).
- [x] **DB Init**: Tabelas criadas antes da primeira interação do usuário.

## 📊 Módulo de Saúde (Telemetria)
- [x] **Logs Locais**: Tabela `sync_log` rastreia cada tentativa de envio.
- [x] **Auditoria**: Registro detalhado de mensagens de erro do Supabase.

## ☁️ Cloud Sync
- [x] **Conexão Segura**: Cliente Supabase validado com SSL/HTTPS.
- [x] **Mapping 1:1**: JSON de upload coincide com as colunas da tabela de produção.
- [x] **Auth Check**: Validação de credenciais via Supabase Auth.