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
# Canvas 1024×1024. El path 24×24 se escala ×42.67 (60% del canvas) y se centra.
# translate(204.8, 204.8): centra el cuadrado 24×42.67 = 614.4 en 1024 → (1024-614.4)/2=204.8
ICON_SVG = f"""\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <rect width="1024" height="1024" fill="{ACCENT_COLOR}"/>
  <g transform="translate(204.8,204.8) scale(42.6667)">
    <path fill="white" d="{BUS_PATH}"/>
  </g>
</svg>
"""

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


def generate_pngs(svg_path: Path):
    print("\nGenerando PNGs para cada densidad:")
    for density, size in DENSITIES.items():
        out_dir = ANDROID_RES / density
        out_dir.mkdir(exist_ok=True)
        for name in ("ic_launcher.png", "ic_launcher_round.png"):
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


def update_adaptive_background():
    bg_path = ANDROID_RES / "drawable" / "ic_launcher_background.xml"
    bg_path.write_text(ADAPTIVE_BACKGROUND_XML)
    print(f"  {bg_path.relative_to(REPO_ROOT)}")


def update_adaptive_foreground():
    fg_path = ANDROID_RES / "drawable-v24" / "ic_launcher_foreground.xml"
    fg_path.write_text(ADAPTIVE_FOREGROUND_XML)
    print(f"  {fg_path.relative_to(REPO_ROOT)}")


def main():
    check_rsvg()
    print("Generando iconos de la aplicación Android BusGasteiz...")

    with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
        f.write(ICON_SVG)
        svg_path = Path(f.name)

    try:
        print("\nActualizando icono adaptativo (background):")
        update_adaptive_background()

        print("\nActualizando icono adaptativo (foreground):")
        update_adaptive_foreground()

        generate_pngs(svg_path)
    finally:
        svg_path.unlink(missing_ok=True)

    print("\n✓ Iconos generados correctamente.")


if __name__ == "__main__":
    main()
