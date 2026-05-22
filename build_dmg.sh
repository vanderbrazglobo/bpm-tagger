#!/bin/bash
# build_dmg.sh — Gera o instalador .dmg do BPM Tagger para macOS
set -e

APP_NAME="BPM Tagger"
VERSION="1.4.1"
DMG_NAME="BPM-Tagger-${VERSION}"
BUILD_DIR="$(pwd)/build_dmg"
APP_DIR="${BUILD_DIR}/${APP_NAME}.app"
CONTENTS="${APP_DIR}/Contents"
MACOS="${CONTENTS}/MacOS"
RESOURCES="${CONTENTS}/Resources"
PYTHON="$(which python3.11 2>/dev/null || echo ~/envs/bpm/bin/python3.11)"

echo "🎵 BPM Tagger — Build DMG v${VERSION}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Limpa build anterior
echo "🧹 Limpando build anterior..."
rm -rf "${BUILD_DIR}"
mkdir -p "${MACOS}" "${RESOURCES}"

# 2. Copia o script principal
echo "📦 Copiando arquivos..."
cp bpm_tagger_app.py "${MACOS}/bpm_tagger_app.py"

# 3. Cria o launcher shell
cat > "${MACOS}/${APP_NAME}" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=$(find ~/envs/bpm/bin -name "python3.11" 2>/dev/null | head -1)
if [ -z "$PYTHON" ]; then
    osascript -e 'display alert "Python não encontrado" message "Instale o ambiente virtual conforme o README." as critical'
    exit 1
fi
exec "$PYTHON" "${DIR}/bpm_tagger_app.py"
LAUNCHER
chmod +x "${MACOS}/${APP_NAME}"

# 4. Cria o Info.plist
cat > "${CONTENTS}/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd"\>
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>BPM Tagger</string>
    <key>CFBundleDisplayName</key>
    <string>BPM Tagger</string>
    <key>CFBundleIdentifier</key>
    <string>com.vanderbraz.bpm-tagger</string>
    <key>CFBundleVersion</key>
    <string>1.4.1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.4.1</string>
    <key>CFBundleExecutable</key>
    <string>BPM Tagger</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
PLIST

# 5. Cria ícone simples (texto emoji como placeholder)
echo "🎨 Criando ícone..."
cat > /tmp/make_icon.py << 'ICONPY'
import os, struct, zlib

# Cria um ícone PNG simples 512x512 com fundo azul e nota musical
def make_png(size=512):
    import struct, zlib
    w = h = size
    raw = []
    for y in range(h):
        row = [0]
        for x in range(w):
            # Fundo gradiente azul escuro
            r = 26
            g = 86 + int((y/h) * 30)
            b = 219
            a = 255
            # Círculo central
            cx, cy = w//2, h//2
            radius = w * 0.42
            dist = ((x-cx)**2 + (y-cy)**2) ** 0.5
            if dist < radius:
                r, g, b = 15, 52, 161
            # Nota musical simples (retângulo)
            nx, ny, nw, nh = int(w*0.38), int(h*0.22), int(w*0.06), int(h*0.45)
            if nx <= x <= nx+nw and ny <= y <= ny+nh:
                r, g, b = 255, 255, 255
            nx2 = int(w*0.56)
            if nx2 <= x <= nx2+nw and ny <= y <= ny+nh:
                r, g, b = 255, 255, 255
            # Linha horizontal
            lx, ly = int(w*0.38), int(h*0.38)
            if lx <= x <= lx + int(w*0.26) and ly <= y <= ly + int(h*0.04):
                r, g, b = 255, 255, 255
            row += [r, g, b, a]
        raw.append(bytes(row))

    def png_chunk(name, data):
        c = zlib.crc32(name + data) & 0xffffffff
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)

    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    # RGBA = color type 6
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
    raw_data = b''.join(raw)
    idat = zlib.compress(raw_data)
    png = b'\x89PNG\r\n\x1a\n'
    png += png_chunk(b'IHDR', ihdr)
    png += png_chunk(b'IDAT', idat)
    png += png_chunk(b'IEND', b'')
    return png

with open('/tmp/AppIcon.png', 'wb') as f:
    f.write(make_png(512))
print("Icon OK")
ICONPY
python3 /tmp/make_icon.py

# Converte PNG para icns
if command -v sips &>/dev/null; then
    mkdir -p /tmp/AppIcon.iconset
    for size in 16 32 64 128 256 512; do
        sips -z $size $size /tmp/AppIcon.png --out /tmp/AppIcon.iconset/icon_${size}x${size}.png &>/dev/null
        sips -z $((size*2)) $((size*2)) /tmp/AppIcon.png --out /tmp/AppIcon.iconset/icon_${size}x${size}@2x.png &>/dev/null
    done
    iconutil -c icns /tmp/AppIcon.iconset -o "${RESOURCES}/AppIcon.icns" 2>/dev/null && echo "✔ Ícone gerado" || echo "⚠ Ícone não gerado (opcional)"
fi

# 6. Cria o DMG
echo "💿 Gerando DMG..."
test -f "${DMG_NAME}.dmg" && rm "${DMG_NAME}.dmg"

create-dmg \
    --volname "${APP_NAME} ${VERSION}" \
    --volicon "${RESOURCES}/AppIcon.icns" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "${APP_NAME}.app" 150 180 \
    --hide-extension "${APP_NAME}.app" \
    --app-drop-link 450 180 \
    "${DMG_NAME}.dmg" \
    "${BUILD_DIR}" 2>/dev/null || \
create-dmg \
    --volname "${APP_NAME} ${VERSION}" \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "${APP_NAME}.app" 150 180 \
    --app-drop-link 450 180 \
    "${DMG_NAME}.dmg" \
    "${BUILD_DIR}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DMG criado: ${DMG_NAME}.dmg"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
