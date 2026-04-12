# Checklist Técnico - Entrega UNIVESP

**Projeto:** AguaFlow  
**Data:** 2026-04-12  
**Responsável:** Clodoaldo Maldonado

---

## 1. Conexão Supabase

- [x] Variáveis de ambiente configuradas (.env)
  - [x] `SUPABASE_URL` definida
  - [x] `SUPABASE_KEY` definida
- [x] Teste de conexão realizado (`teste_supabase.py`)
- [x] Autenticação funcional
- [ ] Tables/queries acessíveis (tabela `unidades` precisa de schema)
- [ ] Tratamento de erros implementado
- [ ] Timeout configurado adequadamente

**Status:** [ ] Pendente [x] Em Progresso [ ] Concluído

**Observações:** Conexão estabelecida com sucesso. Tabela `unidades` existe mas requer criação de colunas via SQL. Script `popular_unidades.py` criado para população em massa.

---

## 2. Banco SQLite

- [x] Arquivo de banco criado/localizado corretamente
- [x] Schema inicializado (tabelas criadas)
- [x] Conexão estabelecida sem erros
- [x] CRUDs funcionando (Create, Read, Update, Delete)
- [x] 96 unidades pré-cadastradas (Apto 161 ao 106)
- [x] Script `popular_unidades.py` para população em massa
- [x] Path do banco resolvido corretamente (cross-platform)

**Status:** [ ] Pendente [ ] Em Progresso [x] Concluído

**Observações:** Banco SQLite fully operational com 96 unidades cadastradas.

---

## 3. Interface Flet

- [ ] Aplicação inicia sem erros
- [ ] Todas as views carregam corretamente
  - [x] `dashboard.py` - Exibe 96 unidades (lidas e pendentes)
  - [ ] `dashboard_saude.py`
  - [ ] `configuracoes.py`
  - [x] `relatorio_view.py`
- [ ] Navegação entre telas funcional
- [ ] Componentes UI renderizam corretamente
- [ ] Eventos/interações respondem adequadamente
- [ ] Responsividade testada
- [ ] Ícones carregam sem AttributeError

**Status:** [ ] Pendente [x] Em Progresso [ ] Concluído

**Observações:** Dashboard atualizado para exibir todas as 96 unidades, indicando visualmente quais possuem leitura (verde) e quais estão pendentes (cinza).

---

## 4. Relatórios PDF

- [ ] Engine `utils/relatorio_engine.py` funcional
- [ ] Geração de PDF executa sem erros
- [ ] Layout do relatório formatado corretamente
- [ ] Dados são populados no template
- [ ] Download/salvamento do PDF funciona
- [ ] Caracteres especiais (PT-BR) renderizam
- [ ] Teste de geração realizado

**Status:** [ ] Pendente [ ] Em Progresso [ ] Concluído

**Observações:**

---

## 5. Alertas WhatsApp

- [ ] Engine `utils/alertas_engine.py` configurada
- [ ] Credenciais API WhatsApp definidas
- [ ] Envio de mensagens funcional
- [ ] Template de alerta configurado
- [ ] Tratamento de falhas implementado
- [ ] Rate limiting considerado
- [ ] Teste de envio realizado

**Status:** [ ] Pendente [ ] Em Progresso [ ] Concluído

**Observações:**

---

## 6. Dependências e Ambiente

- [ ] `requirements.txt` atualizado
- [x] Ambiente virtual configurado
- [x] Versões críticas fixadas:
  - [x] httpcore==1.0.9 (compatível Python 3.14)
  - [x] httpx==0.27.0 (compatível Python 3.14)
- [x] Sem conflitos de typing

**Status:** [ ] Pendente [ ] Em Progresso [x] Concluído

---

## 7. Validação Final

- [ ] Aplicação roda em modo produção
- [ ] Logs configurados e acessíveis
- [ ] Erros críticos tratados
- [ ] Documentação mínima presente
- [ ] Docker (se aplicável) funcional

---

## Assinatura

**Desenvolvedor:** ___________________________

**Data de conclusão:** ___/___/______

**Aprovado por:** ___________________________
