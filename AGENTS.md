# AGENTS.md — Utilidades BusGasteiz

Repositorio de utilidades diversas de desarrollo para el proyecto BusGasteiz.

---

## Estructura del repositorio

```
utils/
├── README.md                     # Descripción mínima del repositorio
├── frame_screenshots.sh          # Composita los screenshots de la app en los frames de dispositivo
├── gen_icon.swift                 # Genera el icono de la app en múltiples resoluciones
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

Script Swift que genera el icono de la aplicación en todas las resoluciones necesarias para el
App Store y el proyecto Xcode a partir de una imagen fuente de alta resolución.

Uso:
```bash
swift gen_icon.swift
```

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
- Los scripts están escritos en **Bash** o **Swift** según convenga.
- No añadir dependencias externas; los scripts deben funcionar con las herramientas estándar de macOS
  y Xcode.
