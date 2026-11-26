#!/usr/bin/env python3
"""
Limpieza de viajes Ecobici (Etapa 1 - MA2004B).

Uso:
    python limpieza.py --csv public_data_web_2026-09.csv \
                       --gbfs station_information.json \
                       --out ./out

Aplica las reglas de limpieza en orden, registra cuántos registros descarta
cada una y escribe:
    out/viajes_limpios.csv      viajes que sobreviven todas las reglas
    out/viajes_descartados.csv  viajes eliminados, con la regla que los eliminó
    out/estaciones.csv          catálogo GBFS (código, nombre, lat, lon, capacidad)
    out/reporte_limpieza.md     tabla de descartes por regla + resumen por día

Las reglas y umbrales están en la sección CONFIG; cada decisión está comentada
para poder defenderla en la Activity 1.
"""
import argparse
import json
from datetime import date, timedelta

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
# Horario de operación de Ecobici: 05:00 a 00:30 del día siguiente.
# Un viaje pertenece al "día de servicio" del día en que se retiró la bici;
# los retiros entre 00:00 y 00:30 se asignan al día anterior.
APERTURA_MIN = 5 * 60          # 05:00  -> minutos desde medianoche
CIERRE_MIN = 24 * 60 + 30      # 00:30 del día siguiente, en minutos del día de servicio

DUR_MIN_MINUTOS = 2            # viajes más cortos que esto se descartan (cualquier par de estaciones)
DUR_MISMA_EST_MINUTOS = 5      # viajes que inician y terminan en la misma estación con menos de esto: reenganche
DUR_MAX_MINUTOS = 180          # viajes más largos que esto: olvido / robo / falla de registro

# Días de asueto oficiales (Ley Federal del Trabajo, art. 74) y otros días que
# distorsionan la demanda de un día laboral típico. Se agregan por mes analizado.
FESTIVOS_OFICIALES = {
    date(2026, 9, 16): "Día de la Independencia (asueto oficial LFT)",
}
# Días atípicos que NO se eliminan por default pero se marcan en la columna
# `dia_atipico` para poder excluirlos después si el EDA lo justifica.
DIAS_ATIPICOS = {
    date(2026, 9, 15): "Víspera del Grito: oficinas de gobierno con jornada reducida",
    date(2026, 9, 25): "Consejo Técnico Escolar SEP (sin clases en básica)",
}
# Periodos vacacionales escolares (SEP) que caen dentro del mes analizado.
# Ciclo 2026-2027: clases inician 31/08/2026; no hay vacaciones en septiembre.
VACACIONES = []  # lista de (inicio, fin) inclusivos, p. ej. (date(2026,12,21), date(2027,1,8))


# ----------------------------------------------------------------------------
def haversine_km(lat0, lon0, lat1, lon1):
    p = np.pi / 180
    a = (np.sin((lat1 - lat0) * p / 2) ** 2
         + np.cos(lat0 * p) * np.cos(lat1 * p) * np.sin((lon1 - lon0) * p / 2) ** 2)
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def cargar_estaciones(path):
    with open(path) as f:
        st = json.load(f)["data"]["stations"]
    est = pd.DataFrame(st)[["short_name", "station_id", "name", "lat", "lon", "capacity"]]
    est = est.rename(columns={"short_name": "codigo", "name": "nombre", "capacity": "capacidad"})
    # El CSV de viajes usa el código corto ("028", "710", "235-236"); lo dejamos como texto.
    est["codigo"] = est["codigo"].astype(str)
    return est.set_index("codigo")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--gbfs", required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--anio", type=int, default=None, help="año del archivo (default: se infiere de Fecha_Arribo)")
    ap.add_argument("--mes", type=int, default=None, help="mes del archivo (default: se infiere de Fecha_Arribo)")
    args = ap.parse_args()

    import os
    os.makedirs(args.out, exist_ok=True)

    # ---------------- carga ----------------
    df = pd.read_csv(args.csv, dtype=str)
    n0 = len(df)
    df["t0"] = pd.to_datetime(df["Fecha_Retiro"] + " " + df["Hora_Retiro"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df["t1"] = pd.to_datetime(df["Fecha_Arribo"] + " " + df["Hora_Arribo"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df["dur_min"] = (df["t1"] - df["t0"]).dt.total_seconds() / 60

    # El archivo mensual se arma por fecha de ARRIBO; el periodo de análisis es ese mes.
    moda = df["t1"].dt.to_period("M").mode()[0]
    anio = args.anio or moda.year
    mes = args.mes or moda.month
    inicio_mes = pd.Timestamp(anio, mes, 1)
    fin_mes = (inicio_mes + pd.offsets.MonthEnd(1)).normalize()

    est = cargar_estaciones(args.gbfs)

    # ---------------- variables derivadas ----------------
    # minutos desde medianoche del retiro; si es antes de las 05:00, pertenece al día de servicio anterior
    min_dia = df["t0"].dt.hour * 60 + df["t0"].dt.minute
    antes_apertura = min_dia < APERTURA_MIN
    df["min_servicio"] = np.where(antes_apertura, min_dia + 24 * 60, min_dia)
    df["fecha_servicio"] = (df["t0"] - pd.to_timedelta(antes_apertura.astype(int), unit="D")).dt.date
    df["dia_semana"] = pd.to_datetime(df["fecha_servicio"]).dt.dayofweek  # 0=lunes ... 6=domingo
    df["hora_retiro"] = df["t0"].dt.hour
    df["hora_arribo"] = df["t1"].dt.hour
    df["misma_estacion"] = df["Ciclo_Estacion_Retiro"] == df["Ciclo_EstacionArribo"]

    for lado, col in [("retiro", "Ciclo_Estacion_Retiro"), ("arribo", "Ciclo_EstacionArribo")]:
        df[f"lat_{lado}"] = df[col].map(est["lat"])
        df[f"lon_{lado}"] = df[col].map(est["lon"])
    df["dist_km"] = haversine_km(df["lat_retiro"], df["lon_retiro"], df["lat_arribo"], df["lon_arribo"])
    df["vel_kmh"] = df["dist_km"] / (df["dur_min"] / 60)

    fechas_vac = set()
    for a, b in VACACIONES:
        d = a
        while d <= b:
            fechas_vac.add(d)
            d += timedelta(days=1)

    df["dia_atipico"] = df["fecha_servicio"].map(lambda d: DIAS_ATIPICOS.get(d, ""))

    # ---------------- reglas (en orden) ----------------
    # Cada regla: (nombre, máscara de lo que se DESCARTA, justificación)
    reglas = [
        ("R0_fecha_invalida",
         df["t0"].isna() | df["t1"].isna(),
         "Fecha u hora que no se pudo interpretar."),
        ("R1_fuera_del_mes",
         (pd.to_datetime(df["fecha_servicio"]) < inicio_mes) | (pd.to_datetime(df["fecha_servicio"]) > fin_mes),
         f"Día de servicio fuera de {inicio_mes:%Y-%m}: el archivo se arma por fecha de arribo e incluye viajes "
         "iniciados en meses anteriores (algunos con duración de días o meses) y los retiros de las 00:00–00:30 "
         "del día 1, que pertenecen al último día de servicio del mes anterior."),
        ("R2_duracion_no_positiva",
         df["dur_min"] <= 0,
         "Arribo anterior o igual al retiro."),
        ("R3_reenganche_misma_estacion",
         df["misma_estacion"] & (df["dur_min"] < DUR_MISMA_EST_MINUTOS),
         f"Retiro y arribo en la misma estación en menos de {DUR_MISMA_EST_MINUTOS} min: bici defectuosa "
         "devuelta de inmediato o reenganche; no es un viaje."),
        ("R4_viaje_muy_corto",
         df["dur_min"] < DUR_MIN_MINUTOS,
         f"Duración menor a {DUR_MIN_MINUTOS} min hacia otra estación (mediana ~290 m a la estación vecina): "
         "cambio de bici o anclaje en la estación contigua, no un desplazamiento."),
        ("R5_viaje_muy_largo",
         df["dur_min"] > DUR_MAX_MINUTOS,
         f"Duración mayor a {DUR_MAX_MINUTOS} min (3 h): olvido de anclaje, robo o falla de registro. "
         "El sistema cobra penalización desde los 45 min; el percentil 99.9 de duración es ~110 min."),
        ("R6_estacion_no_en_gbfs",
         df["lat_retiro"].isna() | df["lat_arribo"].isna(),
         "Código de estación que no existe en station_information.json (estación cerrada o renombrada)."),
        ("R7_fin_de_semana",
         df["dia_semana"] >= 5,
         "Sábado o domingo (por día de servicio). El alcance del proyecto es días hábiles."),
        ("R8_festivo_oficial",
         df["fecha_servicio"].isin(FESTIVOS_OFICIALES.keys()),
         "Día de asueto oficial: " + "; ".join(f"{d:%d/%m}: {v}" for d, v in FESTIVOS_OFICIALES.items())),
        ("R9_vacaciones_escolares",
         df["fecha_servicio"].isin(fechas_vac),
         "Periodo vacacional escolar SEP dentro del mes." if fechas_vac else
         "Periodo vacacional escolar SEP dentro del mes (ninguno en este mes)."),
        ("R10_fuera_horario_operacion",
         (df["min_servicio"] < APERTURA_MIN) | (df["min_servicio"] >= CIERRE_MIN),
         "Retiro fuera del horario de operación (05:00–00:30)."),
    ]

    df["regla_descarte"] = ""
    vivo = pd.Series(True, index=df.index)
    filas = []
    for nombre, mask, just in reglas:
        mask = mask.fillna(False)
        aislado = int(mask.sum())                 # cuántos cumplen la regla en el archivo original
        secuencial = int((mask & vivo).sum())     # cuántos elimina dado lo ya eliminado
        df.loc[mask & vivo, "regla_descarte"] = nombre
        vivo &= ~mask
        filas.append((nombre, aislado, secuencial, int(vivo.sum()), just))

    limpio = df[vivo].copy()
    descartado = df[~vivo].copy()

    # ---------------- salidas ----------------
    cols_out = ["Genero_Usuario", "Edad_Usuario", "Bici",
                "Ciclo_Estacion_Retiro", "t0", "Ciclo_EstacionArribo", "t1",
                "dur_min", "dist_km", "vel_kmh", "misma_estacion",
                "fecha_servicio", "dia_semana", "hora_retiro", "hora_arribo", "dia_atipico"]
    limpio[cols_out].rename(columns={"t0": "ts_retiro", "t1": "ts_arribo"}) \
        .to_csv(f"{args.out}/viajes_limpios.csv", index=False, float_format="%.4f")
    descartado[cols_out + ["regla_descarte"]].rename(columns={"t0": "ts_retiro", "t1": "ts_arribo"}) \
        .to_csv(f"{args.out}/viajes_descartados.csv", index=False, float_format="%.4f")

    usadas = set(limpio["Ciclo_Estacion_Retiro"]) | set(limpio["Ciclo_EstacionArribo"])
    est_out = est.reset_index()
    est_out["con_viajes_en_mes"] = est_out["codigo"].isin(usadas)
    est_out.to_csv(f"{args.out}/estaciones.csv", index=False)

    # ---------------- reporte ----------------
    tabla = pd.DataFrame(filas, columns=["regla", "cumplen_regla", "eliminados", "quedan", "justificacion"])
    por_dia = (df.assign(estado=np.where(vivo, "conservado", "descartado"))
                 .groupby(["fecha_servicio", "estado"]).size().unstack(fill_value=0))
    por_dia["dia"] = pd.to_datetime(por_dia.index).strftime("%a")
    por_dia = por_dia[["dia"] + [c for c in ["conservado", "descartado"] if c in por_dia]]

    with open(f"{args.out}/reporte_limpieza.md", "w") as f:
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                 "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        f.write(f"# Reporte de limpieza — Ecobici {meses[mes-1]} {anio}\n\n")
        f.write(f"Archivo: `{os.path.basename(args.csv)}` — {n0:,} registros.  \n")
        f.write(f"Catálogo GBFS: `{os.path.basename(args.gbfs)}` — {len(est):,} estaciones.  \n")
        f.write(f"**Conservados: {len(limpio):,} ({len(limpio)/n0:.1%}) — Descartados: {len(descartado):,} ({len(descartado)/n0:.1%})**\n\n")
        f.write("## Reglas aplicadas (en orden)\n\n")
        f.write("`cumplen_regla` = registros del archivo original que cumplen la condición; "
                "`eliminados` = los que efectivamente elimina esa regla después de las anteriores.\n\n")
        f.write("| # | Regla | Cumplen | Eliminados | Quedan | Justificación |\n|---|---|---:|---:|---:|---|\n")
        for i, r in tabla.iterrows():
            f.write(f"| {i} | `{r.regla}` | {r.cumplen_regla:,} | {r.eliminados:,} | {r.quedan:,} | {r.justificacion} |\n")
        f.write("\n## Parámetros\n\n")
        f.write(f"- Horario de operación: {APERTURA_MIN//60:02d}:{APERTURA_MIN%60:02d}–"
                f"{(CIERRE_MIN%1440)//60:02d}:{CIERRE_MIN%60:02d} (día de servicio por hora de retiro)\n")
        f.write(f"- Duración mínima: {DUR_MIN_MINUTOS} min; misma estación: {DUR_MISMA_EST_MINUTOS} min; máxima: {DUR_MAX_MINUTOS} min\n")
        f.write(f"- Festivos eliminados: {', '.join(f'{d:%d/%m/%Y}' for d in FESTIVOS_OFICIALES) or 'ninguno'}\n")
        f.write(f"- Vacaciones eliminadas: {', '.join(f'{a:%d/%m}–{b:%d/%m}' for a, b in VACACIONES) or 'ninguna en el mes'}\n")
        f.write("- Días atípicos marcados en `dia_atipico` pero **conservados**: "
                + ("; ".join(f"{d:%d/%m} ({v})" for d, v in DIAS_ATIPICOS.items()) or "ninguno") + "\n")
        f.write("\n## Registros por día de servicio\n\n")
        f.write(por_dia.to_markdown())
        f.write("\n\n## Notas\n\n")
        f.write("- El archivo mensual está organizado por fecha de **arribo**: contiene viajes que iniciaron el mes anterior "
                "(eliminados por R1) y no contiene los viajes que iniciaron el último día del mes y terminaron después de "
                "medianoche (están en el archivo del mes siguiente). El último día de servicio queda ligeramente censurado "
                "en su cola nocturna.\n")
        f.write("- Los viajes de ida y vuelta a la misma estación con duración ≥ "
                f"{DUR_MISMA_EST_MINUTOS} min se conservan: para el modelo de inventario por estación son un retiro y un arribo reales.\n")
        f.write("- Los códigos dobles tipo `235-236` corresponden a estaciones pareadas que el GBFS publica con ese mismo código.\n")
        f.write(f"- Estaciones del GBFS sin viajes en el mes: {', '.join(sorted(set(est.index) - usadas)) or 'ninguna'}.\n")

    print(tabla[["regla", "cumplen_regla", "eliminados", "quedan"]].to_string(index=False))
    print(f"\nConservados {len(limpio):,} de {n0:,} ({len(limpio)/n0:.1%}). Salidas en {args.out}/")


if __name__ == "__main__":
    main()
