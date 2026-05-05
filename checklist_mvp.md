# ✅ Checklist de Prontidão para APK - AguaFlow

## 🚀 Arquitetura e UI
- [x] **Início Seguro**: `bootstrap_seguro` via `run_task` (Adeus tela branca).
- [x] **Rotas Testadas**: Mapeamento completo de `/` até `/relatorios` validado.
- [x] **RAM Management**: `gc.collect()` ativo em todas as trocas de view.
- [x] **Non-Blocking**: Sincronização em background task (Asyncio).

## 💾 Persistência Offline-First
- [x] **Esquema Sync**: Uso de `unidade_id` e `valor_leitura` padrão Supabase.
- [x] **Auto-Cleanup**: `os.remove` de fotos após confirmação de upload.
- [x] **Timezone**: Auditoria via `pytz` (America/Sao_Paulo).

## 📊 Módulo de Saúde (Telemetria)
- [x] **Logs Locais**: Tabela `sync_log` rastreia cada tentativa de envio.
- [x] **Manutenção**: Expiração automática de logs com mais de 30 dias.
- [x] **Auditoria**: Registro detalhado de mensagens de erro do Supabase.

## ☁️ Cloud Sync
- [x] **Conexão Segura**: Cliente Supabase validado com SSL/HTTPS.
- [x] **Mapping 1:1**: JSON de upload coincide com as colunas da tabela de produção.