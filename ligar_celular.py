from pyngrok import ngrok
import os

# Abre o túnel na porta 8080 (onde o Flet roda)
url = ngrok.connect(8080).public_url
print("-" * 30)
print(f"LINK PARA O CELULAR: {url}")
print("-" * 30)

# Inicia o Flet no modo web na porta 8080
os.system("flet run --web --port 8080")
