import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(override=True)

url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").strip()
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

try:
    supabase = create_client(url, key)
    res = supabase.auth.admin.list_users()
    
    print("--- USUÁRIOS ENCONTRADOS NO BANCO ---")
    user_id = None
    email_alvo = "clodoaldomaldonado112@gmail.com"

    for user in res:
        print(f"- {user.email}") # Isso vai listar todos para você conferir
        if user.email.lower() == email_alvo.lower():
            user_id = user.id
            break

    if user_id:
        supabase.auth.admin.update_user_by_id(
            user_id, 
            attributes={"user_metadata": {"role": "admin"}}
        )
        print("\n" + "="*40)
        print("      SUCESSO: VOCÊ AGORA É ADMIN!      ")
        print("="*40)
    else:
        print(f"\nERRO: O e-mail {email_alvo} NÃO está na lista acima.")
        print("DICA: Se a lista acima estiver vazia, você precisa se cadastrar no App primeiro.")

except Exception as e:
    print(f"\nErro: {e}")