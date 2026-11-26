# Etapa 3 - Análisis de servicio y optimización
# Reto Ecobici, subred Polanco (MA2004B)
# Para correrlo: python scripts/optimizacion.py --modelo out/modelo --out out/optimizacion

import argparse, os, itertools
import numpy as np
import pandas as pd
from scipy.linalg import expm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import warnings

# Ignorar avisos falsos de numpy en Mac al multiplicar matrices (los resultados salen bien)

warnings.filterwarnings("ignore", message=".*encountered in matmul")

# Lista de estaciones (la 211 y la 212 van juntas como en la Etapa 2)

NODOS = ["211+212", "208", "204", "210", "217", "207", "205", "201", "225"]
FUENTES = ["211+212", "208", "204", "210"]  # las que se vacían en la mañana

# Horario del día de servicio en minutos y tamaño de los bloques de tasas

T0, T1 = 5 * 60, 24 * 60 + 30  # de 05:00 a 00:30
BLK = 15  # las tasas cambian cada 15 minutos
NB = (T1 - T0) // BLK  # número de bloques en el día

# Parámetros de la optimización

B_TOTAL = 131  # bicis que hay en la subred a las 05:00 (la mitad de los docks)
HORAS_REB = list(range(6, 23))  # horas en las que puede pasar el camión
MAX_RONDAS = 2  # máximo de rondas de rebalanceo al día
C_GRID = [0.0, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]  # valores de c que probamos
C_BASE = 0.2  # cuánto cuesta mover una bici, medido en fallas

# Diccionario con cuántas bicis mete el operador en cada hora (sale al final de modelo.py)

PERFIL_OPERADOR = {7: 237, 8: 817, 9: 597, 10: 240, 11: 62, 12: 16, 13: 15, 14: 6, 15: 6,
                   16: 29, 17: 121, 18: 115, 19: 39, 20: 44, 21: 143, 22: 13, 23: 1}


# Leer las carpetas de entrada y salida desde la terminal

ap = argparse.ArgumentParser()
ap.add_argument("--modelo", default="out/modelo")
ap.add_argument("--out", default="out/optimizacion")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)  # crea la carpeta de salida si no existe

# Leer los archivos que salieron de la Etapa 2

res = pd.read_csv(f"{args.modelo}/resumen_estaciones.csv", dtype={"codigo": str}).set_index("codigo")
tas = pd.read_csv(f"{args.modelo}/tasas_15min.csv", dtype={"codigo": str})
fvi = pd.read_csv(f"{args.modelo}/fallas_vs_inventario.csv", dtype={"codigo": str})
rep = pd.read_csv(f"{args.modelo}/reposiciones.csv", dtype={"codigo": str}).set_index("codigo")

# Guardar la capacidad (docks) de cada estación

K = {s: int(res.loc[s, "K"]) for s in NODOS}


# Función que regresa las tasas de una estación por bloque, en eventos por minuto
# tp puede ser "lambda" (retiros) o "mu" (arribos), y usamos las corregidas por censura

def tasas(s, tp):
    t = tas[(tas.codigo == s) & (tas.tasa == tp)].sort_values("min_inicio")
    return t["corregida_por_hora"].to_numpy() / 60.0


# Función que dice en qué bloque empieza una hora (por ejemplo 9h es el bloque 16)

def hblk(h):
    return (h * 60 - T0) // BLK


# Función que arma la matriz Q de la cadena de nacimiento y muerte
# Un arribo sube una bici y un retiro baja una bici

def generador(Kc, lam, mu):
    Q = np.zeros((Kc + 1, Kc + 1))
    for x in range(Kc + 1):
        if x < Kc: Q[x, x + 1] = mu  # llega alguien a dejar bici
        if x > 0:  Q[x, x - 1] = lam  # alguien se lleva una bici
    np.fill_diagonal(Q, -Q.sum(axis=1))  # la diagonal hace que cada renglón sume 0
    return Q


# Calcular para cada estación y cada bloque:
# la matriz de transición del bloque y las fallas esperadas dentro del bloque
# Así después solo encadenamos bloques en vez de resolver todo otra vez

BLOQ = {}
for s in NODOS:
    Kc, lam, mu = K[s], tasas(s, "lambda"), tasas(s, "mu")
    Pb, lp, lr = [], [], []
    for k in range(NB):
        P1 = expm(generador(Kc, lam[k], mu[k]))  # transición de un minuto
        M = np.eye(Kc + 1)
        perd = np.zeros(Kc + 1)
        rech = np.zeros(Kc + 1)
        for _ in range(BLK):
            M1 = M @ P1
            perd += lam[k] * 0.5 * (M[:, 0] + M1[:, 0])  # retiros perdidos (estación vacía)
            rech += mu[k] * 0.5 * (M[:, Kc] + M1[:, Kc])  # arribos rechazados (estación llena)
            M = M1
        Pb.append(M)
        lp.append(perd)
        lr.append(rech)
    BLOQ[s] = dict(P=Pb, lp=lp, lr=lr)


# Función que calcula las fallas esperadas entre dos bloques para cada número inicial de bicis
# Va de atrás para adelante sumando las fallas de cada bloque

def costo_tramo(s, a, b):
    Kc = K[s]
    vp = np.zeros(Kc + 1)
    vr = np.zeros(Kc + 1)
    for k in range(b - 1, a - 1, -1):
        vp = BLOQ[s]["lp"][k] + BLOQ[s]["P"][k] @ vp
        vr = BLOQ[s]["lr"][k] + BLOQ[s]["P"][k] @ vr
    return vp, vr


# Función que multiplica las matrices de transición entre dos bloques

def transicion(s, a, b):
    M = np.eye(K[s] + 1)
    for k in range(a, b):
        M = M @ BLOQ[s]["P"][k]
    return M


# Revisar que sin rebalanceo salga lo mismo que en la Etapa 2

val = []
for s in NODOS:
    vp, vr = costo_tramo(s, 0, NB)
    e2 = fvi[fvi.codigo == s].sort_values("x0_05h")["E_fallas"].to_numpy()
    val.append(dict(codigo=s, max_dif_abs=float(np.max(np.abs(vp + vr - e2)))))
VAL = pd.DataFrame(val)
VAL.to_csv(f"{args.out}/validacion.csv", index=False)


# ---------- P1: cuántas bicis poner en cada estación a las 05:00 ----------

# Función que reparte B bicis entre las estaciones con el menor costo posible
# Es programación dinámica tipo mochila, da la respuesta exacta

def asignar(V, B):
    INF = 1e18
    f = np.full(B + 1, INF)
    f[0] = 0.0
    arg = []
    for s in NODOS:
        g = np.full(B + 1, INF)
        a = np.zeros(B + 1, int)
        for b in range(B + 1):
            for x in range(min(K[s], b) + 1):
                v = f[b - x] + V[s][x]
                if v < g[b]:
                    g[b], a[b] = v, x
        f = g
        arg.append(a)
    # Regresar de atrás para adelante para ver cuántas le tocaron a cada estación
    x, b = {}, B
    for s, a in zip(reversed(NODOS), reversed(arg)):
        x[s] = int(a[b])
        b -= x[s]
    return f[B], x


# Calcular las fallas del día completo para cada estación según con cuántas bicis empieza

TR_DIA = {s: costo_tramo(s, 0, NB) for s in NODOS}
F_DIA = {s: TR_DIA[s][0] + TR_DIA[s][1] for s in NODOS}

# Ver cómo cambian las fallas si tuviéramos más o menos bicis en total

curva_B = []
for B in range(0, sum(K.values()) + 1, 5):
    v, _ = asignar(F_DIA, B)
    curva_B.append(dict(B=B, E_fallas=round(v, 2)))
CURVA_B = pd.DataFrame(curva_B)
CURVA_B.to_csv(f"{args.out}/p1_fallas_vs_B.csv", index=False)

# Resolver P1 con B = 131 y guardar la tabla

F1, X1 = asignar(F_DIA, B_TOTAL)
P1 = pd.DataFrame([dict(codigo=s, nombre=res.loc[s, "nombre"], K=K[s],
                        x_05h=X1[s], x_mitad=K[s] // 2,
                        perdidos=round(TR_DIA[s][0][X1[s]], 1),
                        rechazados=round(TR_DIA[s][1][X1[s]], 1),
                        E_fallas=round(F_DIA[s][X1[s]], 1),
                        E_fallas_mitad=round(F_DIA[s][K[s] // 2], 1)) for s in NODOS])
P1.to_csv(f"{args.out}/p1_inventario.csv", index=False)


# ---------- P2: inventario + rondas de rebalanceo ----------
# En cada ronda el camión deja la estación con un número fijo de bicis (el objetivo)
# Entonces el día se parte en pedazos y cada pedazo se puede calcular por separado
# El camión puede traer o llevarse bicis del depósito porque la subred no es cerrada

# Diccionarios para no repetir cálculos (si no tarda muchísimo)

cache_tr, cache_T = {}, {}


def tramo(s, a, b):
    if (s, a, b) not in cache_tr:
        cache_tr[(s, a, b)] = costo_tramo(s, a, b)
    return cache_tr[(s, a, b)]


# Función que calcula cuántas bicis hay que mover en promedio para dejar la estación en el objetivo

def mov(s, a, b):
    if (s, a, b) not in cache_T:
        T = transicion(s, a, b)
        xs = np.arange(K[s] + 1)
        cache_T[(s, a, b)] = T @ np.abs(xs[:, None] - xs[None, :])
    return cache_T[(s, a, b)]


# Función que encuentra los mejores objetivos de una estación para cada ronda
# Empieza por la última ronda y se va para atrás

def politica_estacion(s, cortes, c):
    R = len(cortes) - 2
    tp, tr = tramo(s, cortes[-2], cortes[-1])
    W = tp + tr  # costo total (fallas + c por bicis movidas)
    Wf = W.copy()  # solo fallas
    Wm = np.zeros_like(W)  # solo bicis movidas
    Wy = [[] for _ in range(K[s] + 1)]  # objetivos que se van eligiendo
    idx = np.arange(K[s] + 1)
    for r in range(R, 0, -1):
        a, b = cortes[r - 1], cortes[r]
        sp, sr = tramo(s, a, b)
        A = mov(s, a, b)
        tot = c * A + W[None, :]
        yb = tot.argmin(axis=1)  # el mejor objetivo según cómo quedó la estación antes
        W, Wf, Wm, Wy = (sp + sr + tot[idx, yb],
                         sp + sr + Wf[yb],
                         A[idx, yb] + Wm[yb],
                         [[int(yb[y])] + Wy[yb[y]] for y in idx])
    return W, Wf, Wm, Wy


# Función que resuelve P2 para unas horas de ronda y un valor de c

def resolver(horas, c, B=B_TOTAL):
    cortes = [0] + [hblk(h) for h in horas] + [NB]
    pol = {s: politica_estacion(s, cortes, c) for s in NODOS}
    _, x = asignar({s: pol[s][0] for s in NODOS}, B)  # reparto de las 05:00
    return dict(horas=horas, c=c, x=x,
                E_fallas=sum(pol[s][1][x[s]] for s in NODOS),
                E_movidas=sum(pol[s][2][x[s]] for s in NODOS),
                y={s: pol[s][3][x[s]] for s in NODOS})


# Hacer la lista de todas las combinaciones de horas: 0 rondas, 1 ronda y 2 rondas

combos = [()]
for R in range(1, MAX_RONDAS + 1):
    combos += list(itertools.combinations(HORAS_REB, R))

# Probar todas las combinaciones con todos los valores de c

frontera = []
for c in C_GRID:
    for hs in combos:
        r = resolver(list(hs), c)
        frontera.append(dict(rondas=len(hs), horas=" ".join(f"{h}h" for h in hs), c=c,
                             E_fallas=round(r["E_fallas"], 2), E_movidas=round(r["E_movidas"], 2)))
FR = pd.DataFrame(frontera)
FR["obj"] = FR.E_fallas + FR.c * FR.E_movidas  # lo que estamos minimizando
FR.to_csv(f"{args.out}/p2_frontera.csv", index=False)

# Quedarnos con el mejor horario para cada número de rondas

mejor = {}
for R in range(MAX_RONDAS + 1):
    sub = FR[(FR.rondas == R) & (FR.c == C_BASE)]
    hs = sub.loc[sub.obj.idxmin(), "horas"]
    mejor[R] = [int(h[:-1]) for h in hs.split()] if hs else []

# Guardar la política propuesta: bicis a las 05:00 y objetivo de cada ronda

PROP = resolver(mejor[MAX_RONDAS], C_BASE)
pol = []
for s in NODOS:
    fila = dict(codigo=s, nombre=res.loc[s, "nombre"], K=K[s], x_05h=PROP["x"][s])
    for h, y in zip(PROP["horas"], PROP["y"][s]):
        fila[f"objetivo_{h}h"] = y
    pol.append(fila)
POL = pd.DataFrame(pol)
POL.to_csv(f"{args.out}/p2_politica.csv", index=False)


# ---------- Comparar estrategias ----------

# Sacar qué porcentaje de las reposiciones del operador cae en cada hora

w = np.array([PERFIL_OPERADOR.get(h, 0) for h in range(5, 25)], float)
w /= w.sum()


# Función que le suma d bicis a la distribución (si d no es entero lo reparte entre los dos enteros más cercanos)

def desplaza(p, d, Kc):
    lo = int(np.floor(d))
    fr = d - lo
    q = np.zeros_like(p)
    for dd, wt in ((lo, 1 - fr), (lo + 1, fr)):
        if wt == 0:
            continue
        for x in range(Kc + 1):
            q[min(max(x + dd, 0), Kc)] += wt * p[x]  # no puede bajar de 0 ni pasar de K
    return q


# Función que evalúa una estrategia en una estación durante todo el día
# Si el ajuste es un número, el operador suma esas bicis; si es ("y", obj), dejamos la estación en obj

def evaluar(s, x0, ajustes):
    Kc = K[s]
    p = np.zeros(Kc + 1)
    p[x0] = 1.0  # a las 05:00 sabemos cuántas bicis hay
    F = M = 0.0
    curva = np.zeros(NB)
    for k in range(NB):
        if k in ajustes:
            a = ajustes[k]
            if isinstance(a, tuple):
                M += float(p @ np.abs(np.arange(Kc + 1) - a[1]))
                p = np.zeros(Kc + 1)
                p[a[1]] = 1.0
            else:
                M += abs(a)
                p = desplaza(p, a, Kc)
        f = float(p @ (BLOQ[s]["lp"][k] + BLOQ[s]["lr"][k]))  # fallas en este bloque
        F += f
        curva[k] = f
        p = p @ BLOQ[s]["P"][k]  # pasar al siguiente bloque
    return F, M, curva


# Función que corre una estrategia en todas las estaciones y guarda los totales

estr = {}
def correr(nombre, x0s, ajustes_por_s):
    tot = dict(E_fallas=0.0, E_movidas=0.0)
    cur = np.zeros(NB)
    por = {}
    for s in NODOS:
        F, M, cv = evaluar(s, x0s[s], ajustes_por_s.get(s, {}))
        tot["E_fallas"] += F
        tot["E_movidas"] += M
        cur += cv
        por[s] = F
    estr[nombre] = dict(**tot, curva=cur, por=por)


# Estrategia 1: todas a la mitad y nadie mueve nada

mitad = {s: K[s] // 2 for s in NODOS}
correr("Sin intervención (K/2)", mitad, {})

# Estrategia 2: lo que hace hoy el operador (su neto diario repartido por hora)

oper = {s: {hblk(h): float(rep.loc[s, "neto_dia"]) * w[h - 5]
            for h in range(5, 25) if hblk(h) < NB and w[h - 5] > 0} for s in NODOS}
correr("Operador actual", mitad, oper)

# Estrategia 3: solo el mejor reparto a las 05:00

correr("P1: solo inventario 05:00", X1, {})

# Estrategias 4 y 5: reparto a las 05:00 + 1 o 2 rondas

for R in range(1, MAX_RONDAS + 1):
    r = resolver(mejor[R], C_BASE)
    aj = {s: {hblk(h): ("y", y) for h, y in zip(r["horas"], r["y"][s])} for s in NODOS}
    correr(f"P2: inventario + {R} ronda(s) ({', '.join(f'{h}h' for h in r['horas'])})", r["x"], aj)

# Hacer la tabla de comparación y guardarla

viajes_dia = res.loc[NODOS, "lambda_dia"].sum() + res.loc[NODOS, "mu_dia"].sum()  # retiros + arribos al día
base = estr["Operador actual"]["E_fallas"]
CMP = pd.DataFrame([dict(estrategia=k,
                         E_fallas_dia=round(v["E_fallas"], 1),
                         E_bicis_movidas_dia=round(v["E_movidas"], 1),
                         pct_viajes_fallidos=round(100 * v["E_fallas"] / viajes_dia, 1),
                         mejora_vs_operador_pct=round(100 * (base - v["E_fallas"]) / base, 1))
                    for k, v in estr.items()])
CMP.to_csv(f"{args.out}/comparacion.csv", index=False)


# ---------- Prioridad y rotación por estación ----------
# Prioridad: las que más fallan si nadie las toca van primero
# Rotación: cuántos viajes hay por dock al día

ultima = list(estr)[-1]  # la política propuesta
pr = []
for s in NODOS:
    f_op = estr["Operador actual"]["por"][s]
    f_pr = estr[ultima]["por"][s]
    pr.append(dict(codigo=s, nombre=res.loc[s, "nombre"], K=K[s],
                   tipo="fuente (se vacía AM)" if s in FUENTES else "sumidero (se llena AM)",
                   rotacion_viajes_por_dock_dia=round((res.loc[s, "lambda_dia"] + res.loc[s, "mu_dia"]) / K[s], 1),
                   E_fallas_sin_intervencion=round(estr["Sin intervención (K/2)"]["por"][s], 1),
                   E_fallas_operador=round(f_op, 1),
                   E_fallas_propuesta=round(f_pr, 1),
                   fallas_evitadas_vs_operador=round(f_op - f_pr, 1)))
PR = pd.DataFrame(pr).sort_values("E_fallas_sin_intervencion", ascending=False)
PR.insert(0, "prioridad", range(1, len(PR) + 1))
PR.to_csv(f"{args.out}/prioridad_rotacion.csv", index=False)


# ---------- Figuras ----------

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False})
COL = ["#8a8a8a", "#d1495b", "#edae49", "#66a182", "#2e4057"]

# Gráfica de fallas según el total de bicis

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(CURVA_B.B, CURVA_B.E_fallas, color=COL[4])
ax.axvline(B_TOTAL, ls="--", color=COL[0])
ax.text(B_TOTAL + 3, CURVA_B.E_fallas.max() * 0.9, f"B = {B_TOTAL}")
ax.set_xlabel("Bicis en la subred a las 05:00 (B)")
ax.set_ylabel("Fallas esperadas por día")
ax.set_title("P1: fallas con el mejor reparto inicial, según el total de bicis")
fig.tight_layout()
fig.savefig(f"{args.out}/fig_fallas_vs_B.png")
plt.close(fig)

# Gráfica de la frontera fallas vs bicis movidas (solo los puntos que no se pueden mejorar)

fig, ax = plt.subplots(figsize=(7, 4.5))
for R, cl in zip(range(MAX_RONDAS + 1), COL[2:]):
    sub = FR[FR.rondas == R].sort_values("E_movidas")
    fr = sub[sub.E_fallas <= sub.E_fallas.cummin()]
    ax.plot(fr.E_movidas, fr.E_fallas, "o-", ms=3, color=cl, label=f"{R} ronda(s)")
o = estr["Operador actual"]
ax.scatter(o["E_movidas"], o["E_fallas"], color=COL[1], zorder=5, s=50, label="Operador actual")
ax.set_xlabel("Bicis movidas por día (esperado)")
ax.set_ylabel("Fallas esperadas por día")
ax.set_title("P2: frontera fallas vs. bicis movidas")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(f"{args.out}/fig_frontera.png")
plt.close(fig)

# Gráfica de fallas por hora para cada estrategia

fig, ax = plt.subplots(figsize=(8, 4))
t = (T0 + np.arange(NB) * BLK) / 60
for (k, v), cl in zip(estr.items(), COL):
    ax.plot(t, v["curva"] * (60 / BLK), color=cl, label=k, lw=1.5)  # pasar de por bloque a por hora
ax.set_xlabel("Hora")
ax.set_ylabel("Fallas esperadas por hora")
ax.set_xticks(range(5, 25, 2))
ax.set_title("Fallas a lo largo del día por estrategia")
ax.legend(frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig(f"{args.out}/fig_fallas_por_hora.png")
plt.close(fig)


# Guardar todas las tablas en un markdown para copiarlas al reporte

with open(f"{args.out}/ficha_optimizacion.md", "w") as f:
    f.write("# Etapa 3 — ficha de resultados (generada por optimizacion.py)\n\n")
    f.write(f"Validación contra la Etapa 2: diferencia máxima {VAL.max_dif_abs.max():.2e} fallas.\n\n")
    f.write(f"## P1 — inventario a las 05:00 (B = {B_TOTAL})\n\n" + P1.to_markdown(index=False) + "\n\n")
    f.write(f"## P2 — política propuesta (c = {C_BASE})\n\n" + POL.to_markdown(index=False) + "\n\n")
    f.write("## Comparación de estrategias\n\n" + CMP.to_markdown(index=False) + "\n\n")
    f.write("## Prioridad y rotación\n\n" + PR.to_markdown(index=False) + "\n")


# Ver los resultados en la terminal

print(f"validación vs Etapa 2: max dif = {VAL.max_dif_abs.max():.2e}")  # tiene que ser casi 0
print(CMP.to_string(index=False))  # tabla de comparación de estrategias
print("\nPolítica propuesta:\n" + POL.to_string(index=False))  # bicis a las 05:00 y objetivos por ronda