[app]

# Identidade do aplicativo
title = AguaFlow
package.name = aguaflow
package.domain = br.com.vivereprudente

# Versão
version = 1.2.0
version.code = 120

# Fonte
source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,svg,kv,atlas,json,ttf,otf,env
# Adicionado .env explicitamente para garantir que as chaves de API subam no APK
source.include_patterns = assets/*,assets/**/*,.env
source.exclude_dirs = tests,bin,__pycache__,.venv,venv,.git,database/Backups,relatorios,exports,temp
source.exclude_patterns = *.pyc,*.pyo,*.spec,test_*.py,docs/*,*.md,*.log

# Ponto de entrada
entry_point = main.py

# Ícone e splash
# icon.filename = assets/icon.png
# presplash.filename = assets/splash.png
presplash.color = #121417

# Orientação
orientation = portrait

# Permissões Android necessárias
android.permissions = CAMERA,INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE

# API Android
android.minapi = 21
android.api = 33
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

# Recursos Android
android.allow_backup = True

# Features Android (câmera)
android.manifest.features = android.hardware.camera

# Requirements — CORRIGIDO: Tudo em uma única linha contínua, sem quebras
requirements = python3,flet==0.82.2,supabase,httpx,pytz,python-dotenv,fpdf2,qrcode,pillow,requests,anthropic,certifi

# Gradle — aumenta heap para compilações pesadas
android.gradle_dependencies = com.android.support:appcompat-v7:28.0.0

# Fullscreen
fullscreen = 0

# Log
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1