# Reto Ecobici — Smart Bicycle Redistribution under Uncertainty
MA2004B Optimización Estocástica · Equipo 4 · Subred Polanco (10 estaciones), días hábiles de septiembre 2026

## Instalación
    python3 -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    pip install -r requirements.txt

## Reproducir
Los datos crudos no se incluyen por tamaño. Descargar:
- `public_data_web_2026-09.csv` — https://ecobici.cdmx.gob.mx/datos-abiertos/
- `station_information.json` — https://gbfs.mex.lyftbikes.com/gbfs/en/station_information.json

Desde los crudos:

    python scripts/limpieza.py --csv public_data_web_2026-09.csv --gbfs station_information.json --out out
    python scripts/subred.py --limpios out/viajes_limpios.csv --estaciones out/estaciones.csv --out out/polanco
    python scripts/modelo.py --limpios out/viajes_limpios.csv --estaciones out/estaciones.csv --out out/modelo

Atajo con el CSV limpio incluido (`datos/viajes_limpios.csv.gz`, 1,173,180 viajes):

    python scripts/subred.py --limpios datos/viajes_limpios.csv.gz --estaciones datos/estaciones.csv --out out/polanco
    python scripts/modelo.py --limpios datos/viajes_limpios.csv.gz --estaciones datos/estaciones.csv --out out/modelo

## Contenido
| Carpeta | Qué hay |
|---|---|
| `scripts/` | `limpieza.py` (reglas R1–R10), `subred.py` (Etapa 1), `modelo.py` (Etapa 2) |
| `datos/` | Catálogo GBFS, viajes limpios, tabla de la subred, reporte de limpieza |
| `out/polanco/` | Figuras de la Etapa 1: mapa, deriva acumulada, variabilidad diaria |
| `out/modelo/` | Salidas de la Etapa 2: tasas cada 15 min, pruebas de supuestos, censura, operador actual, fallas vs. inventario |
| `docs/` | Parte 1 (PDF) y documento de la Etapa 2 |
| `notebooks/` | Notebook de la Etapa 2 |

## Etapas
1. Datos y análisis exploratorio ✅
2. Modelo estocástico (nacimiento y muerte, Poisson no homogéneo, Kolmogorov) ✅
3. Análisis de servicio y optimización ⏳
4. Simulación y comparación de estrategias ⏳
5. Impacto y conclusiones ⏳
