#!/usr/bin/env python3
"""
Script de teste atualizado para AguaFlow.
Valida a conexão com as tabelas reais: 'unidades' e 'leituras'.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# 1. Configuração do Ambiente
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Nota: Ajustado para as chaves padrão que costumas usar
SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY')

# Dados de teste baseados na estrutura real do banco
UNIDADE_ID_EXISTENTE = "QR161"  # Unidade que já cadastrámos no Supabase
VALOR_TESTE = 123.4
LEITURISTA = "Zelador - Teste Final"

def testar_fluxo_completo():
    print("=" * 60)
    print("AGUAFLOW - TESTE DE INTEGRAÇÃO SUPABASE")
    print("=" * 60)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n❌ ERRO: Credenciais não encontradas no ficheiro .env")
        return False

    try:
        # 2. Inicialização
        print(f"\n[1/3] Conectando a: {SUPABASE_URL}")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("  [OK] Cliente Supabase criado.")

        # 3. Inserção na tabela 'leituras'
        print(f"\n[2/3] Inserindo leitura de teste para unidade: {UNIDADE_ID_EXISTENTE}")
        dados_leitura = {
            "unidade_id": UNIDADE_ID_EXISTENTE,
            "valor_leitura": VALOR_TESTE,
            "tipo_registro": "Água",
            "leiturista": LEITURISTA
            # Removi a linha do sincronizado aqui
        }
        
        insert_res = supabase.table("leituras").insert(dados_leitura).execute()
        
        if len(insert_res.data) > 0:
            print(f"  [OK] Dados inseridos com sucesso! ID: {insert_res.data[0].get('id')}")
            id_criado = insert_res.data[0].get('id')
        else:
            print("  [!] Falha ao confirmar inserção.")
            return False

        # 4. Verificação/Leitura
        print("\n[3/3] Verificando dados na nuvem...")
        select_res = supabase.table("leituras").select("*").eq("id", id_criado).execute()
        
        if len(select_res.data) > 0:
            print(f"  [OK] Leitura recuperada: {select_res.data[0]['valor_leitura']} m³")
            print("\n" + "=" * 60)
            print("RESULTADO: TESTE PASSED - O SISTEMA ESTÁ ONLINE")
            print("=" * 60)
            return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("RESULTADO: TESTE FAILED")
        print("=" * 60)
        print(f"\nErro: {str(e)}")
        print("\nDICA: Verifica se a tabela 'leituras' tem as colunas 'unidade_id' e 'valor_leitura'.")
        return False

if __name__ == "__main__":
    testar_fluxo_completo()