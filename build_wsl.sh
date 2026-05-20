#!/bin/bash
# Script de build isolado — roda em WSL2 com PATH limpo do Linux
# Redireciona TUDO para log no filesystem Linux (evita broken pipe do Windows)
exec > /tmp/aguaflow_build.log 2>&1
set -e

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/home/clodo
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$HOME/.aguaflow_venv/bin:$PATH
export FLET_CLI_NO_RICH_OUTPUT=1
export ANDROID_HOME=$HOME/Android/sdk

BUILD_DIR=$HOME/aguaflow_build

echo "=== AguaFlow v1.2.0 — Build APK ==="
echo "Java:   $(java -version 2>&1 | head -1)"
echo "Python: $(python3 --version)"
echo "Flet:   $(flet --version)"
echo "Mem:    $(free -h | grep Mem | awk '{print $2}')"
echo "Dir:    $BUILD_DIR"
echo "===================================="

cd "$BUILD_DIR"
ls main.py requirements.txt >/dev/null && echo "main.py + requirements.txt: OK"

flet build apk \
    --org br.com.vivereprudente \
    --project AguaFlow \
    --product "AguaFlow" \
    --build-version 1.2.0 \
    --build-number 120 \
    --permissions camera photo_library \
    --yes

APK=$(find "$BUILD_DIR/build" -name "*.apk" 2>/dev/null | head -1)
if [ -n "$APK" ]; then
    cp "$APK" /mnt/c/AguaFlow/AguaFlow-1.2.0.apk
    cp /tmp/aguaflow_build.log /mnt/c/AguaFlow/build_output.log
    echo "===================================="
    echo "APK gerado com sucesso!"
    echo "Destino: C:/AguaFlow/AguaFlow-1.2.0.apk"
    echo "Tamanho: $(du -h "$APK" | cut -f1)"
    echo "===================================="
else
    echo "ERRO: APK nao encontrado apos o build."
    find "$BUILD_DIR/build" -type f 2>/dev/null | head -20
    cp /tmp/aguaflow_build.log /mnt/c/AguaFlow/build_output.log
    exit 1
fi
