#!/usr/bin/env python3
"""gen_icon_android.py — Genera el icono de la aplicación Android BusGasteiz.

Genera PNGs del icono en todas las densidades mipmap usando el símbolo de
autobús (Material Design: directions_bus) en blanco sobre el fondo verde
corporativo (#60A589), y actualiza los ficheros XML del icono adaptativo.

El diseño es equivalente al icono iOS generado por gen_icon.swift.

Requisitos: rsvg-convert (librsvg, disponible con `brew install librsvg`)

Uso: python3 gen_icon_android.py
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
ANDROID_RES = REPO_ROOT / "android" / "BusGasteiz" / "app" / "src" / "main" / "res"

ACCENT_COLOR = "#60A589"

# Material Design directions_bus (24×24 viewport) — mismo símbolo que el badge
# de parada de la lista de paradas de la app Android.
BUS_PATH = (
    "M4,16c0,0.88 0.39,1.67 1,2.22V20c0,0.55 0.45,1 1,1h1c0.55,0 1,-0.45 1,-1v-1h8"
    "v1c0,0.55 0.45,1 1,1h1c0.55,0 1,-0.45 1,-1v-1.78c0.61,-0.55 1,-1.34 1,-2.22"
    "V6c0,-3.5 -3.58,-4 -8,-4s-8,0.5 -8,4v10z"
    "M7.5,17c-0.83,0 -1.5,-0.67 -1.5,-1.5S6.67,14 7.5,14s1.5,0.67 1.5,1.5S8.33,17 7.5,17z"
    "M16.5,17c-0.83,0 -1.5,-0.67 -1.5,-1.5s0.67,-1.5 1.5,-1.5 1.5,0.67 1.5,1.5"
    " -0.67,1.5 -1.5,1.5z"
    "M18,11H6V6h12v5z"
)

# ─── SVG para los PNGs de densidad ───────────────────────────────────────────
# Canvas 1024×1024. El path 24×24 se escala al 60% del canvas:
# scale = (1024 × 0.6) / 24 = 614.4 / 24 = 25.6
# translate = (1024 - 614.4) / 2 = 204.8  → centra el bloque escalado
ICON_SVG_SQUARE = f"""\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <rect width="1024" height="1024" fill="{ACCENT_COLOR}"/>
  <g transform="translate(204.8,204.8) scale(25.6)">
    <path fill="white" d="{BUS_PATH}"/>
  </g>
</svg>
"""

# SVG redondo: mismo icono pero recortado en un círculo con esquinas transparentes.
# El clip-path se aplica en un <g> externo sin transform para que las coordenadas
# del círculo (en el espacio 0-1024) se evalúen correctamente por librsvg/rsvg-convert.
# Si se pusiera clip-path en el <g transform="..."> interno, librsvg interpretaría
# las coordenadas del clip en el espacio local transformado (24×24), dejando solo
# el fondo verde visible.
ICON_SVG_ROUND = f"""\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <defs>
    <clipPath id="circle"><circle cx="512" cy="512" r="512"/></clipPath>
  </defs>
  <g clip-path="url(#circle)">
    <rect width="1024" height="1024" fill="{ACCENT_COLOR}"/>
    <g transform="translate(204.8,204.8) scale(25.6)">
      <path fill="white" d="{BUS_PATH}"/>
    </g>
  </g>
</svg>
"""

# ─── SVG para el icono de la tienda (512×512) ─────────────────────────────────
# Mismo diseño que el icono cuadrado estándar.
ICON_SVG_STORE = ICON_SVG_SQUARE

# ─── Densidades mipmap y tamaños en píxeles ───────────────────────────────────
DENSITIES = {
    "mipmap-mdpi":    48,
    "mipmap-hdpi":    72,
    "mipmap-xhdpi":   96,
    "mipmap-xxhdpi":  144,
    "mipmap-xxxhdpi": 192,
}

# ─── XML del icono adaptativo (background) ────────────────────────────────────
ADAPTIVE_BACKGROUND_XML = f"""\
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
  <path
      android:fillColor="{ACCENT_COLOR}"
      android:pathData="M0,0h108v108h-108z" />
</vector>
"""

# ─── XML del icono adaptativo (foreground) ────────────────────────────────────
# Canvas 108×108. El path 24×24 se escala ×2 y se traslada para centrar
# el contenido del bus (aprox. (4,2)–(20,21)) en el canvas.
# Con scaleX/Y=2 y translateX/Y=30/31: centro efectivo ≈ (54, 54). ✓
ADAPTIVE_FOREGROUND_XML = f"""\
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
  <group
      android:scaleX="2.0"
      android:scaleY="2.0"
      android:translateX="30"
      android:translateY="31">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="{BUS_PATH}" />
  </group>
</vector>
"""


def check_rsvg():
    result = subprocess.run(["which", "rsvg-convert"], capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: rsvg-convert no encontrado.")
        print("Instálalo con: brew install librsvg")
        sys.exit(1)


def generate_pngs():
    print("\nGenerando PNGs para cada densidad:")

    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
        f.write(ICON_SVG_SQUARE)
        svg_square = Path(f.name)
    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
        f.write(ICON_SVG_ROUND)
        svg_round = Path(f.name)

    try:
        for density, size in DENSITIES.items():
            out_dir = ANDROID_RES / density
            out_dir.mkdir(exist_ok=True)
            for name, svg_path in (
                ("ic_launcher.png", svg_square),
                ("ic_launcher_round.png", svg_round),
            ):
                out_path = out_dir / name
                # Elimina la versión .webp preexistente si existe
                webp_path = out_dir / name.replace(".png", ".webp")
                if webp_path.exists():
                    webp_path.unlink()
                subprocess.run(
                    ["rsvg-convert", "-w", str(size), "-h", str(size),
                     str(svg_path), "-o", str(out_path)],
                    check=True,
                )
                print(f"  {out_path.relative_to(REPO_ROOT)}")
    finally:
        svg_square.unlink(missing_ok=True)
        svg_round.unlink(missing_ok=True)


def update_adaptive_background():
    bg_path = ANDROID_RES / "drawable" / "ic_launcher_background.xml"
    bg_path.write_text(ADAPTIVE_BACKGROUND_XML)
    print(f"  {bg_path.relative_to(REPO_ROOT)}")


def update_adaptive_foreground():
    fg_path = ANDROID_RES / "drawable-v24" / "ic_launcher_foreground.xml"
    fg_path.write_text(ADAPTIVE_FOREGROUND_XML)
    print(f"  {fg_path.relative_to(REPO_ROOT)}")


def generate_store_icon():
    """Genera el icono 512×512 para la tienda (Google Play) en busgasteiz/temp/."""
    temp_dir = REPO_ROOT / "temp"
    temp_dir.mkdir(exist_ok=True)
    out_path = temp_dir / "ic_play_store_512.png"

    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
        f.write(ICON_SVG_STORE)
        svg_path = Path(f.name)
    try:
        subprocess.run(
            ["rsvg-convert", "-w", "512", "-h", "512", str(svg_path), "-o", str(out_path)],
            check=True,
        )
    finally:
        svg_path.unlink(missing_ok=True)

    print(f"  {out_path.relative_to(REPO_ROOT)}")


def main():
    check_rsvg()
    print("Generando iconos de la aplicación Android BusGasteiz...")

    print("\nActualizando icono adaptativo (background):")
    update_adaptive_background()

    print("\nActualizando icono adaptativo (foreground):")
    update_adaptive_foreground()

    generate_pngs()

    print("\nGenerando icono para Google Play Store (512×512):")
    generate_store_icon()

    print("\n✓ Iconos generados correctamente.")


if __name__ == "__main__":
    main()
