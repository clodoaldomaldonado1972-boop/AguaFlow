import smtplib
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    # USE A SUA SENHA DE 16 DÍGITOS AQUI (SEM ESPAÇOS)
    server.login("clodoaldomaldonado112@gmail.com", "jbtxbeqxfslfufgn")
    print("✅ CONEXÃO COM SUCESSO! O Google aceitou.")
    server.quit()
except Exception as e:
    print(f"❌ ERRO AINDA PERSISTE: {e}")
