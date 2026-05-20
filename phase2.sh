#!/bin/bash
exec >> /tmp/aguaflow_build.log 2>&1
set -e

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/home/clodo
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$HOME/.aguaflow_venv/bin:$HOME/flutter/3.41.4/bin:$PATH
export ANDROID_HOME=$HOME/Android/sdk
export SERIOUS_PYTHON_SITE_PACKAGES=$HOME/aguaflow_build/build/site-packages

BUILD_DIR=$HOME/aguaflow_build
FLUTTER_DIR=$BUILD_DIR/build/flutter
FLUTTER_LIB=$FLUTTER_DIR/lib
PUBSPEC=$FLUTTER_DIR/pubspec.yaml
MAIN_DART=$FLUTTER_LIB/main.dart

echo "=== FASE 2: Injecao Camera + Recompilacao ==="
echo "SERIOUS_PYTHON_SITE_PACKAGES=$SERIOUS_PYTHON_SITE_PACKAGES"
echo "Flutter: $(flutter --version 2>&1 | head -1)"

# PASSO 2: image_picker (idempotente)
if ! grep -q "image_picker" "$PUBSPEC"; then
    sed -i 's/  flet: 0.82.2/  flet: 0.82.2\n  image_picker: ^1.1.2/' "$PUBSPEC"
    echo "image_picker adicionado ao pubspec.yaml"
else
    echo "image_picker ja presente no pubspec.yaml"
fi

# PASSO 3: Copia Dart da camera
cp "$BUILD_DIR/flutter_camera/camera_service.dart" "$FLUTTER_LIB/"
cp "$BUILD_DIR/flutter_camera/camera_extension.dart" "$FLUTTER_LIB/"
echo "Arquivos Dart da camera copiados"

# PASSO 4: Registra CameraExtension no main.dart (idempotente)
if ! grep -q "CameraExtension" "$MAIN_DART"; then
    sed -i "1s/^/import 'camera_extension.dart';\n/" "$MAIN_DART"
    sed -i "s/List<FletExtension> extensions = \[/List<FletExtension> extensions = [\n  CameraExtension(),/" "$MAIN_DART"
    echo "CameraExtension registrada em main.dart"
else
    echo "CameraExtension ja registrada em main.dart"
fi

echo "--- main.dart (top 15 linhas) ---"
head -15 "$MAIN_DART"

# PASSO 5: flutter pub get + build
cd "$FLUTTER_DIR"
echo "=== flutter pub get ==="
flutter pub get

echo "=== flutter build apk --release ==="
flutter build apk --release

# PASSO 6: Copia APK final
APK=$(find "$FLUTTER_DIR/build/app/outputs/flutter-apk" -name "app-release.apk" 2>/dev/null | head -1)
[ -z "$APK" ] && APK=$(find "$FLUTTER_DIR/build" -name "*.apk" 2>/dev/null | head -1)

if [ -f "$APK" ]; then
    cp "$APK" /mnt/c/AguaFlow/AguaFlow-1.2.0.apk
    cp /tmp/aguaflow_build.log /mnt/c/AguaFlow/build_output.log
    echo "===================================="
    echo "APK GERADO COM SUCESSO!"
    echo "Destino: C:/AguaFlow/AguaFlow-1.2.0.apk"
    du -h "$APK"
    echo "===================================="
else
    echo "ERRO: APK nao encontrado apos o build."
    find "$BUILD_DIR/build" -type f -name "*.apk" 2>/dev/null
    cp /tmp/aguaflow_build.log /mnt/c/AguaFlow/build_output.log
    exit 1
fi
