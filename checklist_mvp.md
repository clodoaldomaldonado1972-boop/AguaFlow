# Checklist MVP AguaFlow

## Especificações Técnicas

### Banco de Dados SQLite
- [ ] Implementar persistência local com SQLite
- [ ] Criar tabelas para leituras de água e gás
- [ ] Configurar índices para otimização de consultas
- [ ] Implementar backup automático do banco local

### Fuso Horário pytz
- [ ] Configurar fuso horário de São Paulo (America/Sao_Paulo)
- [ ] Registrar timestamps usando pytz para consistência
- [ ] Exibir datas/horas no formato local brasileiro
- [ ] Validar conversões de horário em operações críticas

### Sincronização Supabase
- [ ] Configurar cliente Supabase para autenticação
- [x] Implementar upload de leituras pendentes
- [x] Criar teste de upload de leituras simuladas para Supabase
- [ ] Criar tabelas na nuvem para sincronização
- [ ] Implementar resolução de conflitos local ↔ nuvem
- [ ] Adicionar indicadores de status de sincronização

### Interface e Inicialização
- [x] Corrigir inicialização de tela Flet em `CHECKLIST_MVP.py` com `ft.app(target=main)`
- [x] Ajustar botão de navegação de retorno para usar `page.push_route` e `page.run_async`
