# Etapa 3 — ficha de resultados (generada por optimizacion.py)

Validación contra la Etapa 2: diferencia máxima 1.99e-03 fallas.

## P1 — inventario a las 05:00 (B = 131)

| codigo   | nombre                               |   K |   x_05h |   x_mitad |   perdidos |   rechazados |   E_fallas |   E_fallas_mitad |
|:---------|:-------------------------------------|----:|--------:|----------:|-----------:|-------------:|-----------:|-----------------:|
| 211+212  | Isaac Newton-Horacio + Hegel-Horacio |  70 |      62 |        35 |       31.9 |          0.2 |       32.1 |             59   |
| 208      | Hesiodo-Lamartine                    |  25 |      24 |        12 |       62.5 |         35   |       97.4 |            109.4 |
| 204      | Temístocles-Homero                   |  27 |      23 |        13 |       23.4 |          0.2 |       23.6 |             33.6 |
| 210      | Eugenio Sue-Horacio                  |  27 |      22 |        13 |       23.4 |          0   |       23.4 |             32.4 |
| 217      | Euler-Horacio                        |  31 |       0 |        15 |       17.6 |         48   |       65.5 |             80   |
| 207      | Torquato Tasso-Homero                |  23 |       0 |        11 |       10.2 |         17.6 |       27.8 |             37.6 |
| 205      | Taine-Homero                         |  19 |       0 |         9 |       11.9 |         13   |       24.9 |             30.4 |
| 201      | Lope de Vega-Av. Ejército Nacional   |  19 |       0 |         9 |       16.9 |         12.4 |       29.3 |             37.7 |
| 225      | Petrarca-Presidente Masaryk          |  21 |       0 |        10 |        8.9 |         10.5 |       19.4 |             27.5 |

## P2 — política propuesta (c = 0.2)

| codigo   | nombre                               |   K |   x_05h |   objetivo_9h |   objetivo_17h |
|:---------|:-------------------------------------|----:|--------:|--------------:|---------------:|
| 211+212  | Isaac Newton-Horacio + Hegel-Horacio |  70 |      63 |            25 |             42 |
| 208      | Hesiodo-Lamartine                    |  25 |      24 |            24 |              6 |
| 204      | Temístocles-Homero                   |  27 |      23 |            16 |             19 |
| 210      | Eugenio Sue-Horacio                  |  27 |      21 |            15 |             21 |
| 217      | Euler-Horacio                        |  31 |       0 |             0 |             30 |
| 207      | Torquato Tasso-Homero                |  23 |       0 |             1 |             22 |
| 205      | Taine-Homero                         |  19 |       0 |             1 |             18 |
| 201      | Lope de Vega-Av. Ejército Nacional   |  19 |       0 |            10 |             19 |
| 225      | Petrarca-Presidente Masaryk          |  21 |       0 |             4 |             19 |

## Comparación de estrategias

| estrategia                            |   E_fallas_dia |   E_bicis_movidas_dia |   pct_viajes_fallidos |   mejora_vs_operador_pct |
|:--------------------------------------|---------------:|----------------------:|----------------------:|-------------------------:|
| Sin intervención (K/2)                |          447.6 |                   0   |                  18.6 |                    -34.3 |
| Operador actual                       |          333.2 |                 162.9 |                  13.9 |                      0   |
| P1: solo inventario 05:00             |          343.5 |                   0   |                  14.3 |                     -3.1 |
| P2: inventario + 1 ronda(s) (9h)      |          225.7 |                 146.4 |                   9.4 |                     32.3 |
| P2: inventario + 2 ronda(s) (9h, 17h) |          158   |                 253.3 |                   6.6 |                     52.6 |

## Prioridad y rotación

|   prioridad | codigo   | nombre                               |   K | tipo                   |   rotacion_viajes_por_dock_dia |   E_fallas_sin_intervencion |   E_fallas_operador |   E_fallas_propuesta |   fallas_evitadas_vs_operador |
|------------:|:---------|:-------------------------------------|----:|:-----------------------|-------------------------------:|----------------------------:|--------------------:|---------------------:|------------------------------:|
|           1 | 208      | Hesiodo-Lamartine                    |  25 | fuente (se vacía AM)   |                           23.3 |                       109.4 |                93.1 |                 62.8 |                          30.2 |
|           2 | 217      | Euler-Horacio                        |  31 | sumidero (se llena AM) |                           10.7 |                        80   |                64.2 |                 26   |                          38.2 |
|           3 | 211+212  | Isaac Newton-Horacio + Hegel-Horacio |  70 | fuente (se vacía AM)   |                            7.1 |                        59   |                26.5 |                 14.2 |                          12.3 |
|           4 | 201      | Lope de Vega-Av. Ejército Nacional   |  19 | sumidero (se llena AM) |                            7.6 |                        37.7 |                38   |                 12.7 |                          25.3 |
|           5 | 207      | Torquato Tasso-Homero                |  23 | sumidero (se llena AM) |                            7.4 |                        37.6 |                32.1 |                  7.9 |                          24.2 |
|           6 | 204      | Temístocles-Homero                   |  27 | fuente (se vacía AM)   |                            6.2 |                        33.6 |                15.1 |                 10   |                           5.2 |
|           7 | 210      | Eugenio Sue-Horacio                  |  27 | fuente (se vacía AM)   |                            5.9 |                        32.4 |                 8.6 |                  8.6 |                          -0   |
|           8 | 205      | Taine-Homero                         |  19 | sumidero (se llena AM) |                            9.8 |                        30.4 |                29   |                  9.8 |                          19.2 |
|           9 | 225      | Petrarca-Presidente Masaryk          |  21 | sumidero (se llena AM) |                            7.9 |                        27.5 |                26.6 |                  6   |                          20.6 |
