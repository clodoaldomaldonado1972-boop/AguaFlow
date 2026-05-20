#!/bin/bash
# Script de build APK — AguaFlow v1.2.0
# Executar em WSL2 Ubuntu: bash /mnt/c/AguaFlow/build_apk_wsl.sh
set -e

PROJECT_SRC="/mnt/c/AguaFlow"
BUILD_DIR="$HOME/aguaflow_build"
FLET_VERSION="0.82.2"

echo "========================================"
echo " AguaFlow — Build APK via Flet $FLET_VERSION"
echo "========================================"

# 1. Dependências do sistema
echo "[1/6] Instalando dependências do sistema..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-pip python3-venv python3-dev \
    git curl unzip wget \
    openjdk-17-jdk \
    lib32z1 lib32ncurses-dev \
    build-essential \
    autoconf automake libtool pkg-config zlib1g-dev libffi-dev libssl-dev

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
echo "Java: $(java -version 2>&1 | head -1)"

# 2. Venv Python no WSL2
echo "[2/6] Criando venv Python..."
python3 -m venv "$HOME/.aguaflow_venv"
source "$HOME/.aguaflow_venv/bin/activate"
pip install --upgrade pip -q
# Instala o Cython obrigatório para compilação de receitas do Android NDK
pip install "cython<3.0.0" -q
pip install "flet==$FLET_VERSION" -q
echo "Flet instalado: $(flet --version)"

# 3. Copiar projeto para filesystem nativo do WSL2 (mais rápido que /mnt/c/)
echo "[3/6] Sincronizando projeto para $BUILD_DIR..."
mkdir -p "$BUILD_DIR"
rsync -a --delete \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='database/Backups' \
    --exclude='relatorios' \
    --exclude='exports' \
    --exclude='temp' \
    --exclude='*.log' \
    --exclude='*.db' \
    --exclude='build/' \
    "$PROJECT_SRC/" "$BUILD_DIR/"

echo "Projeto sincronizado. Arquivos Python:"
find "$BUILD_DIR" -name "*.py" | wc -l

# 4. Garantir .env presente
if [ ! -f "$BUILD_DIR/.env" ]; then
    echo "ERRO: .env não encontrado em $BUILD_DIR"
    exit 1
fi
echo ".env: OK"

# 5. Build APK
echo "[4/6] Iniciando flet build apk..."
cd "$BUILD_DIR"

export FLET_CLI_NO_RICH_OUTPUT=1
export PYTHONUTF8=1

# CORREÇÃO: O Flet 0.82.2 lê todas as configurações, permissões e versões
# diretamente do seu arquivo buildozer.spec. Não passamos parâmetros manuais aqui.
flet build apk

# 6. Copiar APK para Windows
echo "[5/6] Copiando APK para Windows..."
# O find agora busca em todo o diretório de build, incluindo a pasta oculta .buildozer
APK_PATH=$(find "$BUILD_DIR" -name "*.apk" 2>/dev/null | head -1)

if [ -n "$APK_PATH" ]; then
    cp "$APK_PATH" "/mnt/c/AguaFlow/AguaFlow-1.2.0.apk"
    echo "========================================"
    echo " APK gerado com sucesso!"
    echo " Windows: C:\\AguaFlow\\AguaFlow-1.2.0.apk"
    echo " Tamanho: $(du -h "$APK_PATH" | cut -f1)"
    echo "========================================"
else
    echo "ERRO: APK não encontrado após build."
    echo "Verifique os logs acima para identificar falhas do compilador."
    exit 1
fi