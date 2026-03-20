"""
================================================================================
🗄️ PASTA: database/ - "COFRE LOCAL" DO AGUAFLOW
================================================================================

Esta pasta contém todo o código relacionado ao banco de dados local (SQLite).
É o nosso "COFRE LOCAL" onde guardamos os dados de forma segura e confiável.

🔐 POR QUE "COFRE LOCAL"?
   - Os dados ficam no celular do zelador, 100% seguro OFFLINE
   - Se o Wi-Fi cair, os dados NÃO se perdem
   - Cada leitura é validada em duas camadas (Python + SQL)
   - Sistema de backup cria cópias diárias automáticas
   - Dados sincronizam com Supabase quando conexão voltar

📦 MÓDULOS PRINCIPAIS:
   • database.py      → Gerenciador unificado de BD (leituras, validação, reset)
   • backup.py        → Cria backups timestampados (segurança extra)
   • reset.py         → Reseta período mensal (move atual → anterior)
   • gestao_periodos.py → Gerencia ciclos de leitura
   • diagnostico.py   → Ferramentas para diagnóstico de dados

🛡️ GARANTIAS DO COFRE:
   ✓ Nenhum dado se perde
   ✓ Validação rigorosa (sem letras, sem valores inválidos)
   ✓ Recuperação automática se app travar
   ✓ Backup de emergência
   ✓ Pronto para sincronizar com nuvem

Sistema de Banco de Dados:
   📍 Local: database/database.py → SQLite (aguaflow.db)
      - Rápido, confiável, funcionana OFFLINE
      - Toda validação é feita aqui
      - Suporta transactions com rollback automático
   
   ☁️ Remoto: Supabase (será integrado)
      - Backup na nuvem
      - Sincronização bidirecional
      - Trilha de auditoria
      - Resolução automática de conflitos

================================================================================
"""

# Exports principais para facilitar import
from database.database import Database

__all__ = ['Database']
