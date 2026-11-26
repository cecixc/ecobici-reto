#!/usr/bin/env python3
"""
Etapa 2 - Modelo matemático de la subred (MA2004B).

Uso:
    python modelo.py --limpios out/viajes_limpios.csv --estaciones out/estaciones.csv --out out/modelo

Modelo: cada estación i es una cadena de Markov de nacimiento y muerte en tiempo
continuo, X_i(t) = bicis ancladas, con estados 0..K_i (K_i = docks del GBFS).
    nacimiento (llega una bici):  tasa mu_i(t)      si X < K   (si X = K el usuario es rechazado)
    muerte (alguien la retira):   tasa lambda_i(t)  si X > 0   (si X = 0 el usuario se va sin bici)
lambda y mu son constantes por bloques de 15 min (Poisson no homogéneo).

El script:
  1. prueba los supuestos contra los datos (Poisson, exponencialidad, granularidad,
     día de la semana, censura) y guarda la tabla de resultados;
  2. estima lambda(t) y mu(t) corrigiendo la censura (horas en que la estación
     estaba vacía o llena no cuentan como exposición);
  3. reconstruye con el ID de la bici lo que hoy mueve el operador;
  4. resuelve las ecuaciones de Kolmogorov hacia adelante y calcula las
     cantidades que corresponden a las fallas del operador.

Salidas en --out:
    tasas_15min.csv            lambda y mu por estación y bloque (crudas y corregidas)
    pruebas_supuestos.csv      un renglón por prueba y estación
    episodios_censura.csv      huecos improbables detectados (vacía / llena / fuera de servicio)
    reposiciones.csv           bicis metidas y sacadas por el operador, por estación y hora
    fallas_vs_inventario.csv   E[retiros perdidos], E[arribos rechazados] para cada inventario a las 05:00
    resumen_estaciones.csv     inventario inicial óptimo y fallas esperadas por estación
    fig_*.png, ficha_modelo.md
"""
import argparse, os
import numpy as np
import pandas as pd
from scipy import stats
from scipy.linalg import expm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
SUBRED = ["211", "212", "208", "204", "210", "217", "207", "205", "201", "225"]
FUENTES, SUMIDEROS = SUBRED[:5], SUBRED[5:]
# 211 y 212 están en la misma esquina (Horacio entre Newton y Hegel, ~20 m): los usuarios las usan
# como una sola. Se modelan también como un nodo fusionado con K = K211 + K212.
FUSION = {"211+212": ["211", "212"]}
SUBRED_M = SUBRED + list(FUSION)
MIEMBROS = {**{s: [s] for s in SUBRED}, **FUSION}
T0, T1 = 5 * 60, 24 * 60 + 30     # día de servicio en minutos desde las 00:00: 05:00 a 00:30
B = 15                             # tamaño del bloque para lambda(t), mu(t), en minutos
NB = (T1 - T0) // B
UMBRAL_HUECO = 6.9                 # un hueco sin eventos con Lambda > 6.9 tiene prob. e^-6.9 = 0.1% bajo Poisson
ITER_CENSURA = 4                   # iteraciones estimar tasa -> detectar huecos -> reestimar
GRUPO_T1, GRUPO_T2 = 1.0, 2.0      # viaje en grupo: mismo origen y destino, salen a <1 min y llegan a <2 min
MIN_CELDA = 1.0                    # media mínima por celda para la prueba de dispersión
MAX_BICIS_DANADAS = 2              # hueco de retiros con <= 2 bicis quietas todo el tiempo = vacía de bicis útiles

ap = argparse.ArgumentParser()
ap.add_argument("--limpios", required=True)
ap.add_argument("--estaciones", required=True)
ap.add_argument("--out", default="out/modelo")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)

c = pd.read_csv(args.limpios, dtype={"Ciclo_Estacion_Retiro": str, "Ciclo_EstacionArribo": str, "dia_atipico": str},
                parse_dates=["ts_retiro", "ts_arribo"])
est = pd.read_csv(args.estaciones, dtype={"codigo": str}).set_index("codigo")
K = est["capacidad"].reindex(SUBRED).astype(int)
NOM = est["nombre"].reindex(SUBRED).str.replace(r"^CE-\d+\s+", "", regex=True)
for f, mm in FUSION.items():
    K[f] = int(K[mm].sum()); NOM[f] = " + ".join(NOM[m] for m in mm)
d0 = pd.to_datetime(c["fecha_servicio"])
c["tr"] = (c["ts_retiro"] - d0).dt.total_seconds() / 60     # minutos desde 00:00 del día de servicio
c["ta"] = (c["ts_arribo"] - d0).dt.total_seconds() / 60
DIAS = sorted(c["fecha_servicio"].unique())
ND = len(DIAS)

# eventos de la subred: un retiro o un arribo por viaje
ev = pd.concat([
    pd.DataFrame({"est": c.Ciclo_Estacion_Retiro, "otra": c.Ciclo_EstacionArribo, "dia": c.fecha_servicio,
                  "t": c.tr, "t_otra": c.ta, "tipo": "ret"}),
    pd.DataFrame({"est": c.Ciclo_EstacionArribo, "otra": c.Ciclo_Estacion_Retiro, "dia": c.fecha_servicio,
                  "t": c.ta, "t_otra": c.tr, "tipo": "arr"})], ignore_index=True)
ev = ev[ev.est.isin(SUBRED) & (ev.t >= T0) & (ev.t < T1)]
ev = pd.concat([ev] + [ev[ev.est.isin(mm)].assign(est=f) for f, mm in FUSION.items()], ignore_index=True)
ev = ev.sort_values(["est", "tipo", "dia", "otra", "t"])

# viajes en grupo (dos o más personas que salen y llegan juntas)
prev = ev.shift()
mismo = (ev.est.eq(prev.est) & ev.tipo.eq(prev.tipo) & ev.dia.eq(prev.dia) & ev.otra.eq(prev.otra)
         & (ev.t - prev.t <= GRUPO_T1) & ((ev.t_otra - prev.t_otra).abs() <= GRUPO_T2))
ev["grupo"] = (~mismo).cumsum()
ev = ev.sort_values(["est", "tipo", "dia", "t"]).reset_index(drop=True)
tam = ev[ev.est.isin(SUBRED)].groupby("grupo").size()
frac_grupo = tam[tam > 1].sum() / tam.sum()
evg = ev.drop_duplicates("grupo")      # un evento por grupo


def tiempos(df):
    return {d: g.t.values for d, g in df.groupby("dia")}


def tasa(tb, expo):
    """tasa por minuto en cada bloque = eventos / minutos de exposición (MLE de Poisson con censura)."""
    N = np.zeros(NB); E = np.zeros(NB)
    for d in DIAS:
        t = tb.get(d, np.array([]))
        np.add.at(N, ((t - T0) // B).astype(int), 1)
        E += expo[d]
    return N / np.maximum(E, 1e-9), N, E


def Lambda(rate):
    cum = np.concatenate([[0], np.cumsum(rate * B)])
    def L(t):
        t = np.clip(np.asarray(t, float), T0, T1 - 1e-9)
        b = ((t - T0) // B).astype(int)
        return cum[b] + rate[b] * (t - T0 - b * B)
    return L


def huecos(t, L, umbral):
    pts = np.concatenate([[T0], np.sort(t), [T1]])
    g = np.diff(L(pts))
    return [(pts[i], pts[i + 1], g[i]) for i in np.where(g > umbral)[0]], len(g)


def quitar_exposicion(expo, d, a, b):
    for k in range(int((a - T0) // B), int(min((b - T0) // B, NB - 1)) + 1):
        lo = T0 + k * B
        expo[d][k] -= max(0.0, min(b, lo + B) - max(a, lo))


def interseca(A, Bv):
    out = []
    for d, a, b in A:
        for d2, a2, b2 in Bv:
            if d == d2 and min(b, b2) > max(a, a2):
                out.append((d, max(a, a2), min(b, b2)))
    return out


# ----------------------------------------------------------------------------
# 1-2. Censura y tasas corregidas
# ----------------------------------------------------------------------------
TB = {(s, tp): tiempos(ev[(ev.est == s) & (ev.tipo == tp)]) for s in SUBRED_M for tp in ("ret", "arr")}
cruda, corr, marcados, n_huecos = {}, {}, {}, {}
for key, tb in TB.items():
    expo = {d: np.full(NB, float(B)) for d in DIAS}
    cruda[key] = tasa(tb, expo)[0]
    for _ in range(ITER_CENSURA):
        r = tasa(tb, expo)[0]
        L = Lambda(r)
        expo = {d: np.full(NB, float(B)) for d in DIAS}
        fl, ng = [], 0
        for d in DIAS:
            f, k = huecos(tb.get(d, np.array([])), L, UMBRAL_HUECO)
            ng += k
            fl += [(d, a, b) for a, b, _ in f]
            for a, b, _ in f:
                quitar_exposicion(expo, d, a, b)
    marcados[key], n_huecos[key] = fl, ng

# ----------------------------------------------------------------------------
# Rastreo por ID de bici: cadenas "llega a A en t1 -> su siguiente viaje sale de B en t2"
# ----------------------------------------------------------------------------
cb = c.sort_values(["Bici", "ts_retiro"]).reset_index(drop=True)
sig = cb.groupby("Bici").shift(-1)
ch = pd.DataFrame({"A": cb.Ciclo_EstacionArribo, "t1": cb.ts_arribo, "d1": pd.to_datetime(cb.fecha_servicio),
                   "B": sig.Ciclo_Estacion_Retiro, "t2": sig.ts_retiro, "d2": pd.to_datetime(sig.fecha_servicio)}).dropna(subset=["B"])
ch = ch[((ch.d2 - ch.d1).dt.days <= 1) & (ch.t2 >= ch.t1)]   # sin fin de semana ni festivo de por medio
quieta = ch[ch.A == ch.B]                                      # bici que se quedó anclada en A de t1 a t2 (confirmada)

# cota inferior del inventario, minuto a minuto: bicis confirmadas en la estación
grid = pd.date_range(pd.Timestamp(DIAS[0]), pd.Timestamp(DIAS[-1]) + pd.Timedelta("1D"), freq="1min")
gmin = np.asarray(grid.hour * 60 + grid.minute)
madrugada = gmin < 30                                   # 00:00-00:30 pertenecen al día de servicio anterior
gdia = np.asarray((grid - pd.to_timedelta(madrugada.astype(int), unit="D")).strftime("%Y-%m-%d"))
gmin = np.where(madrugada, gmin + 1440, gmin)
en_servicio = np.isin(gdia, DIAS) & (gmin >= T0) & (gmin < T1)
LB, LLENA_CONF = {}, {}
for s in SUBRED_M:
    q = quieta[quieta.A.isin(MIEMBROS[s]) & quieta.B.isin(MIEMBROS[s])]
    a = np.searchsorted(grid.values, q.t1.values.astype(grid.values.dtype))
    b = np.searchsorted(grid.values, q.t2.values.astype(grid.values.dtype))
    o = np.zeros(len(grid) + 1, int); np.add.at(o, a, 1); np.add.at(o, b, -1)
    LB[s] = np.cumsum(o)[:-1]
    # tramos en que la estación está llena con certeza (bicis confirmadas >= docks)
    full = (LB[s] >= K[s]) & en_servicio
    cambios = np.flatnonzero(np.diff(np.concatenate([[0], full.astype(int), [0]])))
    LLENA_CONF[s] = [(gdia[i], gmin[i], gmin[j - 1] + 1) for i, j in zip(cambios[::2], cambios[1::2])]


def union(iv):
    """une intervalos (dia, a, b) que se traslapan."""
    out = []
    for d, a, b in sorted(iv):
        if out and out[-1][0] == d and a <= out[-1][2]:
            out[-1] = (d, out[-1][1], max(out[-1][2], b))
        else:
            out.append((d, a, b))
    return out


def bicis_todo_el_hueco(s, d, a, b):
    """bicis confirmadas en s durante TODO el intervalo [a, b] (minutos del día de servicio d)."""
    ta = pd.Timestamp(d) + pd.Timedelta(minutes=float(a)); tb = pd.Timestamp(d) + pd.Timedelta(minutes=float(b))
    q = quieta[quieta.A.isin(MIEMBROS[s]) & quieta.B.isin(MIEMBROS[s]) & (quieta.t1 <= ta) & (quieta.t2 >= tb)]
    return len(q)


# si faltan retiros y arribos al mismo tiempo, la estación estaba fuera de servicio, no vacía ni llena
episodios = []
for s in SUBRED_M:
    fs = interseca(marcados[(s, "ret")], marcados[(s, "arr")])
    for d, a, b in fs:
        episodios.append((s, d, a, b, "fuera de servicio"))
    for tp, lab in (("ret", "vacía (faltan retiros)"), ("arr", "llena (faltan arribos)")):
        for d, a, b in marcados[(s, tp)]:
            # parte del hueco que no es fuera de servicio
            resto = [(a, b)]
            for d2, a2, b2 in fs:
                if d2 != d:
                    continue
                nuevo = []
                for x, y in resto:
                    if b2 <= x or a2 >= y:
                        nuevo.append((x, y))
                    else:
                        if a2 > x: nuevo.append((x, a2))
                        if b2 < y: nuevo.append((b2, y))
                resto = nuevo
            for x, y in resto:
                if y - x > 0.5:
                    episodios.append((s, d, x, y, lab))
EP = pd.DataFrame(episodios, columns=["codigo", "dia", "inicio_min", "fin_min", "tipo"])
EP["bicis_quietas"] = [bicis_todo_el_hueco(s, d, a, b) for s, d, a, b in zip(EP.codigo, EP.dia, EP.inicio_min, EP.fin_min)]
# Verificación con el ID de la bici. Un hueco de retiros con 3 o más bicis ancladas todo el tiempo no
# es una estación vacía: se descarta como censura (cuenta como exposición normal). Con 1-2 bicis
# quietas en plena demanda lo más probable es que estén dañadas: se acepta como vacía "de bicis útiles".
# Segunda verificación, simétrica: si en un hueco de retiros llegan 3+ bicis y nadie las toma, había
# bicis; si en un hueco de arribos salen 3+ bicis (se liberan docks) y nadie llega, había docks.
def eventos_dentro(s, tp, d, a, b):
    t = TB[(s, tp)].get(d, np.array([]))
    return int(((t > a) & (t < b)).sum())


EP["eventos_contrarios"] = [eventos_dentro(s, "arr" if tp.startswith("vacía") else "ret", d, a, b)
                            for s, d, a, b, tp in zip(EP.codigo, EP.dia, EP.inicio_min, EP.fin_min, EP.tipo)]
vac = EP.tipo == "vacía (faltan retiros)"
lle = EP.tipo == "llena (faltan arribos)"
EP.loc[vac & EP.bicis_quietas.between(1, MAX_BICIS_DANADAS), "tipo"] = "vacía (solo bicis sin usar)"
EP.loc[vac & ((EP.bicis_quietas > MAX_BICIS_DANADAS) | (EP.eventos_contrarios > MAX_BICIS_DANADAS)), "tipo"] = "hueco no explicado (no se corrige)"
EP.loc[lle & (EP.eventos_contrarios > MAX_BICIS_DANADAS), "tipo"] = "hueco no explicado (no se corrige)"
EP["censura"] = EP.tipo != "hueco no explicado (no se corrige)"


def max_conf_sobre_K(s, d, a, b):
    m = (gdia == d) & (gmin >= a) & (gmin < b)
    return LB[s][m].max() / K[s] if m.any() else np.nan


EP["max_bicis_confirmadas/K"] = [round(max_conf_sobre_K(s, d, a, b), 3) for s, d, a, b in zip(EP.codigo, EP.dia, EP.inicio_min, EP.fin_min)]
EP["inicio"] = EP.inicio_min.map(lambda m: f"{int(m // 60) % 24:02d}:{int(m % 60):02d}")
EP["fin"] = EP.fin_min.map(lambda m: f"{int(m // 60) % 24:02d}:{int(m % 60):02d}")
EP["duracion_min"] = (EP.fin_min - EP.inicio_min).round(1)
EP.to_csv(f"{args.out}/episodios_censura.csv", index=False)
ES_VACIA = EP.tipo.str.startswith("vacía")
ES_LLENA = EP.tipo.str.startswith("llena")
ES_FUERA = EP.tipo == "fuera de servicio"

# tasas corregidas: los minutos censurados aceptados no cuentan como exposición
CENS = {}
for s in SUBRED_M:
    for tp, m in (("ret", ES_VACIA), ("arr", ES_LLENA)):
        e = EP[(EP.codigo == s) & (m | ES_FUERA)]
        iv = list(zip(e.dia, e.inicio_min, e.fin_min))
        if tp == "arr":            # además, los minutos en que la estación está llena confirmada
            iv += LLENA_CONF[s]
        CENS[(s, tp)] = union(iv)
        expo = {d: np.full(NB, float(B)) for d in DIAS}
        for d, a, b in CENS[(s, tp)]:
            quitar_exposicion(expo, d, a, b)
        corr[(s, tp)] = tasa(TB[(s, tp)], expo)[0]

# demanda que no se ve: integral de la tasa corregida sobre los episodios de vacía / llena
perdidos = {}
for s in SUBRED_M:
    for tp, m in (("ret", ES_VACIA), ("arr", ES_LLENA)):
        L = Lambda(corr[(s, tp)])
        e = EP[(EP.codigo == s) & m]
        iv = list(zip(e.dia, e.inicio_min, e.fin_min)) + (LLENA_CONF[s] if tp == "arr" else [])
        perdidos[(s, tp)] = float(sum(L(b) - L(a) for _, a, b in union(iv))) / ND

tas = []
for s in SUBRED_M:
    for tp in ("ret", "arr"):
        for k in range(NB):
            tas.append((s, "lambda" if tp == "ret" else "mu", T0 + k * B, cruda[(s, tp)][k] * 60, corr[(s, tp)][k] * 60))
TAS = pd.DataFrame(tas, columns=["codigo", "tasa", "min_inicio", "cruda_por_hora", "corregida_por_hora"])
TAS["hora"] = TAS.min_inicio.map(lambda m: f"{int(m // 60) % 24:02d}:{int(m % 60):02d}")
TAS.round(3).to_csv(f"{args.out}/tasas_15min.csv", index=False)

# ----------------------------------------------------------------------------
# 1. Pruebas de supuestos
# ----------------------------------------------------------------------------
P = []

# (a) Poisson: índice de dispersión de los conteos por bloque de 15 min entre los 21 días
def dispersion(df):
    df = df.assign(b=((df.t - T0) // B).astype(int))
    cnt = df.groupby(["est", "tipo", "b", "dia"]).size().unstack(fill_value=0).reindex(columns=DIAS, fill_value=0)
    m = cnt.mean(axis=1)
    X2 = (cnt.sub(m, axis=0) ** 2).sum(axis=1) / m
    r = pd.DataFrame({"m": m, "disp": cnt.var(axis=1) / m, "p": stats.chi2.sf(X2, ND - 1)})
    return r[r.m >= MIN_CELDA]

for lab, df in (("viajes", ev), ("grupos", evg)):
    r = dispersion(df)
    for (s, tp), g in r.groupby(level=[0, 1]):
        P.append(dict(prueba=f"dispersion_15min_{lab}", codigo=s, tipo=tp, n=len(g),
                      estadistico=round(g.disp.median(), 3), frac_rechazo_5pct=round((g.p < .05).mean(), 3)))

# (b) exponencialidad por reescalamiento del tiempo: si es Poisson con tasa lambda(t),
#     los huecos z = Lambda(t_k) - Lambda(t_{k-1}) son Exp(1). Prueba K-S.
Z = {}
for key in TB:
    s, tp = key
    tbg = tiempos(evg[(evg.est == s) & (evg.tipo == tp)])
    for lab, rate, quitar in (("cruda", cruda[key], False), ("corregida", corr[key], True)):
        L = Lambda(rate)
        zs = []
        for d, t in tbg.items():
            t = np.sort(t)
            z = np.diff(L(t))
            if quitar:  # se excluyen los huecos que caen dentro de un episodio censurado aceptado
                mid = (t[1:] + t[:-1]) / 2
                fuera = np.ones(len(z), bool)
                for d2, a, b in CENS[key]:
                    if d2 == d:
                        fuera &= ~((mid > a) & (mid < b))
                z = z[fuera]
            zs.append(z)
        zs = np.concatenate(zs)
        Z[(s, tp, lab)] = zs
        ks = stats.kstest(zs, "expon")
        P.append(dict(prueba=f"ks_exponencial_{lab}", codigo=s, tipo=tp, n=len(zs),
                      estadistico=round(ks.statistic, 4), p_valor=round(ks.pvalue, 4)))

# (c) granularidad: ¿los cuatro cuartos de cada hora tienen la misma tasa?
g = ev.assign(h=(ev.t // 60).astype(int), q=((ev.t % 60) // 15).astype(int)) \
      .groupby(["est", "tipo", "h", "q"]).size().unstack(fill_value=0)
g = g[g.sum(axis=1) >= 40]
pv = g.apply(lambda r: stats.chisquare(r.values).pvalue, axis=1)
for (s, tp), x in pv.groupby(level=[0, 1]):
    P.append(dict(prueba="cuartos_de_hora_homogeneos", codigo=s, tipo=tp, n=len(x), frac_rechazo_5pct=round((x < .05).mean(), 3)))

# (d) día de la semana (Kruskal-Wallis sobre viajes diarios de la subred)
diario = ev[ev.est.isin(SUBRED)].groupby("dia").size().reindex(DIAS)
dow = pd.to_datetime(pd.Series(DIAS)).dt.dayofweek.values
kw = stats.kruskal(*[diario.values[dow == k] for k in range(5)])
P.append(dict(prueba="kruskal_dia_semana", codigo="subred", tipo="ambos", n=ND, estadistico=round(kw.statistic, 3), p_valor=round(kw.pvalue, 4)))
m_d, v_d = diario.mean(), diario.var()
sigma_theta = np.sqrt(max(v_d - m_d, 0) / m_d ** 2)   # Var(N) = m + sigma^2 m^2 (Poisson mixta)
P.append(dict(prueba="factor_diario_sd", codigo="subred", tipo="ambos", n=ND, estadistico=round(sigma_theta, 4)))
rel = ev[ev.est.isin(SUBRED)].groupby(["est", "tipo", "dia"]).size().unstack(fill_value=0)
rel = rel.div(rel.mean(axis=1), axis=0)
C = np.corrcoef(rel.values)
P.append(dict(prueba="corr_media_series_diarias", codigo="subred", tipo="ambos", n=len(rel),
              estadistico=round(C[np.triu_indices_from(C, 1)].mean(), 3)))

# (e) censura: ¿hay más huecos improbables de los que Poisson permite?
for key in TB:
    s, tp = key
    esperados = n_huecos[key] * np.exp(-UMBRAL_HUECO)
    obs = len(marcados[key])
    P.append(dict(prueba="huecos_improbables_obs_vs_esp", codigo=s, tipo=tp, n=n_huecos[key],
                  estadistico=obs, esperado=round(esperados, 2), p_valor=round(stats.poisson.sf(obs - 1, esperados), 6)))

# (f) independencia: fracción de viajes internos (acoplamiento entre estaciones)
toca = c.Ciclo_Estacion_Retiro.isin(SUBRED) | c.Ciclo_EstacionArribo.isin(SUBRED)
interno = c.Ciclo_Estacion_Retiro.isin(SUBRED) & c.Ciclo_EstacionArribo.isin(SUBRED)
P.append(dict(prueba="frac_viajes_internos", codigo="subred", tipo="ambos", n=int(toca.sum()), estadistico=round(interno.sum() / toca.sum(), 4)))
P.append(dict(prueba="frac_viajes_en_grupo", codigo="subred", tipo="ambos", n=len(ev), estadistico=round(frac_grupo, 4)))

# ----------------------------------------------------------------------------
# 3. Lo que hoy hace el operador (rastreo por ID de bici)
# ----------------------------------------------------------------------------
mov = ch[ch.A != ch.B]      # la bici cambió de estación sin que haya un viaje: la movió el operador
REP = pd.DataFrame({
    "metidas_dia": {s: (mov.B.isin(MIEMBROS[s]) & ~mov.A.isin(MIEMBROS[s])).sum() / ND for s in SUBRED_M},
    "sacadas_dia": {s: (mov.A.isin(MIEMBROS[s]) & ~mov.B.isin(MIEMBROS[s])).sum() / ND for s in SUBRED_M}}).reindex(SUBRED_M)
REP["neto_dia"] = REP.metidas_dia - REP.sacadas_dia
# hora de las que se meten el mismo día con ventana corta (cota superior = hora del siguiente retiro)
x = mov[mov.B.isin(SUBRED) & (mov.d1 == mov.d2) & ((mov.t2 - mov.t1).dt.total_seconds() <= 2 * 3600)]
hora_meten = x.t2.dt.hour.value_counts().sort_index()
REP.index.name = "codigo"
REP.round(2).to_csv(f"{args.out}/reposiciones.csv")
frac_mov = (ch.A != ch.B).mean()

conf_llena = {s: ((LB[s] >= K[s]) & en_servicio).sum() / ND for s in SUBRED_M}
# inventario confirmado a las 05:00 (bicis que pasaron la noche y salieron de la misma estación)
x05 = {s: np.median(LB[s][(gmin == T0) & en_servicio]) for s in SUBRED_M}

# ----------------------------------------------------------------------------
# 4. Modelo: ecuaciones de Kolmogorov hacia adelante
# ----------------------------------------------------------------------------
def generador(Kc, lam, mu, absorbente=False):
    n = Kc + 1 + (1 if absorbente else 0)
    Q = np.zeros((n, n))
    for x in range(Kc + 1):
        if x < Kc: Q[x, x + 1] = mu
        if x > 0:  Q[x, x - 1] = lam
    if absorbente:            # F = primera falla: alguien no encuentra bici (en 0) o no encuentra dock (en K)
        Q[0, n - 1] = lam
        Q[Kc, n - 1] = mu
    np.fill_diagonal(Q, -Q.sum(axis=1))
    return Q

MIN = np.arange(T0, T1)
res_x0, curvas, resumen = [], {}, []
for s in SUBRED_M:
    Kc = int(K[s]); lam = corr[(s, "ret")]; mu = corr[(s, "arr")]
    M = np.eye(Kc + 1)                          # renglón x0 = distribución de X(t) dado X(05:00) = x0
    F = np.eye(Kc + 2)[:Kc + 1]                 # con estado absorbente de primera falla
    perd = np.zeros(Kc + 1); rech = np.zeros(Kc + 1)
    p0 = np.zeros((Kc + 1, len(MIN))); pK = np.zeros((Kc + 1, len(MIN))); pF = np.zeros((Kc + 1, len(MIN)))
    j = 0
    for k in range(NB):
        P1 = expm(generador(Kc, lam[k], mu[k]))           # un minuto
        P1F = expm(generador(Kc, lam[k], mu[k], True))
        for _ in range(B):
            p0[:, j] = M[:, 0]; pK[:, j] = M[:, Kc]; pF[:, j] = F[:, -1]
            M1 = M @ P1
            perd += lam[k] * 0.5 * (M[:, 0] + M1[:, 0])     # E[retiros perdidos] = integral de lambda P(X=0)
            rech += mu[k] * 0.5 * (M[:, Kc] + M1[:, Kc])    # E[arribos rechazados] = integral de mu P(X=K)
            M = M1; F = F @ P1F; j += 1
    tot = perd + rech
    x_opt = int(np.argmin(tot))
    for x0 in range(Kc + 1):
        res_x0.append((s, x0, perd[x0], rech[x0], tot[x0], F[x0, -1]))
    # hora mediana de la primera falla con el mejor inventario inicial
    cdf = pF[x_opt]
    med = MIN[np.searchsorted(cdf, 0.5)] if cdf[-1] >= 0.5 else np.nan
    curvas[s] = dict(p0=p0, pK=pK, x_opt=x_opt)
    resumen.append(dict(codigo=s, nombre=NOM[s], K=Kc,
                        lambda_dia=round(lam.sum() * B, 1), mu_dia=round(mu.sum() * B, 1),
                        lambda_cruda_dia=round(cruda[(s, "ret")].sum() * B, 1), mu_cruda_dia=round(cruda[(s, "arr")].sum() * B, 1),
                        retiros_no_vistos_dia=round(perdidos[(s, "ret")], 1), arribos_no_vistos_dia=round(perdidos[(s, "arr")], 1),
                        min_vacia_dia=round(EP[(EP.codigo == s) & (EP.tipo.str.startswith("vacía"))].duracion_min.sum() / ND, 1),
                        min_llena_dia=round(EP[(EP.codigo == s) & (EP.tipo.str.startswith("llena"))].duracion_min.sum() / ND, 1),
                        min_fuera_servicio_dia=round(EP[(EP.codigo == s) & (EP.tipo == "fuera de servicio")].duracion_min.sum() / ND, 1),
                        x0_optimo=x_opt, fallas_esp_x0_opt=round(tot[x_opt], 1),
                        perdidos_x0_opt=round(perd[x_opt], 1), rechazados_x0_opt=round(rech[x_opt], 1),
                        fallas_esp_mitad=round(tot[Kc // 2], 1),
                        p_alguna_falla_x0_opt=round(F[x_opt, -1], 3),
                        hora_mediana_1a_falla=(f"{int(med // 60) % 24:02d}:{int(med % 60):02d}" if med == med else "después de 00:30"),
                        operador_neto_dia=round(REP.loc[s, "neto_dia"], 1),
                        min_llena_confirmada_dia=round(conf_llena[s], 1),
                        episodios_vacia=int((EP[EP.codigo == s].tipo == "vacía (faltan retiros)").sum()),
                        episodios_vacia_bicis_sin_usar=int((EP[EP.codigo == s].tipo == "vacía (solo bicis sin usar)").sum()),
                        huecos_no_explicados=int((EP[EP.codigo == s].tipo == "hueco no explicado (no se corrige)").sum()),
                        episodios_llena=int((EP[EP.codigo == s].tipo.str.startswith("llena")).sum()),
                        mediana_max_confirmadas_sobre_K_en_llena=round(EP[(EP.codigo == s) & ES_LLENA]["max_bicis_confirmadas/K"].median(), 2),
                        bicis_confirmadas_05h_mediana=x05[s]))
X0 = pd.DataFrame(res_x0, columns=["codigo", "x0_05h", "E_retiros_perdidos", "E_arribos_rechazados", "E_fallas", "P_alguna_falla"])
X0.round(4).to_csv(f"{args.out}/fallas_vs_inventario.csv", index=False)
R = pd.DataFrame(resumen).set_index("codigo")
R.to_csv(f"{args.out}/resumen_estaciones.csv")
PT = pd.DataFrame(P)
PT.to_csv(f"{args.out}/pruebas_supuestos.csv", index=False)

# ----------------------------------------------------------------------------
# Figuras
# ----------------------------------------------------------------------------
col_f, col_s = "#d95f02", "#1b7837"
rol = {s: col_f if s in FUENTES else col_s for s in SUBRED}
xh = (np.arange(NB) * B + T0) / 60
ticks = [5, 8, 11, 14, 17, 20, 23]

# 1. tasas crudas vs corregidas
fig, axs = plt.subplots(2, 5, figsize=(16, 6.2), dpi=130, sharex=True)
for ax, s in zip(axs.flat, SUBRED):
    ax.step(xh, cruda[(s, "ret")] * 60, where="post", color="#c0392b", lw=.9, alpha=.45)
    ax.step(xh, corr[(s, "ret")] * 60, where="post", color="#c0392b", lw=1.6, label="λ retiros")
    ax.step(xh, cruda[(s, "arr")] * 60, where="post", color="#2980b9", lw=.9, alpha=.45)
    ax.step(xh, corr[(s, "arr")] * 60, where="post", color="#2980b9", lw=1.6, label="μ arribos")
    ax.set_title(f"{s} {NOM[s]}", fontsize=8.5, color=rol[s]); ax.set_xticks(ticks); ax.tick_params(labelsize=7); ax.grid(alpha=.2)
axs[0, 0].legend(fontsize=7); axs[0, 0].set_ylabel("eventos / hora", fontsize=8); axs[1, 0].set_ylabel("eventos / hora", fontsize=8)
fig.suptitle("Tasas por bloque de 15 min, día hábil de septiembre 2026. Línea gruesa: corregida por censura; tenue: cruda", fontsize=10.5)
plt.tight_layout(); plt.savefig(f"{args.out}/fig_tasas.png"); plt.close()

# 2. QQ de los huecos reescalados contra Exp(1)
fig, axs = plt.subplots(1, 3, figsize=(13, 4.3), dpi=130)
qs = np.linspace(.005, .995, 199); teo = -np.log(1 - qs)
for ax, (tit, grupo, tp) in zip(axs, [("Retiros en estaciones que se vacían", FUENTES, "ret"),
                                     ("Retiros en estaciones que se llenan", SUMIDEROS, "ret"),
                                     ("Arribos (las 10)", SUBRED, "arr")]):
    for lab, cc in (("cruda", "#999999"), ("corregida", "#222222")):
        z = np.concatenate([Z[(s, tp, lab)] for s in grupo])
        D = stats.kstest(z, "expon").statistic
        ax.plot(teo, np.quantile(z, qs), color=cc, lw=1.6, label=f"tasa {lab}  (K-S D = {D:.3f})")
    ax.plot([0, 5.5], [0, 5.5], ls="--", color="#c0392b", lw=.9, label="Exp(1) exacta")
    ax.set_title(tit, fontsize=9.5); ax.set_xlabel("cuantil teórico Exp(1)", fontsize=8); ax.set_xlim(0, 5.5); ax.set_ylim(0, 7)
    ax.legend(fontsize=7, loc="upper left"); ax.grid(alpha=.2)
axs[0].set_ylabel("cuantil observado", fontsize=8)
fig.suptitle("Reescalamiento del tiempo: si los eventos son Poisson con tasa λ(t), los huecos Λ(t_k) − Λ(t_{k−1}) son Exp(1)", fontsize=10)
plt.tight_layout(); plt.savefig(f"{args.out}/fig_qq_exponencial.png"); plt.close()

# 3. censura por hora del día
fig, ax = plt.subplots(figsize=(11, 4.2), dpi=130)
hh = np.arange(5, 25)
def min_por_hora(e):
    v = np.zeros(len(hh))
    for a, b in zip(e.inicio_min, e.fin_min):
        for m in np.arange(np.floor(a), b):
            i = int(m // 60) - 5
            if 0 <= i < len(hh): v[i] += 1
    return v / ND
v1 = min_por_hora(EP[EP.codigo.isin(FUENTES) & EP.tipo.str.startswith("vacía")])
v2 = min_por_hora(EP[EP.codigo.isin(SUMIDEROS) & EP.tipo.str.startswith("llena")])
ax.bar(hh - .2, v1, width=.4, color=col_f, label="estaciones que se vacían: minutos sin retiros (vacía)")
ax.bar(hh + .2, v2, width=.4, color=col_s, label="estaciones que se llenan: minutos sin arribos (llena)")
ax.set_xticks(hh); ax.set_xticklabels([f"{h % 24:02d}" for h in hh], fontsize=8)
ax.set_ylabel("minutos por día hábil (suma de 5 estaciones)"); ax.legend(fontsize=8); ax.grid(alpha=.2, axis="y")
ax.set_title("Cuándo está censurada la demanda: huecos con probabilidad < 0.1% bajo Poisson", fontsize=10)
plt.tight_layout(); plt.savefig(f"{args.out}/fig_censura_por_hora.png"); plt.close()

# 4. P(vacía), P(llena) con el mejor inventario inicial
fig, axs = plt.subplots(2, 5, figsize=(16, 6), dpi=130, sharex=True, sharey=True)
xm = MIN / 60
for ax, s in zip(axs.flat, SUBRED):
    cv = curvas[s]; x = cv["x_opt"]
    ax.plot(xm, cv["p0"][x], color="#2980b9", lw=1.6, label="P(vacía)")
    ax.plot(xm, cv["pK"][x], color="#c0392b", lw=1.6, label="P(llena)")
    ax.set_title(f"{s} {NOM[s]} — x0* = {x} de {K[s]}", fontsize=8.5, color=rol[s])
    ax.set_xticks(ticks); ax.tick_params(labelsize=7); ax.grid(alpha=.2); ax.set_ylim(0, 1)
axs[0, 0].legend(fontsize=7)
fig.suptitle("Probabilidad de estación vacía / llena a lo largo del día, sin redistribución, partiendo del inventario a las 05:00 que minimiza las fallas esperadas", fontsize=10)
plt.tight_layout(); plt.savefig(f"{args.out}/fig_prob_falla.png"); plt.close()

# 5. fallas esperadas vs inventario inicial
fig, axs = plt.subplots(2, 5, figsize=(16, 6), dpi=130)
for ax, s in zip(axs.flat, SUBRED):
    d = X0[X0.codigo == s]
    ax.plot(d.x0_05h, d.E_retiros_perdidos, color="#2980b9", lw=1.3, label="retiros perdidos")
    ax.plot(d.x0_05h, d.E_arribos_rechazados, color="#c0392b", lw=1.3, label="arribos rechazados")
    ax.plot(d.x0_05h, d.E_fallas, color="k", lw=2, label="total")
    ax.axvline(curvas[s]["x_opt"], color="k", ls=":", lw=.8)
    ax.set_title(f"{s} {NOM[s]} (K = {K[s]})", fontsize=8.5, color=rol[s]); ax.tick_params(labelsize=7); ax.grid(alpha=.2)
axs[0, 0].legend(fontsize=7); axs[1, 2].set_xlabel("bicis en la estación a las 05:00", fontsize=8)
fig.suptitle("Fallas esperadas en el día (usuarios sin bici + usuarios sin dock) según el inventario inicial, sin redistribución", fontsize=10)
plt.tight_layout(); plt.savefig(f"{args.out}/fig_fallas_vs_inventario.png"); plt.close()

# 6. operador hoy
fig, ax = plt.subplots(figsize=(10, 4), dpi=130)
xx = np.arange(len(SUBRED))
ax.bar(xx - .2, REP.loc[SUBRED, "metidas_dia"], width=.4, color="#555555", label="bicis que mete el operador")
ax.bar(xx + .2, -REP.loc[SUBRED, "sacadas_dia"], width=.4, color="#bbbbbb", label="bicis que saca el operador")
ax.scatter(xx, REP.loc[SUBRED, "neto_dia"], color=[rol[s] for s in SUBRED], zorder=3, s=40, label="neto")
ax.axhline(0, color="k", lw=.6); ax.set_xticks(xx); ax.set_xticklabels(SUBRED)
ax.set_ylabel("bicis por día hábil"); ax.legend(fontsize=8); ax.grid(alpha=.2, axis="y")
ax.set_title("Redistribución actual reconstruida con el ID de la bici (llega a A, su siguiente viaje sale de B ≠ A)", fontsize=10)
plt.tight_layout(); plt.savefig(f"{args.out}/fig_operador_actual.png"); plt.close()

# ----------------------------------------------------------------------------
# Ficha
# ----------------------------------------------------------------------------
def p(prueba, s=None, tp=None, col="estadistico"):
    q = PT[PT.prueba == prueba]
    if s is not None: q = q[q.codigo == s]
    if tp is not None: q = q[q.tipo == tp]
    return q[col]

with open(f"{args.out}/ficha_modelo.md", "w") as f:
    f.write("# Etapa 2 — salidas de modelo.py\n\n")
    f.write(f"{ND} días hábiles, bloques de {B} min, umbral de hueco Λ > {UMBRAL_HUECO} (p = {np.exp(-UMBRAL_HUECO):.4f}).\n\n")
    f.write("## Pruebas\n\n")
    f.write(f"- Viajes en grupo: {frac_grupo:.1%} de los eventos. Internos: {interno.sum() / toca.sum():.1%}.\n")
    f.write(f"- Dispersión 15 min (mediana var/media): viajes ret {p('dispersion_15min_viajes', tp='ret').median():.2f}, "
            f"arr {p('dispersion_15min_viajes', tp='arr').median():.2f}; grupos ret {p('dispersion_15min_grupos', tp='ret').median():.2f}, "
            f"arr {p('dispersion_15min_grupos', tp='arr').median():.2f}.\n")
    f.write(f"- Cuartos de hora homogéneos: rechazo medio {p('cuartos_de_hora_homogeneos', col='frac_rechazo_5pct').mean():.0%} (esperado 5%).\n")
    f.write(f"- Kruskal día de semana p = {kw.pvalue:.3f}. Factor diario sd = {sigma_theta:.3f}. Corr media series diarias = "
            f"{p('corr_media_series_diarias').iloc[0]:.2f}.\n")
    f.write(f"- Fracción de cadenas de bici con cambio de estación sin viaje (operador): {frac_mov:.1%}.\n\n")
    f.write(PT.to_markdown(index=False) + "\n\n## Resumen por estación\n\n" + R.drop(columns="nombre").T.to_markdown() + "\n\n")
    f.write("Hora (cota superior) a la que el operador mete bicis en la subred, mismo día y ventana < 2 h:\n\n")
    f.write(hora_meten.to_frame("bicis_mes").T.to_markdown() + "\n")

print(f"días {ND}; grupo {frac_grupo:.3f}; internos {interno.sum() / toca.sum():.3f}; sigma_theta {sigma_theta:.3f}; KW p {kw.pvalue:.3f}")
print(R.drop(columns="nombre").to_string())
print(PT[PT.prueba.str.startswith("ks")].pivot_table(index=["codigo", "tipo"], columns="prueba", values="estadistico"))
print(PT[PT.prueba == "huecos_improbables_obs_vs_esp"][["codigo", "tipo", "estadistico", "esperado", "p_valor"]].to_string(index=False))
print("operador mete (hora):", hora_meten.to_dict())
