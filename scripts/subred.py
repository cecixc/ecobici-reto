#!/usr/bin/env python3
"""
Ficha de la subred (Etapa 1 - EDA) a partir de viajes_limpios.csv y estaciones.csv.

Uso:
    python subred.py --limpios out/viajes_limpios.csv --estaciones out/estaciones.csv --out out/polanco

Genera:
    viajes_subred.csv          viajes que tocan la subred (retiro o arribo en ella), con banderas
    tabla_estaciones.csv       indicadores por estación
    perfil_horario.csv         retiros y arribos promedio por estación y hora
    od_interna.csv             matriz origen-destino interna (viajes/día)
    fig_*.png                  figuras
    ficha_subred.md            resumen con tablas, listo para el memo
"""
import argparse, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SUBRED = ["211", "212", "208", "204", "210", "217", "207", "205", "201", "225"]
HORAS = list(range(5, 24)) + [0]          # 05 h ... 23 h, 00 h (día de servicio)
AM, PM = [7, 8, 9], [17, 18, 19]

ap = argparse.ArgumentParser()
ap.add_argument("--limpios", required=True)
ap.add_argument("--estaciones", required=True)
ap.add_argument("--out", default="out/polanco")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)

c = pd.read_csv(args.limpios, dtype={"Ciclo_Estacion_Retiro": str, "Ciclo_EstacionArribo": str, "dia_atipico": str},
                parse_dates=["ts_retiro", "ts_arribo"])
est = pd.read_csv(args.estaciones, dtype={"codigo": str}).set_index("codigo")
ndias = c["fecha_servicio"].nunique()

en_ret = c["Ciclo_Estacion_Retiro"].isin(SUBRED)
en_arr = c["Ciclo_EstacionArribo"].isin(SUBRED)
v = c[en_ret | en_arr].copy()
v["tipo"] = np.select([en_ret[v.index] & en_arr[v.index], en_ret[v.index]], ["interno", "sale"], "entra")
v.to_csv(f"{args.out}/viajes_subred.csv", index=False)

# ---------- perfiles horarios ----------
ret = v[v.tipo != "entra"].groupby(["Ciclo_Estacion_Retiro", "hora_retiro"]).size().unstack(fill_value=0)
arr = v[v.tipo != "sale"].groupby(["Ciclo_EstacionArribo", "hora_arribo"]).size().unstack(fill_value=0)
ret = ret.reindex(index=SUBRED, columns=HORAS, fill_value=0) / ndias
arr = arr.reindex(index=SUBRED, columns=HORAS, fill_value=0) / ndias
net = arr - ret
cum = net.cumsum(axis=1)
perfil = pd.concat({"retiros": ret, "arribos": arr}, names=["medida", "codigo"]).round(2)
perfil.to_csv(f"{args.out}/perfil_horario.csv")

# ---------- tabla de estaciones ----------
T = pd.DataFrame(index=SUBRED)
T["nombre"] = est["nombre"].reindex(SUBRED).str.replace(r"^CE-\d+ ", "", regex=True)
T["capacidad"] = est["capacidad"].reindex(SUBRED)
T["retiros_dia"] = ret.sum(axis=1).round(1)
T["arribos_dia"] = arr.sum(axis=1).round(1)
T["neto_7_10h"] = net[AM].sum(axis=1).round(1)
T["neto_17_20h"] = net[PM].sum(axis=1).round(1)
T["deriva_max"] = cum.max(axis=1).round(1)
T["deriva_min"] = cum.min(axis=1).round(1)
T["rango_deriva/cap"] = ((cum.max(axis=1) - cum.min(axis=1)) / T["capacidad"]).round(2)
T["rol"] = np.where(T["neto_7_10h"] < -15, "fuente (se vacía AM)", np.where(T["neto_7_10h"] > 15, "sumidero (se llena AM)", "neutra"))
# variabilidad día a día de los retiros
diario = v[v.tipo != "entra"].groupby(["Ciclo_Estacion_Retiro", "fecha_servicio"]).size().unstack(fill_value=0).reindex(SUBRED)
T["cv_retiros_diarios"] = (diario.std(axis=1) / diario.mean(axis=1)).round(2)
T["lat"] = est["lat"].reindex(SUBRED); T["lon"] = est["lon"].reindex(SUBRED)
T.index.name = "codigo"
T.to_csv(f"{args.out}/tabla_estaciones.csv")

# ---------- OD interna ----------
od = v[v.tipo == "interno"].groupby(["Ciclo_Estacion_Retiro", "Ciclo_EstacionArribo"]).size().unstack(fill_value=0)
od = od.reindex(index=SUBRED, columns=SUBRED, fill_value=0) / ndias
od.round(2).to_csv(f"{args.out}/od_interna.csv")

n_int, n_sale, n_entra = (v.tipo == "interno").sum(), (v.tipo == "sale").sum(), (v.tipo == "entra").sum()
tot = len(v)

# destinos externos principales
dest_ext = v[v.tipo == "sale"]["Ciclo_EstacionArribo"].value_counts().head(8)
orig_ext = v[v.tipo == "entra"]["Ciclo_Estacion_Retiro"].value_counts().head(8)

# ---------- figuras ----------
col_f, col_s, col_n = "#d95f02", "#1b7837", "#777777"
rolcol = {"fuente (se vacía AM)": col_f, "sumidero (se llena AM)": col_s, "neutra": col_n}
etq = {k: f"{k} {T.loc[k,'nombre']}" for k in SUBRED}
xt = list(range(len(HORAS))); xl = [f"{h:02d}" for h in HORAS]

# 1. mapa
fig, ax = plt.subplots(figsize=(7.5, 6), dpi=140)
for k in SUBRED:
    ax.scatter(T.loc[k, "lon"], T.loc[k, "lat"], s=T.loc[k, "capacidad"] * 9, color=rolcol[T.loc[k, "rol"]], alpha=.75, edgecolor="k", lw=.5)
    ax.annotate(k, (T.loc[k, "lon"], T.loc[k, "lat"]), xytext=(6, 6), textcoords="offset points", fontsize=9)
for r, cc in rolcol.items():
    ax.scatter([], [], color=cc, s=80, label=r)
ax.legend(loc="lower right", fontsize=8, title="tamaño = capacidad")
ax.set_title("Subred Polanco: 10 estaciones", fontsize=11); ax.set_xlabel("lon"); ax.set_ylabel("lat"); ax.grid(alpha=.25)
plt.tight_layout(); plt.savefig(f"{args.out}/fig_mapa.png"); plt.close()

# 2. perfiles horarios (small multiples)
fig, axs = plt.subplots(2, 5, figsize=(16, 6), dpi=130, sharex=True)
for ax, k in zip(axs.flat, SUBRED):
    ax.bar(xt, ret.loc[k].values, color="#c0392b", alpha=.7, label="retiros", width=.8)
    ax.bar(xt, -arr.loc[k].values, color="#2980b9", alpha=.7, label="arribos", width=.8)
    ax.axhline(0, color="k", lw=.6)
    ax.set_title(etq[k], fontsize=8.5, color=rolcol[T.loc[k, "rol"]])
    ax.set_xticks(xt[::3]); ax.set_xticklabels(xl[::3], fontsize=7); ax.tick_params(axis="y", labelsize=7)
axs[0, 0].legend(fontsize=7, loc="upper left")
fig.suptitle("Retiros (arriba) y arribos (abajo) promedio por hora, viajes/día hábil — septiembre 2026", fontsize=11)
plt.tight_layout(); plt.savefig(f"{args.out}/fig_perfiles_horarios.png"); plt.close()

# 3. deriva acumulada vs capacidad
fig, axs = plt.subplots(2, 5, figsize=(16, 6), dpi=130, sharex=True)
for ax, k in zip(axs.flat, SUBRED):
    cap = T.loc[k, "capacidad"]
    ax.plot(xt, cum.loc[k].values, color=rolcol[T.loc[k, "rol"]], lw=2)
    ax.axhspan(-cap, 0, color="#2980b9", alpha=.08); ax.axhspan(0, cap, color="#c0392b", alpha=.08)
    ax.axhline(cap, color="#c0392b", ls="--", lw=.8); ax.axhline(-cap, color="#2980b9", ls="--", lw=.8); ax.axhline(0, color="k", lw=.6)
    ax.set_title(etq[k], fontsize=8.5, color=rolcol[T.loc[k, "rol"]])
    ax.set_xticks(xt[::3]); ax.set_xticklabels(xl[::3], fontsize=7); ax.tick_params(axis="y", labelsize=7)
    ax.text(0.02, 0.95, f"cap {cap}", transform=ax.transAxes, fontsize=7, va="top")
fig.suptitle("Deriva acumulada del inventario sin redistribución (arribos − retiros acumulados desde las 05 h) vs ±capacidad.\n"
             "Si la curva cruza la banda, la estación se llenaría (arriba) o vaciaría (abajo) partiendo de cualquier nivel inicial.", fontsize=10)
plt.tight_layout(); plt.savefig(f"{args.out}/fig_deriva_acumulada.png"); plt.close()

# 4. OD heatmap
fig, ax = plt.subplots(figsize=(7.5, 6.5), dpi=140)
im = ax.imshow(od.values, cmap="Blues")
ax.set_xticks(range(10)); ax.set_yticks(range(10)); ax.set_xticklabels(SUBRED, fontsize=8); ax.set_yticklabels(SUBRED, fontsize=8)
ax.set_xlabel("arribo"); ax.set_ylabel("retiro")
for i in range(10):
    for j in range(10):
        if od.values[i, j] >= 0.5:
            ax.text(j, i, f"{od.values[i,j]:.1f}", ha="center", va="center", fontsize=7, color="w" if od.values[i, j] > od.values.max() * .6 else "k")
plt.colorbar(im, ax=ax, shrink=.8, label="viajes/día hábil")
ax.set_title(f"Matriz O–D interna (viajes internos = {n_int/tot*100:.1f}% de los que tocan la subred)", fontsize=10)
plt.tight_layout(); plt.savefig(f"{args.out}/fig_od_interna.png"); plt.close()

# 5. variabilidad diaria
fig, ax = plt.subplots(figsize=(11, 4.5), dpi=130)
ax.boxplot([diario.loc[k].values for k in SUBRED], tick_labels=SUBRED, patch_artist=True,
           boxprops=dict(facecolor="#dddddd"), medianprops=dict(color="k"))
ax.set_ylabel("retiros por día hábil"); ax.set_title("Variabilidad día a día de los retiros por estación (21 días hábiles)", fontsize=10); ax.grid(alpha=.25, axis="y")
plt.tight_layout(); plt.savefig(f"{args.out}/fig_variabilidad_diaria.png"); plt.close()

# ---------- ficha ----------
with open(f"{args.out}/ficha_subred.md", "w") as f:
    f.write("# Subred Polanco — ficha de la Etapa 1\n\n")
    f.write(f"Periodo: {ndias} días hábiles de septiembre 2026 (limpieza en `reporte_limpieza.md`). "
            f"Estaciones: {len(SUBRED)}, capacidad total {int(T.capacidad.sum())} docks. "
            f"Radio máximo entre estaciones ≈ 1.1 km.\n\n")
    f.write(f"Viajes que tocan la subred: **{tot/ndias:,.0f}/día** — internos {n_int/ndias:,.0f} ({n_int/tot*100:.1f}%), "
            f"salen hacia el exterior {n_sale/ndias:,.0f} ({n_sale/tot*100:.1f}%), entran desde el exterior {n_entra/ndias:,.0f} ({n_entra/tot*100:.1f}%).\n\n")
    f.write("## Por qué esta subred\n\n")
    f.write("1. **Contiene las dos fallas del operador en la misma zona.** Cinco estaciones son fuentes matutinas (zona residencial sobre Horacio/Homero: "
            "pierden bicis de 7 a 10 h) y cinco son sumideros (corredor de oficinas Masaryk/Ejército Nacional: se saturan). "
            "La redistribución *dentro* de la subred tiene sentido: hay de dónde sacar y a dónde llevar, a menos de 1 km.\n")
    n_desbal = int((T["rango_deriva/cap"] >= 1).sum())
    f.write(f"2. **El desbalance es sistemático, no ruido.** En {n_desbal} de las {len(SUBRED)} estaciones la deriva acumulada del inventario a lo largo del día "
            "supera su capacidad (`rango_deriva/cap` ≥ 1): sin intervención se vaciarían o llenarían todos los días (ver `fig_deriva_acumulada.png`).\n")
    f.write("3. **Volumen suficiente y estable.** ~2,150 viajes/día tocan la subred; el coeficiente de variación de los retiros diarios por estación "
            f"está entre {T.cv_retiros_diarios.min():.2f} y {T.cv_retiros_diarios.max():.2f} (ver `fig_variabilidad_diaria.png`).\n")
    f.write("4. **Zona contigua y compacta** (≈1.1 km de diámetro), lo que permite tratar la redistribución como un problema local.\n\n")
    f.write("## Estaciones\n\n")
    cols = ["nombre", "capacidad", "retiros_dia", "arribos_dia", "neto_7_10h", "neto_17_20h", "rango_deriva/cap", "cv_retiros_diarios", "rol"]
    f.write(T[cols].to_markdown() + "\n\n")
    f.write("`neto_7_10h` = arribos − retiros entre 7 y 10 h (promedio por día hábil); negativo = la estación pierde bicis. "
            "`rango_deriva/cap` = (máximo − mínimo de la deriva acumulada) / capacidad; ≥ 1 implica que la estación no puede absorber el día sin redistribución.\n\n")
    f.write("## Intercambio con el exterior\n\n")
    f.write("Destinos externos principales de los viajes que salen de la subred (viajes/día):\n\n")
    f.write(pd.DataFrame({"viajes_dia": (dest_ext / ndias).round(1), "nombre": est["nombre"].reindex(dest_ext.index)}).to_markdown() + "\n\n")
    f.write("Orígenes externos principales de los viajes que entran:\n\n")
    f.write(pd.DataFrame({"viajes_dia": (orig_ext / ndias).round(1), "nombre": est["nombre"].reindex(orig_ext.index)}).to_markdown() + "\n\n")
    f.write("## Implicación para el modelo\n\n")
    f.write("Sólo ~7% de los viajes son internos: la subred **no es un sistema cerrado** y no conviene modelarla como una red de colas cerrada. "
            "La formulación natural es tratar cada estación como una cola con capacidad finita (K = docks) donde los retiros y los arribos "
            "son procesos de llegada exógenos con tasas que dependen de la hora, y el resto de la red es el exterior. "
            "Los estados 0 (sin bicis) y K (sin docks) son las dos fallas que el operador quiere evitar.\n\n")
    f.write("## Viajes no observados\n\n")
    f.write("Las tasas de retiro estimadas de los CSV están censuradas: cuando una estación está vacía no se registra ningún retiro, aunque haya demanda. "
            "Las fuentes de la subred (208, 211, 204, 210, 212) son las candidatas a estar subestimadas en la mañana, y los sumideros (217, 207, 205, 201, 225) "
            "a tener arribos subestimados. En el EDA esto se manifiesta como perfiles de retiro que se 'aplanan' en la hora pico en lugar de seguir "
            "la forma del resto de la red; es una de las hipótesis a revisar al estimar parámetros.\n")

print(f"Subred: {tot/ndias:.0f} viajes/día; internos {n_int/tot*100:.1f}%")
print(T[["nombre", "capacidad", "retiros_dia", "arribos_dia", "neto_7_10h", "rango_deriva/cap", "cv_retiros_diarios", "rol"]].to_string())
