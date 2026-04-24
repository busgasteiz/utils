#!/usr/bin/env python3
"""
Genera un fichero GPX para simular un usuario montado en un bus de la
línea 3 de Vitoria-Gasteiz descargando los datos GTFS actualizados de Tuvisa.

El GPX sigue el recorrido real de la forma (shape) del viaje, con
timestamps calculados a partir de los horarios programados. Xcode puede
reproducirlo en el simulador de iOS para probar la feature "En el bus".

Uso:
    python3 gen_line3_gpx.py [--output <path>] [--trip <trip_id>]
                             [--gtfs-url <url>]

Por defecto escribe el GPX en:
    ../ios/BusGasteiz/Simulations/line3_bus_ride.gpx

Cómo usarlo en Xcode:
    Product → Scheme → Edit Scheme → Run → Options → Default Location
    → Add GPX File to Workspace → seleccionar el .gpx generado
"""

import argparse
import csv
import io
import math
import os
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "..", "ios", "BusGasteiz",
                           "Simulations", "line3_bus_ride.gpx")

GTFS_URL         = "https://www.vitoria-gasteiz.org/we001/http/vgTransit/google_transit.zip"
ROUTE_SHORT_NAME = "3"
PREFERRED_TRIP   = "L3S1_001-LAB"   # laborables, sentido Goikolarra/Durana

# ──────────────────────────────────────────────────────────────────────────────
# Geometría
# ──────────────────────────────────────────────────────────────────────────────

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos puntos GPS."""
    R = 6_371_000
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p)
         * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

# ──────────────────────────────────────────────────────────────────────────────
# Utilidades de tiempo
# ──────────────────────────────────────────────────────────────────────────────

def time_to_secs(t: str) -> int:
    """Convierte HH:MM:SS (puede superar las 24 h) a segundos."""
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s

def secs_to_iso(base: datetime, secs: float) -> str:
    """Timestamp ISO 8601 para base + secs."""
    return (base + timedelta(seconds=secs)).strftime("%Y-%m-%dT%H:%M:%SZ")

# ──────────────────────────────────────────────────────────────────────────────
# Descarga y acceso al ZIP GTFS
# ──────────────────────────────────────────────────────────────────────────────

def download_gtfs(url: str) -> zipfile.ZipFile:
    """Descarga el ZIP GTFS y lo devuelve como ZipFile en memoria."""
    print(f"Descargando GTFS: {url}")
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    print(f"  {len(data) / 1024:.0f} KB descargados")
    return zipfile.ZipFile(io.BytesIO(data))

def read_csv(zf: zipfile.ZipFile, name: str):
    """Devuelve un DictReader sobre el fichero <name> del ZIP."""
    with zf.open(name) as f:
        text = io.TextIOWrapper(f, encoding="utf-8")
        return list(csv.DictReader(text))

# ──────────────────────────────────────────────────────────────────────────────
# Carga de datos GTFS
# ──────────────────────────────────────────────────────────────────────────────

def load_stops(zf: zipfile.ZipFile) -> dict[str, tuple[float, float]]:
    return {
        row["stop_id"]: (float(row["stop_lat"]), float(row["stop_lon"]))
        for row in read_csv(zf, "stops.txt")
    }

def find_trip_and_shape(zf: zipfile.ZipFile,
                        route_short: str,
                        preferred_trip: str) -> tuple[str, str]:
    route_id = None
    for row in read_csv(zf, "routes.txt"):
        if row["route_short_name"] == route_short:
            route_id = row["route_id"]
            break
    if not route_id:
        sys.exit(f"No se encontró la ruta con short_name={route_short!r}")

    trip_id = shape_id = None
    for row in read_csv(zf, "trips.txt"):
        if row["route_id"] != route_id:
            continue
        if row["trip_id"] == preferred_trip:
            return preferred_trip, row["shape_id"]
        if trip_id is None:
            trip_id, shape_id = row["trip_id"], row["shape_id"]

    if not trip_id:
        sys.exit(f"No se encontró ningún viaje para la ruta {route_short!r}")
    return trip_id, shape_id

def load_stop_times(zf: zipfile.ZipFile, trip_id: str) -> list[dict]:
    rows = [r for r in read_csv(zf, "stop_times.txt") if r["trip_id"] == trip_id]
    rows.sort(key=lambda r: int(r["stop_sequence"]))
    return rows

def load_shape(zf: zipfile.ZipFile,
               shape_id: str) -> list[tuple[int, float, float, float]]:
    """Devuelve lista de (seq, lat, lon, dist_traveled) ordenada por seq."""
    points = [
        (int(r["shape_pt_sequence"]),
         float(r["shape_pt_lat"]),
         float(r["shape_pt_lon"]),
         float(r["shape_dist_traveled"]))
        for r in read_csv(zf, "shapes.txt")
        if r["shape_id"] == shape_id
    ]
    points.sort(key=lambda r: r[0])
    return points

# ──────────────────────────────────────────────────────────────────────────────
# Interpolación de timestamps
# ──────────────────────────────────────────────────────────────────────────────

def nearest_shape_idx(shape: list, lat: float, lon: float,
                      min_idx: int = 0) -> int:
    """Índice del punto de forma más cercano a (lat, lon), a partir de min_idx."""
    min_idx = min(min_idx, len(shape) - 1)
    best_i, best_d = min_idx, float("inf")
    for i in range(min_idx, len(shape)):
        d = haversine(lat, lon, shape[i][1], shape[i][2])
        if d < best_d:
            best_d, best_i = d, i
    return best_i

def assign_timestamps(shape: list,
                      stop_times: list[dict],
                      stops: dict) -> list[tuple[float, float, float]]:
    """
    Asigna un timestamp (en segundos desde medianoche) a cada punto de la
    forma interpolando linealmente (por distancia acumulada) entre paradas
    consecutivas del horario.

    Devuelve lista de (lat, lon, t_secs).
    """
    # Proyectar cada parada al punto de forma más cercano de forma monótona
    ctrl: dict[int, float] = {}
    min_idx = 0
    for row in stop_times:
        sid = row["stop_id"]
        if sid not in stops:
            continue
        lat, lon = stops[sid]
        idx = nearest_shape_idx(shape, lat, lon, min_idx)
        ctrl[idx] = time_to_secs(row["arrival_time"])
        min_idx = idx + 1

    ctrl_sorted = sorted(ctrl.items())
    if len(ctrl_sorted) < 2:
        sys.exit("No hay suficientes paradas mapeadas a la forma.")

    n     = len(shape)
    times = [None] * n

    # Interpolación entre puntos de control
    for seg in range(len(ctrl_sorted) - 1):
        i0, t0 = ctrl_sorted[seg]
        i1, t1 = ctrl_sorted[seg + 1]
        if i1 <= i0:
            times[i0] = t0
            continue

        seg_pts = shape[i0 : i1 + 1]
        cum = [0.0]
        for k in range(1, len(seg_pts)):
            d = haversine(seg_pts[k-1][1], seg_pts[k-1][2],
                          seg_pts[k][1],   seg_pts[k][2])
            cum.append(cum[-1] + d)
        total = cum[-1]

        for k, gi in enumerate(range(i0, i1 + 1)):
            frac = (cum[k] / total) if total > 0 else (k / max(1, len(seg_pts) - 1))
            times[gi] = t0 + frac * (t1 - t0)

    # Extender antes del primer punto de control (velocidad del primer tramo)
    fi, ft = ctrl_sorted[0]
    li, lt = ctrl_sorted[1]
    total_d = sum(
        haversine(shape[k][1], shape[k][2], shape[k+1][1], shape[k+1][2])
        for k in range(fi, li)
    )
    speed = total_d / max(1, lt - ft)
    for gi in range(fi - 1, -1, -1):
        d = haversine(shape[gi][1], shape[gi][2], shape[gi+1][1], shape[gi+1][2])
        times[gi] = times[gi + 1] - (d / speed if speed > 0 else 1)

    # Extender después del último punto de control
    li, lt = ctrl_sorted[-1]
    pi, pt = ctrl_sorted[-2]
    total_d = sum(
        haversine(shape[k][1], shape[k][2], shape[k+1][1], shape[k+1][2])
        for k in range(pi, li)
    )
    speed = total_d / max(1, lt - pt)
    for gi in range(li + 1, n):
        d = haversine(shape[gi-1][1], shape[gi-1][2], shape[gi][1], shape[gi][2])
        times[gi] = times[gi - 1] + (d / speed if speed > 0 else 1)

    return [(shape[i][1], shape[i][2], times[i]) for i in range(n)]

# ──────────────────────────────────────────────────────────────────────────────
# Generación del GPX
# ──────────────────────────────────────────────────────────────────────────────

def generate_gpx(waypoints: list[tuple[float, float, float]],
                 base_dt:   datetime,
                 out_path:  str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="gen_line3_gpx"',
        '     xmlns="http://www.topografix.com/GPX/1/1">',
        '  <!-- Simulación: bus línea 3 Vitoria-Gasteiz (Betoño → Goikolarra) -->',
        '  <!-- Horario laborables, primer servicio (06:45 h)                  -->',
    ]
    for lat, lon, t in waypoints:
        ts = secs_to_iso(base_dt, t)
        lines += [
            f'  <wpt lat="{lat:.6f}" lon="{lon:.6f}">',
            f'    <time>{ts}</time>',
            f'  </wpt>',
        ]
    lines.append('</gpx>')
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✓ GPX escrito en: {out_path}")
    print(f"  Waypoints: {len(waypoints)}")

# ──────────────────────────────────────────────────────────────────────────────
# Punto de entrada
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--gtfs-url", default=GTFS_URL,
                        help="URL del ZIP GTFS de Tuvisa")
    parser.add_argument("--output",   default=DEFAULT_OUT,
                        help="Ruta del fichero GPX a generar")
    parser.add_argument("--trip",     default=PREFERRED_TRIP,
                        help="trip_id a usar (por defecto: L3S1_001-LAB)")
    args = parser.parse_args()

    out_path = os.path.realpath(args.output)

    zf = download_gtfs(args.gtfs_url)

    trip_id, shape_id = find_trip_and_shape(zf, ROUTE_SHORT_NAME, args.trip)
    print(f"Viaje: {trip_id}  |  Forma: {shape_id}")

    stops      = load_stops(zf)
    stop_times = load_stop_times(zf, trip_id)
    shape      = load_shape(zf, shape_id)

    print(f"Paradas del viaje: {len(stop_times)}  |  Puntos de forma: {len(shape)}")

    waypoints = assign_timestamps(shape, stop_times, stops)

    # La fecha base es 2025-01-15 a medianoche UTC.
    # El primer waypoint corresponde a las 06:45 (hora Madrid = 05:45 UTC en invierno).
    # Xcode solo usa las diferencias entre timestamps, así que la fecha absoluta
    # no afecta a la simulación.
    base_dt = datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc)

    generate_gpx(waypoints, base_dt, out_path)

    print()
    print("Cómo añadirlo a Xcode:")
    print("  1. Xcode → Product → Scheme → Edit Scheme")
    print("  2. Run → Options → Default Location")
    print("  3. Add GPX File to Workspace… → seleccionar el .gpx generado")

if __name__ == "__main__":
    main()

