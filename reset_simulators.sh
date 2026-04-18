#!/usr/bin/env bash
# reset_simulators.sh
# Apaga, borra el contenido y reinicia todos los simuladores disponibles en Xcode.
#
# Uso:
#   ./reset_simulators.sh          # Pide confirmación antes de borrar
#   ./reset_simulators.sh --force  # Borra sin pedir confirmación

set -euo pipefail

FORCE=false
for arg in "$@"; do
    [[ "$arg" == "--force" ]] && FORCE=true
done

# ─── Obtener todos los simuladores disponibles (no "unavailable") ─────────────

mapfile -t SIMULATORS < <(
    xcrun simctl list devices available --json \
    | jq -r '.devices
             | to_entries[]
             | .value[]
             | "\(.name)|\(.udid)|\(.state)"'
)

if [[ ${#SIMULATORS[@]} -eq 0 ]]; then
    echo "⚠️  No se encontraron simuladores disponibles."
    exit 0
fi

echo "📱  Simuladores encontrados: ${#SIMULATORS[@]}"
echo ""
for entry in "${SIMULATORS[@]}"; do
    NAME="${entry%%|*}"
    REST="${entry#*|}"
    UDID="${REST%%|*}"
    STATE="${REST##*|}"
    printf "   • %-40s %s  [%s]\n" "$NAME" "$UDID" "$STATE"
done
echo ""

# ─── Confirmación ─────────────────────────────────────────────────────────────

if [[ "$FORCE" == false ]]; then
    read -r -p "⚠️  Se borrará el contenido de TODOS los simuladores. ¿Continuar? [s/N] " REPLY
    echo ""
    if [[ ! "$REPLY" =~ ^[sS]$ ]]; then
        echo "Operación cancelada."
        exit 0
    fi
fi

# ─── Apagar los simuladores en ejecución ──────────────────────────────────────

BOOTED=()
for entry in "${SIMULATORS[@]}"; do
    STATE="${entry##*|}"
    [[ "$STATE" == "Booted" ]] && BOOTED+=("${entry%%|*}|$(echo "$entry" | cut -d'|' -f2)")
done

if [[ ${#BOOTED[@]} -gt 0 ]]; then
    echo "⏹️  Apagando simuladores en ejecución…"
    for entry in "${BOOTED[@]}"; do
        NAME="${entry%%|*}"
        UDID="${entry##*|}"
        echo "   Apagando $NAME ($UDID)…"
        xcrun simctl shutdown "$UDID" 2>/dev/null || true
    done
    echo ""
fi

# ─── Borrar contenido de cada simulador ───────────────────────────────────────

echo "🗑️  Borrando contenido…"
OK=0
FAIL=0
for entry in "${SIMULATORS[@]}"; do
    NAME="${entry%%|*}"
    REST="${entry#*|}"
    UDID="${REST%%|*}"

    if xcrun simctl erase "$UDID" 2>/dev/null; then
        printf "   ✅  %-40s %s\n" "$NAME" "$UDID"
        (( OK++ )) || true
    else
        printf "   ❌  %-40s %s  (no se pudo borrar)\n" "$NAME" "$UDID"
        (( FAIL++ )) || true
    fi
done

echo ""
echo "🎉  Listo. $OK simulador(es) reseteado(s)$([ "$FAIL" -gt 0 ] && echo ", $FAIL con error" || echo ".")."
