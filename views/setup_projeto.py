import os
import subprocess
import sys
from database.database import Database

def configurar_ambiente():
    print("🛠️ Iniciando Configuração do AguaFlow - Vivere Prudente...")
    
    # 1. Criação de Pastas Essenciais
    pastas = ['database', 'views', 'assets', 'logs']
    for pasta in pastas:
        if not os.path.exists(pasta):
            os.makedirs(pasta)
            print(f"✅ Pasta '{pasta}' criada.")

    # 2. Verificação do Tesseract (Vital para o OCR)
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if not os.path.exists(tesseract_path):
        print("⚠️ AVISO: Tesseract OCR não encontrado em C:\\Program Files\\")
        print("🔗 Baixe em: https://github.com/UB-Mannheim/tesseract/wiki")
    else:
        print("✅ Tesseract OCR detectado.")

    # 3. Inicialização do Banco de Dados Local
    try:
        print("🗄️ Inicializando banco de dados SQLite...")
        Database.init_db()
        # Aqui você pode chamar uma função para popular as 98 unidades se o banco estiver vazio
        print("✅ Banco de dados pronto para uso.")
    except Exception as e:
        print(f"❌ Erro ao iniciar banco: {e}")

    # 4. Verificação do Arquivo .env
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("NEXT_PUBLIC_SUPABASE_URL=seu_url_aqui\n")
            f.write("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY=sua_chave_aqui\n")
        print("📝 Arquivo .env criado (Lembre-se de preencher com as chaves do Supabase!).")

    print("\n🚀 Configuração concluída! Use 'python main.py' para iniciar.")

if __name__ == "__main__":
    configurar_ambiente()