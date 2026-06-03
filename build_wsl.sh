
#!/bin/bash
# Script de build isolado — roda em WSL2 com PATH limpo do Linux
# Redireciona TUDO para log no filesystem Linux (evita broken pipe do Windows)
exec > /tmp/aguaflow_build.log 2>&1
set -e

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/home/clodo
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$HOME/.aguaflow_venv/bin:$HOME/flutter/3.41.4/bin:$PATH
export FLET_CLI_NO_RICH_OUTPUT=1
export ANDROID_HOME=$HOME/Android/sdk

SRC=/mnt/c/AguaFlow
BUILD_DIR=$HOME/aguaflow_build
FLUTTER_DIR=$BUILD_DIR/build/flutter

echo "=== AguaFlow v1.3.0 — Build APK 143 ==="
echo "Java:   $(java -version 2>&1 | head -1)"
echo "Python: $(python3 --version)"
echo "Flet:   $(flet --version)"
echo "Flutter:$(flutter --version 2>&1 | head -1)"
echo "Mem:    $(free -h | grep Mem | awk '{print $2}')"
echo "Dir:    $BUILD_DIR"
echo "===================================="

# Sincroniza apenas os arquivos necessários do Windows para o WSL
echo "Sincronizando fontes..."
rsync -a --delete \
    --exclude='*.apk' \
    --exclude='*.log' \
    --exclude='*.pdf' \
    --exclude='*.csv' \
    --exclude='*.spec' \
    --exclude='*.sh' \
    --exclude='*.txt.bak' \
    --exclude='Dockerfile' \
    --exclude='docker-compose.yml' \
    --exclude='build/' \
    --exclude='build_output.log' \
    --exclude='docs/' \
    --exclude='agents-e-skills/' \
    --exclude='logs/' \
    --exclude='storage/' \
    --exclude='testes/' \
    --exclude='tests/' \
    --exclude='export/' \
    --exclude='supabase/' \
    --exclude='estrutura.txt' \
    --exclude='checklist_mvp.md' \
    --exclude='*.md' \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.venv/' \
    --exclude='C:*' \
    --exclude='assets/Photos/' \
    "$SRC/" "$BUILD_DIR/"

echo "Sincronizacao OK"

cd "$BUILD_DIR"
ls main.py requirements.txt >/dev/null && echo "main.py + requirements.txt: OK"
echo "Tamanho do BUILD_DIR: $(du -sh . --exclude=build | cut -f1)"

# ── PRÉ-PASSO: Determina modo de build (incremental vs clean) ──
# flet build testa pubspec.yaml em FLUTTER_DIR: se ausente, faz build incremental quebrado
if [ -f "$FLUTTER_DIR/pubspec.yaml" ]; then
    # Flutter project válido: corrige apenas o .kt corrompido (build incremental seguro)
    STALE_MAIN="$FLUTTER_DIR/android/app/src/main/kotlin/br/com/vivereprudente/aguaflow/MainActivity.kt"
    if [ -f "$STALE_MAIN" ]; then
        cat > "$STALE_MAIN" << 'STALE_EOF'
package br.com.vivereprudente.aguaflow

import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity()
STALE_EOF
        echo "✅ MainActivity.kt stale corrigido (build incremental)"
    fi
else
    # Flutter dir ausente ou inválido: apaga build/ inteiro para forçar build limpo
    echo "⚠️  FLUTTER_DIR sem pubspec.yaml — limpando build/ para rebuild limpo..."
    rm -rf "$BUILD_DIR/build"
    echo "✅ build/ limpo — flet criará tudo do zero"
fi

# ── PASSO 1: flet build gera o projeto Flutter + empacota Python + compila APK base ──
flet build apk \
    --org br.com.vivereprudente \
    --project AguaFlow \
    --product "AguaFlow" \
    --build-version 1.3.0 \
    --build-number 143 \
    --permissions camera photo_library \
    --yes

echo "===================================="
echo "Flet build OK. Injetando extensao de camera..."
echo "===================================="

# ── PASSO 2: Injeta dependências Flutter no pubspec.yaml (idempotente) ──
# Adiciona permissão VIBRATE ao AndroidManifest.xml para HapticFeedback funcionar
MANIFEST="$FLUTTER_DIR/android/app/src/main/AndroidManifest.xml"
if [ -f "$MANIFEST" ] && ! grep -q "VIBRATE" "$MANIFEST"; then
    sed -i '/<uses-permission android:name="android.permission.CAMERA"/i\    <uses-permission android:name="android.permission.VIBRATE"/>' "$MANIFEST"
    echo "✅ Permissão VIBRATE adicionada ao AndroidManifest.xml"
else
    echo "⏭️  Permissão VIBRATE já presente ou manifest não encontrado"
fi

PUBSPEC="$FLUTTER_DIR/pubspec.yaml"
if ! grep -q "image_picker" "$PUBSPEC"; then
    sed -i 's/  flet: 0.82.2/  flet: 0.82.2\n  image_picker: 1.1.2/' "$PUBSPEC"
    echo "✅ image_picker 1.1.2 (versão exata) adicionado ao pubspec.yaml"
else
    echo "⏭️  image_picker ja presente no pubspec.yaml"
fi
if ! grep -q "mobile_scanner" "$PUBSPEC"; then
    sed -i 's/  image_picker: 1.1.2/  image_picker: 1.1.2\n  mobile_scanner: 6.0.0/' "$PUBSPEC"
    echo "✅ mobile_scanner 6.0.0 (versão exata) adicionado ao pubspec.yaml"
else
    echo "⏭️  mobile_scanner ja presente no pubspec.yaml"
fi

# ── PASSO 3: Copia arquivos Dart das extensões ──
FLUTTER_LIB="$FLUTTER_DIR/lib"
cp "$BUILD_DIR/flutter_camera/camera_service.dart" "$FLUTTER_LIB/"
cp "$BUILD_DIR/flutter_camera/camera_extension.dart" "$FLUTTER_LIB/"
cp "$BUILD_DIR/flutter_camera/barcode_service.dart" "$FLUTTER_LIB/"
cp "$BUILD_DIR/flutter_camera/barcode_extension.dart" "$FLUTTER_LIB/"
echo "✅ Arquivos Dart da camera e barcode copiados"

# Copia BeepPlugin.kt e escreve MainActivity.kt completo (idempotente por sobrescrita)
# Motivo: sed falha — Flet gera "class MainActivity : FlutterActivity()" sem "{" e com espaço,
# impossível de casar com padrão de substituição sem format-matching frágil.
KOTLIN_DIR="$FLUTTER_DIR/android/app/src/main/kotlin/br/com/vivereprudente/aguaflow"
cp "$BUILD_DIR/flutter_camera/BeepPlugin.kt" "$KOTLIN_DIR/"
echo "✅ BeepPlugin.kt copiado"

MAIN_ACTIVITY="$KOTLIN_DIR/MainActivity.kt"
cat > "$MAIN_ACTIVITY" << 'KOTLIN_EOF'
package br.com.vivereprudente.aguaflow

import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: io.flutter.embedding.engine.FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        flutterEngine.plugins.add(BeepPlugin())
    }
}
KOTLIN_EOF
echo "✅ MainActivity.kt escrito com BeepPlugin registrado"

# ── PASSO 4: Registra extensões em main.dart (idempotente) ──
MAIN_DART="$FLUTTER_LIB/main.dart"
if ! grep -q "CameraExtension" "$MAIN_DART"; then
    sed -i "1s/^/import 'camera_extension.dart';\n/" "$MAIN_DART"
    sed -i "s/List<FletExtension> extensions = \[/List<FletExtension> extensions = [\n  CameraExtension(),/" "$MAIN_DART"
    echo "✅ CameraExtension registrada em main.dart"
else
    echo "⏭️  CameraExtension ja registrada em main.dart"
fi
if ! grep -q "BarcodeScannerExtension" "$MAIN_DART"; then
    sed -i "1s/^/import 'barcode_extension.dart';\n/" "$MAIN_DART"
    sed -i "s/List<FletExtension> extensions = \[/List<FletExtension> extensions = [\n  BarcodeScannerExtension(),/" "$MAIN_DART"
    echo "✅ BarcodeScannerExtension registrada em main.dart"
else
    echo "⏭️  BarcodeScannerExtension ja registrada em main.dart"
fi

# ── PASSO 5: Atualiza dependências e recompila com câmera ──
# SERIOUS_PYTHON_SITE_PACKAGES deve apontar para o diretório gerado pelo flet build
export SERIOUS_PYTHON_SITE_PACKAGES="$BUILD_DIR/build/site-packages"
echo "SERIOUS_PYTHON_SITE_PACKAGES=$SERIOUS_PYTHON_SITE_PACKAGES"

echo "⏳ flutter pub get..."
cd "$FLUTTER_DIR"
flutter pub get

echo "⏳ flutter build apk com camera..."
flutter build apk --release --build-number 143 --build-name 1.3.0

# ── PASSO 6: Copia o APK final ──
APK=$(find "$FLUTTER_DIR/build/app/outputs/flutter-apk" -name "app-release.apk" 2>/dev/null | head -1)
[ -z "$APK" ] && APK=$(find "$FLUTTER_DIR/build" -name "*.apk" 2>/dev/null | head -1)
[ -z "$APK" ] && APK="$BUILD_DIR/build/apk/AguaFlow.apk"

if [ -f "$APK" ]; then
    cp "$APK" /mnt/c/AguaFlow/AguaFlow-1.3.0-b143.apk
    cp /tmp/aguaflow_build.log /mnt/c/AguaFlow/build_output.log
    echo "===================================="
    echo "APK gerado com sucesso!"
    echo "Destino: C:/AguaFlow/AguaFlow-1.3.0.apk"
    echo "Tamanho: $(du -h "$APK" | cut -f1)"
    echo "===================================="
else
    echo "ERRO: APK nao encontrado apos o build."
    find "$BUILD_DIR/build" -type f 2>/dev/null | head -20
    cp /tmp/aguaflow_build.log /mnt/c/AguaFlow/build_output.log
    exit 1
fi
