#!/usr/bin/env bash
# set_simulator_statusbar.sh
# Aplica una configuración de status bar a todos los simuladores de iOS en ejecución.

set -euo pipefail

# ─── Obtener simuladores iOS en ejecución (formato: "Nombre|UDID") ────────────

BOOTED_DEVICES=()
while IFS= read -r entry; do
    BOOTED_DEVICES+=("$entry")
done < <(
    xcrun simctl list devices booted --json \
    | jq -r '.devices
             | to_entries[]
             | select(.key | contains("iOS"))
             | .value[]
             | select(.state == "Booted")
             | "\(.name)|\(.udid)"'
)

if [[ ${#BOOTED_DEVICES[@]} -eq 0 ]]; then
    echo "⚠️  No hay simuladores de iOS en ejecución."
    exit 0
fi

echo "📱  Simuladores iOS activos: ${#BOOTED_DEVICES[@]}"
echo ""

# ─── Capturar la hora actual (fija para todas las capturas) ──────────────────

CURRENT_TIME=$(date +%H:%M)
echo "🕐  Hora fijada: $CURRENT_TIME"
echo ""

# ─── Aplicar configuración de status bar a cada simulador ─────────────────────

for entry in "${BOOTED_DEVICES[@]}"; do
    NAME="${entry%%|*}"
    UDID="${entry##*|}"

    echo "▶  $NAME ($UDID)"

    xcrun simctl status_bar "$UDID" override \
        --time "$CURRENT_TIME" \
        --dataNetwork wifi \
        --wifiMode active \
        --wifiBars 3 \
        --cellularMode active \
        --cellularBars 4 \
        --batteryState discharging \
        --batteryLevel 100

    echo "   ✅  Status bar configurada."
    echo ""
done

echo "🎉  Listo."
