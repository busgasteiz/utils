# AGENTS.md — Utilidades BusGasteiz

Repositorio de utilidades diversas de desarrollo para el proyecto BusGasteiz.

---

## Estructura del repositorio

```
utils/
├── README.md                     # Descripción mínima del repositorio
├── frame_screenshots.sh          # Composita los screenshots de la app en los frames de dispositivo
├── gen_icon.swift                 # Genera el icono de la app iOS en múltiples resoluciones
├── gen_icon_android.py           # Genera el icono de la app Android en todas las densidades mipmap
├── reset_simulators.sh           # Resetea todos los simuladores de iOS a su estado de fábrica
├── set_simulator_statusbar.sh    # Configura la barra de estado del simulador (hora, batería, señal)
└── frames/                       # Frames de dispositivos para los screenshots del App Store
    ├── iPad Pro (M5) 13" - Space Black - Landscape.psd
    ├── iPad Pro (M5) 13" - Space Black - Portrait.psd
    ├── iPhone 17 Pro - Cosmic Orange - Landscape.psd
    ├── iPhone 17 Pro - Cosmic Orange - Portrait.psd
    ├── iPhone 17 Pro Max - Deep Blue - Landscape.psd
    └── iPhone 17 Pro Max - Deep Blue - Portrait.psd
```

---

## Scripts

### `frame_screenshots.sh`

Composita los screenshots de la aplicación sobre los frames `.psd` de la carpeta `frames/` para
generar las imágenes de presentación del App Store. Requiere que los screenshots estén exportados
previamente desde el simulador o dispositivo.

### `gen_icon.swift`

Script Swift que genera el icono de la **aplicación iOS** en todas las resoluciones necesarias para el
App Store y el proyecto Xcode, usando el SF Symbol `bus.fill` en blanco sobre fondo verde `#60A589`.

Uso:
```bash
swift gen_icon.swift
```

### `gen_icon_android.py`

Script Python que genera el icono de la **aplicación Android** en todas las densidades mipmap,
usando el símbolo `directions_bus` de Material Design en blanco sobre fondo verde `#60A589`.

Genera:
- `ic_launcher_background.xml` — vector de fondo sólido para el icono adaptativo.
- `ic_launcher_foreground.xml` — vector del bus para el icono adaptativo.
- `ic_launcher.png` / `ic_launcher_round.png` en `mipmap-mdpi` → `mipmap-xxxhdpi`.
- `busgasteiz/temp/ic_play_store_512.png` — icono 512×512 para Google Play Store
  (autobús un 25 % más grande que en los iconos de app).

Requisitos: `rsvg-convert` (`brew install librsvg`).

```bash
python3 gen_icon_android.py
```

> ⚠️ El clip circular de `ic_launcher_round.png` se aplica en un `<g>` **externo sin transform**.
> Si se pone `clip-path` en el `<g transform="...">` del bus, `librsvg` evalúa las coordenadas del
> clip en el espacio local transformado (24×24) y recorta el bus fuera de la vista.

### `reset_simulators.sh`

Resetea todos los simuladores de iOS al estado de fábrica (borra datos y ajustes). Útil para
reproducir el comportamiento de primera instalación o limpiar estado corrupto.

### `set_simulator_statusbar.sh`

Configura la barra de estado del simulador activo con valores fijos (hora 9:41, batería al 100 %,
señal completa) para obtener screenshots limpios y consistentes para el App Store.

---

## Recursos — `frames/`

Ficheros Photoshop (`.psd`) con los frames de dispositivo usados para los screenshots del App Store.
Los modelos disponibles son:

| Dispositivo                    | Orientaciones         |
|--------------------------------|-----------------------|
| iPhone 17 Pro (Cosmic Orange)  | Portrait + Landscape  |
| iPhone 17 Pro Max (Deep Blue)  | Portrait + Landscape  |
| iPad Pro M5 13" (Space Black)  | Portrait + Landscape  |

---

## Instrucciones para agentes

- Este repositorio contiene **solo utilidades de desarrollo**; no forma parte del código de la app.
- Los scripts están escritos en **Bash**, **Swift** o **Python** según convenga.
- No añadir dependencias externas; los scripts deben funcionar con las herramientas estándar de macOS,
  Xcode y los paquetes disponibles vía `brew`.
