#!/usr/bin/env bash
# frame_screenshots.sh
# Enmarca capturas del simulador con el marco PSD correspondiente al dispositivo
# y las escala al tamaño requerido por App Store Connect.
#
# - Capturas : directorio actual (*.png)
# - Marcos   : subdirectorio frames/ (*.psd)
# - Resultado: directorio actual (*_framed.png)
#
# Dispositivos soportados:
#   iPhone            → 1242×2688 (6.5")
#   iPad Pro 13"      → 2048×2732
#   iPad Pro 11"      → 1668×2388
#   (landscape: dimensiones invertidas)
#
# La correspondencia entre captura y marco se hace por similitud de tokens
# normalizados, sin depender de formato exacto (e.g. "13-inch" ↔ "13\"").

set -euo pipefail

FRAMES_DIR="frames"
OUTPUT_DIR="."
BG_COLOR="white"

# ─── Validaciones ─────────────────────────────────────────────────────────────

if ! command -v magick &>/dev/null; then
    echo "❌  ImageMagick no encontrado. Instálalo con: brew install imagemagick"
    exit 1
fi

if [[ ! -d "$FRAMES_DIR" ]]; then
    echo "❌  No se encontró el directorio de marcos: $FRAMES_DIR/"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# ─── Normalización de nombres ─────────────────────────────────────────────────
# Convierte a minúsculas, reemplaza 13"/11" por 13-inch/11-inch,
# elimina paréntesis y comprime espacios.

normalize_name() {
    local n
    n=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    n="${n//\"/-inch}"
    n="${n//(/}"
    n="${n//)/}"
    n=$(echo "$n" | tr -s ' ')
    echo "$n"
}

# Devuelve 0 si todas las palabras de $1 aparecen en $2
words_contained_in() {
    local needle="$1" haystack="$2"
    for word in $needle; do
        [[ "$haystack" == *"$word"* ]] || return 1
    done
    return 0
}

# ─── Función: encontrar el PSD que corresponde a una captura ──────────────────
# Argumentos: <nombre_base_captura> <orientacion: Portrait|Landscape>

find_frame() {
    local screenshot_name="$1"
    local orientation="$2"
    local norm_ss
    norm_ss=$(normalize_name "$screenshot_name")
    local best=""
    for psd in "$FRAMES_DIR"/*.psd; do
        [[ -f "$psd" ]] || continue
        local psd_base
        psd_base=$(basename "$psd" .psd)
        # Filtrar por orientación (Portrait / Landscape)
        [[ "$psd_base" == *"$orientation"* ]] || continue
        # Extraer el modelo del nombre del PSD (segmento antes del primer " - ")
        local device="${psd_base%% - *}"
        local norm_dev
        norm_dev=$(normalize_name "$device")
        if words_contained_in "$norm_dev" "$norm_ss"; then
            best="$psd"
            break
        fi
    done
    echo "$best"
}

# ─── Función: extraer info de capas del PSD ──────────────────────────────────
# Lee las capas del PSD y devuelve:
#   canvas_W canvas_H  screen_W screen_H screen_X screen_Y  frame_idx frame_X frame_Y
# La capa "Screen" (GrayscaleAlpha etiquetada "Screen") define dónde va la captura.
# La capa de dispositivo (etiquetada "Hardware" o nombre del dispositivo) va encima.

get_psd_layers() {
    local psd="$1"
    local canvas_w="" canvas_h=""
    local screen_idx="" screen_w="" screen_h="" screen_x="" screen_y=""
    local frame_idx="" frame_x="" frame_y=""

    while IFS='|' read -r idx label w h ox oy; do
        ox=$(echo "$ox" | tr -d '+')
        oy=$(echo "$oy" | tr -d '+')

        if [[ -z "$canvas_w" ]]; then
            canvas_w="$w"; canvas_h="$h"
        fi

        if [[ "$label" == "Screen" ]]; then
            screen_idx="$idx"; screen_w="$w"; screen_h="$h"; screen_x="$ox"; screen_y="$oy"
        elif [[ -n "$label" \
             && "$label" != "Status Bar" \
             && "$label" != "White Fill for Dark Mode" \
             && -z "$frame_idx" ]]; then
            frame_idx="$idx"; frame_x="$ox"; frame_y="$oy"
        fi
    done < <(magick identify -format "%[scene]|%[label]|%[w]|%[h]|%X|%Y\n" "$psd" 2>/dev/null)

    echo "$canvas_w $canvas_h $screen_idx $screen_w $screen_h $screen_x $screen_y $frame_idx $frame_x $frame_y"
}

app_store_target() {
    local psd_base="$1"   # nombre base del PSD elegido
    local orientation="$2"
    if [[ "$psd_base" == *"iPad Pro (M5) 13"* ]]; then
        [[ "$orientation" == "Landscape" ]] && echo "2732x2048" || echo "2048x2732"
    elif [[ "$psd_base" == *"iPad Pro (M5) 11"* ]]; then
        [[ "$orientation" == "Landscape" ]] && echo "2388x1668" || echo "1668x2388"
    else
        # iPhone: tamaño 6.5"
        [[ "$orientation" == "Landscape" ]] && echo "2688x1242" || echo "1242x2688"
    fi
}

# ─── Procesamiento ────────────────────────────────────────────────────────────

shopt -s nullglob
SCREENSHOTS=()
for f in *.png; do
    [[ "$f" == *_framed.png ]] && continue
    SCREENSHOTS+=("$f")
done

if [[ ${#SCREENSHOTS[@]} -eq 0 ]]; then
    echo "⚠️  No se encontraron archivos PNG en el directorio actual."
    exit 0
fi

echo "📸  Encontradas ${#SCREENSHOTS[@]} captura(s)."
echo ""

for SCREENSHOT in "${SCREENSHOTS[@]}"; do
    BASENAME=$(basename "$SCREENSHOT" .png)
    echo "▶  $SCREENSHOT"

    # Detectar orientación a partir de las dimensiones de la captura
    DIMS=$(magick identify -format "%wx%h" "$SCREENSHOT" 2>/dev/null)
    SS_W="${DIMS%%x*}"; SS_H="${DIMS##*x}"
    if (( SS_W > SS_H )); then
        ORIENTATION="Landscape"
    else
        ORIENTATION="Portrait"
    fi
    echo "   🔍  Orientación detectada: $ORIENTATION (${SS_W}×${SS_H})"

    # Buscar marco correspondiente (dispositivo + orientación)
    FRAME_PSD=$(find_frame "$BASENAME" "$ORIENTATION")
    if [[ -z "$FRAME_PSD" ]]; then
        echo "   ⚠️  Sin marco coincidente en $FRAMES_DIR/ — omitiendo."
        echo ""
        continue
    fi
    echo "   🖼   Marco: $FRAME_PSD"

    # Determinar tamaño objetivo App Store Connect
    TARGET=$(app_store_target "$(basename "$FRAME_PSD" .psd)" "$ORIENTATION")
    echo "   🎯  Target App Store: ${TARGET}"

    # ── Screen layer idx también necesario para enmascarar el marco
    read -r CANVAS_W CANVAS_H SCREEN_IDX SCREEN_W SCREEN_H SCREEN_X SCREEN_Y FRAME_IDX FRAME_X FRAME_Y \
        <<< "$(get_psd_layers "$FRAME_PSD")"

    if [[ -z "$SCREEN_W" || -z "$FRAME_IDX" ]]; then
        echo "   ❌  No se pudieron leer las capas del PSD — omitiendo."
        echo ""
        continue
    fi
    echo "   📐  Canvas: ${CANVAS_W}×${CANVAS_H} | Pantalla: ${SCREEN_W}×${SCREEN_H} @ +${SCREEN_X}+${SCREEN_Y} | Marco capa ${FRAME_IDX} @ +${FRAME_X}+${FRAME_Y}"

    # Reescalar la captura al área de pantalla si es necesario
    SRC="$SCREENSHOT"
    if [[ "$SS_W" != "$SCREEN_W" || "$SS_H" != "$SCREEN_H" ]]; then
        echo "   ↔️   Reescalando captura de ${SS_W}×${SS_H} a ${SCREEN_W}×${SCREEN_H}"
        SRC="$TMP_DIR/resized.png"
        magick "$SCREENSHOT" -resize "${SCREEN_W}x${SCREEN_H}!" "$SRC"
    fi

    # Posición de la capa Screen relativa a la capa del marco
    REL_X=$(( SCREEN_X - FRAME_X ))
    REL_Y=$(( SCREEN_Y - FRAME_Y ))

    # Aplanar el PSD completo y colocar la captura encima en la posición de pantalla.
    COMPOSITE="$TMP_DIR/composite.png"
    magick "${FRAME_PSD}" -flatten \
        "$SRC" -geometry "+${SCREEN_X}+${SCREEN_Y}" -composite \
        "$COMPOSITE"

    # Escalar al tamaño App Store Connect del dispositivo
    OUT_FILE="${BASENAME}_framed.png"
    magick "$COMPOSITE" \
        -resize "$TARGET" \
        -background "$BG_COLOR" \
        -gravity Center \
        -extent "$TARGET" \
        "$OUT_FILE"

    echo "   ✅  → $OUT_FILE (${TARGET})"
    echo ""
done

echo "🎉  Listo."
