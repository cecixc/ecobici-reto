# Etapa 2 — salidas de modelo.py

21 días hábiles, bloques de 15 min, umbral de hueco Λ > 6.9 (p = 0.0010).

## Pruebas

- Viajes en grupo: 4.1% de los eventos. Internos: 7.3%.
- Dispersión 15 min (mediana var/media): viajes ret 1.29, arr 1.06; grupos ret 1.26, arr 1.01.
- Cuartos de hora homogéneos: rechazo medio 43% (esperado 5%).
- Kruskal día de semana p = 0.470. Factor diario sd = 0.075. Corr media series diarias = 0.28.
- Fracción de cadenas de bici con cambio de estación sin viaje (operador): 9.2%.

| prueba                        | codigo   | tipo   |     n |   estadistico |   frac_rechazo_5pct |    p_valor |   esperado |
|:------------------------------|:---------|:-------|------:|--------------:|--------------------:|-----------:|-----------:|
| dispersion_15min_viajes       | 201      | arr    |    22 |        0.983  |               0.136 | nan        |     nan    |
| dispersion_15min_viajes       | 201      | ret    |    28 |        1.29   |               0.357 | nan        |     nan    |
| dispersion_15min_viajes       | 204      | arr    |    28 |        1.132  |               0.107 | nan        |     nan    |
| dispersion_15min_viajes       | 204      | ret    |    33 |        1.563  |               0.485 | nan        |     nan    |
| dispersion_15min_viajes       | 205      | arr    |    41 |        0.95   |               0.049 | nan        |     nan    |
| dispersion_15min_viajes       | 205      | ret    |    32 |        1.166  |               0.25  | nan        |     nan    |
| dispersion_15min_viajes       | 207      | arr    |    40 |        1.06   |               0.25  | nan        |     nan    |
| dispersion_15min_viajes       | 207      | ret    |    32 |        1.096  |               0.25  | nan        |     nan    |
| dispersion_15min_viajes       | 208      | arr    |    67 |        1.112  |               0.164 | nan        |     nan    |
| dispersion_15min_viajes       | 208      | ret    |    70 |        1.471  |               0.429 | nan        |     nan    |
| dispersion_15min_viajes       | 210      | arr    |    24 |        1.01   |               0.167 | nan        |     nan    |
| dispersion_15min_viajes       | 210      | ret    |    40 |        1.189  |               0.225 | nan        |     nan    |
| dispersion_15min_viajes       | 211      | arr    |    45 |        1.396  |               0.267 | nan        |     nan    |
| dispersion_15min_viajes       | 211      | ret    |    53 |        1.4    |               0.472 | nan        |     nan    |
| dispersion_15min_viajes       | 211+212  | arr    |    62 |        1.255  |               0.242 | nan        |     nan    |
| dispersion_15min_viajes       | 211+212  | ret    |    71 |        1.405  |               0.38  | nan        |     nan    |
| dispersion_15min_viajes       | 212      | arr    |    47 |        1.038  |               0.255 | nan        |     nan    |
| dispersion_15min_viajes       | 212      | ret    |    50 |        1.52   |               0.46  | nan        |     nan    |
| dispersion_15min_viajes       | 217      | arr    |    56 |        1.022  |               0.179 | nan        |     nan    |
| dispersion_15min_viajes       | 217      | ret    |    52 |        1.159  |               0.288 | nan        |     nan    |
| dispersion_15min_viajes       | 225      | arr    |    35 |        1.13   |               0.057 | nan        |     nan    |
| dispersion_15min_viajes       | 225      | ret    |    32 |        1.084  |               0.312 | nan        |     nan    |
| dispersion_15min_grupos       | 201      | arr    |    22 |        0.946  |               0.091 | nan        |     nan    |
| dispersion_15min_grupos       | 201      | ret    |    28 |        1.271  |               0.357 | nan        |     nan    |
| dispersion_15min_grupos       | 204      | arr    |    27 |        1.043  |               0.074 | nan        |     nan    |
| dispersion_15min_grupos       | 204      | ret    |    32 |        1.493  |               0.406 | nan        |     nan    |
| dispersion_15min_grupos       | 205      | arr    |    41 |        0.913  |               0.049 | nan        |     nan    |
| dispersion_15min_grupos       | 205      | ret    |    32 |        1.133  |               0.188 | nan        |     nan    |
| dispersion_15min_grupos       | 207      | arr    |    38 |        1.006  |               0.184 | nan        |     nan    |
| dispersion_15min_grupos       | 207      | ret    |    32 |        1.075  |               0.219 | nan        |     nan    |
| dispersion_15min_grupos       | 208      | arr    |    67 |        1.055  |               0.119 | nan        |     nan    |
| dispersion_15min_grupos       | 208      | ret    |    70 |        1.457  |               0.429 | nan        |     nan    |
| dispersion_15min_grupos       | 210      | arr    |    24 |        0.981  |               0.167 | nan        |     nan    |
| dispersion_15min_grupos       | 210      | ret    |    40 |        1.118  |               0.225 | nan        |     nan    |
| dispersion_15min_grupos       | 211      | arr    |    45 |        1.342  |               0.267 | nan        |     nan    |
| dispersion_15min_grupos       | 211      | ret    |    52 |        1.468  |               0.481 | nan        |     nan    |
| dispersion_15min_grupos       | 211+212  | arr    |    62 |        1.211  |               0.21  | nan        |     nan    |
| dispersion_15min_grupos       | 211+212  | ret    |    70 |        1.265  |               0.357 | nan        |     nan    |
| dispersion_15min_grupos       | 212      | arr    |    46 |        1.003  |               0.196 | nan        |     nan    |
| dispersion_15min_grupos       | 212      | ret    |    50 |        1.434  |               0.44  | nan        |     nan    |
| dispersion_15min_grupos       | 217      | arr    |    56 |        0.995  |               0.179 | nan        |     nan    |
| dispersion_15min_grupos       | 217      | ret    |    51 |        1.155  |               0.275 | nan        |     nan    |
| dispersion_15min_grupos       | 225      | arr    |    35 |        1.087  |               0.057 | nan        |     nan    |
| dispersion_15min_grupos       | 225      | ret    |    32 |        1.082  |               0.281 | nan        |     nan    |
| ks_exponencial_cruda          | 211      | ret    |  2979 |        0.0735 |             nan     |   0        |     nan    |
| ks_exponencial_corregida      | 211      | ret    |  2947 |        0.0397 |             nan     |   0.0002   |     nan    |
| ks_exponencial_cruda          | 211      | arr    |  2078 |        0.0525 |             nan     |   0        |     nan    |
| ks_exponencial_corregida      | 211      | arr    |  2072 |        0.0467 |             nan     |   0.0002   |     nan    |
| ks_exponencial_cruda          | 212      | ret    |  2610 |        0.0663 |             nan     |   0        |     nan    |
| ks_exponencial_corregida      | 212      | ret    |  2601 |        0.058  |             nan     |   0        |     nan    |
| ks_exponencial_cruda          | 212      | arr    |  2221 |        0.0228 |             nan     |   0.1972   |     nan    |
| ks_exponencial_corregida      | 212      | arr    |  2218 |        0.0208 |             nan     |   0.2866   |     nan    |
| ks_exponencial_cruda          | 208      | ret    |  6057 |        0.0471 |             nan     |   0        |     nan    |
| ks_exponencial_corregida      | 208      | ret    |  6029 |        0.0393 |             nan     |   0        |     nan    |
| ks_exponencial_cruda          | 208      | arr    |  5496 |        0.0063 |             nan     |   0.98     |     nan    |
| ks_exponencial_corregida      | 208      | arr    |  5478 |        0.0085 |             nan     |   0.8173   |     nan    |
| ks_exponencial_cruda          | 204      | ret    |  1901 |        0.0779 |             nan     |   0        |     nan    |
| ks_exponencial_corregida      | 204      | ret    |  1881 |        0.053  |             nan     |   0.0001   |     nan    |
| ks_exponencial_cruda          | 204      | arr    |  1282 |        0.0239 |             nan     |   0.4498   |     nan    |
| ks_exponencial_corregida      | 204      | arr    |  1279 |        0.0279 |             nan     |   0.2685   |     nan    |
| ks_exponencial_cruda          | 210      | ret    |  1914 |        0.0542 |             nan     |   0        |     nan    |
| ks_exponencial_corregida      | 210      | ret    |  1899 |        0.0389 |             nan     |   0.0062   |     nan    |
| ks_exponencial_cruda          | 210      | arr    |  1154 |        0.0174 |             nan     |   0.8717   |     nan    |
| ks_exponencial_corregida      | 210      | arr    |  1154 |        0.0174 |             nan     |   0.8717   |     nan    |
| ks_exponencial_cruda          | 217      | ret    |  2967 |        0.0295 |             nan     |   0.0112   |     nan    |
| ks_exponencial_corregida      | 217      | ret    |  2959 |        0.0271 |             nan     |   0.0253   |     nan    |
| ks_exponencial_cruda          | 217      | arr    |  3481 |        0.028  |             nan     |   0.0083   |     nan    |
| ks_exponencial_corregida      | 217      | arr    |  3447 |        0.0202 |             nan     |   0.12     |     nan    |
| ks_exponencial_cruda          | 207      | ret    |  1609 |        0.0521 |             nan     |   0.0003   |     nan    |
| ks_exponencial_corregida      | 207      | ret    |  1604 |        0.0455 |             nan     |   0.0025   |     nan    |
| ks_exponencial_cruda          | 207      | arr    |  1788 |        0.0279 |             nan     |   0.1206   |     nan    |
| ks_exponencial_corregida      | 207      | arr    |  1783 |        0.0267 |             nan     |   0.1541   |     nan    |
| ks_exponencial_cruda          | 205      | ret    |  1784 |        0.033  |             nan     |   0.0398   |     nan    |
| ks_exponencial_corregida      | 205      | ret    |  1774 |        0.0246 |             nan     |   0.2276   |     nan    |
| ks_exponencial_cruda          | 205      | arr    |  1829 |        0.0138 |             nan     |   0.8747   |     nan    |
| ks_exponencial_corregida      | 205      | arr    |  1789 |        0.0227 |             nan     |   0.3101   |     nan    |
| ks_exponencial_cruda          | 201      | ret    |  1420 |        0.0406 |             nan     |   0.0178   |     nan    |
| ks_exponencial_corregida      | 201      | ret    |  1412 |        0.0215 |             nan     |   0.5237   |     nan    |
| ks_exponencial_cruda          | 201      | arr    |  1369 |        0.0233 |             nan     |   0.4395   |     nan    |
| ks_exponencial_corregida      | 201      | arr    |  1352 |        0.0118 |             nan     |   0.9907   |     nan    |
| ks_exponencial_cruda          | 225      | ret    |  1597 |        0.0216 |             nan     |   0.4414   |     nan    |
| ks_exponencial_corregida      | 225      | ret    |  1591 |        0.0176 |             nan     |   0.7026   |     nan    |
| ks_exponencial_cruda          | 225      | arr    |  1606 |        0.0296 |             nan     |   0.1181   |     nan    |
| ks_exponencial_corregida      | 225      | arr    |  1546 |        0.0243 |             nan     |   0.3159   |     nan    |
| ks_exponencial_cruda          | 211+212  | ret    |  5593 |        0.0409 |             nan     |   0        |     nan    |
| ks_exponencial_corregida      | 211+212  | ret    |  5572 |        0.0333 |             nan     |   0        |     nan    |
| ks_exponencial_cruda          | 211+212  | arr    |  4314 |        0.0238 |             nan     |   0.0147   |     nan    |
| ks_exponencial_corregida      | 211+212  | arr    |  4306 |        0.0221 |             nan     |   0.0289   |     nan    |
| cuartos_de_hora_homogeneos    | 201      | arr    |    13 |      nan      |               0.385 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 201      | ret    |    15 |      nan      |               0.2   | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 204      | arr    |    13 |      nan      |               0.308 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 204      | ret    |    15 |      nan      |               0.533 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 205      | arr    |    12 |      nan      |               0.25  | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 205      | ret    |    15 |      nan      |               0.667 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 207      | arr    |    15 |      nan      |               0.4   | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 207      | ret    |    15 |      nan      |               0.333 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 208      | arr    |    18 |      nan      |               0.667 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 208      | ret    |    19 |      nan      |               0.579 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 210      | arr    |    13 |      nan      |               0.462 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 210      | ret    |    16 |      nan      |               0.312 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 211      | arr    |    17 |      nan      |               0.412 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 211      | ret    |    18 |      nan      |               0.333 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 211+212  | arr    |    18 |      nan      |               0.611 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 211+212  | ret    |    19 |      nan      |               0.474 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 212      | arr    |    15 |      nan      |               0.4   | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 212      | ret    |    18 |      nan      |               0.389 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 217      | arr    |    16 |      nan      |               0.5   | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 217      | ret    |    16 |      nan      |               0.375 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 225      | arr    |    13 |      nan      |               0.462 | nan        |     nan    |
| cuartos_de_hora_homogeneos    | 225      | ret    |    14 |      nan      |               0.357 | nan        |     nan    |
| kruskal_dia_semana            | subred   | ambos  |    21 |        3.55   |             nan     |   0.4703   |     nan    |
| factor_diario_sd              | subred   | ambos  |    21 |        0.075  |             nan     | nan        |     nan    |
| corr_media_series_diarias     | subred   | ambos  |    20 |        0.281  |             nan     | nan        |     nan    |
| huecos_improbables_obs_vs_esp | 211      | ret    |  3093 |       42      |             nan     |   0        |       3.12 |
| huecos_improbables_obs_vs_esp | 211      | arr    |  2165 |       14      |             nan     |   0        |       2.18 |
| huecos_improbables_obs_vs_esp | 212      | ret    |  2710 |       22      |             nan     |   0        |       2.73 |
| huecos_improbables_obs_vs_esp | 212      | arr    |  2308 |        4      |             nan     |   0.205953 |       2.33 |
| huecos_improbables_obs_vs_esp | 208      | ret    |  6246 |       40      |             nan     |   0        |       6.29 |
| huecos_improbables_obs_vs_esp | 208      | arr    |  5679 |       17      |             nan     |   0.000101 |       5.72 |
| huecos_improbables_obs_vs_esp | 204      | ret    |  1985 |       28      |             nan     |   0        |       2    |
| huecos_improbables_obs_vs_esp | 204      | arr    |  1361 |        3      |             nan     |   0.159681 |       1.37 |
| huecos_improbables_obs_vs_esp | 210      | ret    |  1997 |       24      |             nan     |   0        |       2.01 |
| huecos_improbables_obs_vs_esp | 210      | arr    |  1215 |        4      |             nan     |   0.03593  |       1.22 |
| huecos_improbables_obs_vs_esp | 217      | ret    |  3085 |       13      |             nan     |   2.3e-05  |       3.11 |
| huecos_improbables_obs_vs_esp | 217      | arr    |  3606 |       24      |             nan     |   0        |       3.63 |
| huecos_improbables_obs_vs_esp | 207      | ret    |  1679 |       10      |             nan     |   1.2e-05  |       1.69 |
| huecos_improbables_obs_vs_esp | 207      | arr    |  1858 |        5      |             nan     |   0.041879 |       1.87 |
| huecos_improbables_obs_vs_esp | 205      | ret    |  1855 |       15      |             nan     |   0        |       1.87 |
| huecos_improbables_obs_vs_esp | 205      | arr    |  1904 |        5      |             nan     |   0.045626 |       1.92 |
| huecos_improbables_obs_vs_esp | 201      | ret    |  1483 |       10      |             nan     |   4e-06    |       1.49 |
| huecos_improbables_obs_vs_esp | 201      | arr    |  1424 |        7      |             nan     |   0.000718 |       1.44 |
| huecos_improbables_obs_vs_esp | 225      | ret    |  1671 |        9      |             nan     |   6.7e-05  |       1.68 |
| huecos_improbables_obs_vs_esp | 225      | arr    |  1688 |        3      |             nan     |   0.243078 |       1.7  |
| huecos_improbables_obs_vs_esp | 211+212  | ret    |  5782 |       47      |             nan     |   0        |       5.83 |
| huecos_improbables_obs_vs_esp | 211+212  | arr    |  4452 |       14      |             nan     |   0.000244 |       4.49 |
| frac_viajes_internos          | subred   | ambos  | 45279 |        0.0733 |             nan     | nan        |     nan    |
| frac_viajes_en_grupo          | subred   | ambos  | 58784 |        0.041  |             nan     | nan        |     nan    |

## Resumen por estación

|                                          | 211   | 212   | 208   | 204   | 210   | 217   | 207   | 205   | 201   | 225   | 211+212   |
|:-----------------------------------------|:------|:------|:------|:------|:------|:------|:------|:------|:------|:------|:----------|
| K                                        | 35    | 35    | 25    | 27    | 27    | 31    | 23    | 19    | 19    | 21    | 70        |
| lambda_dia                               | 169.2 | 132.0 | 309.3 | 103.4 | 101.1 | 149.5 | 80.9  | 91.3  | 73.9  | 81.0  | 283.3     |
| mu_dia                                   | 106.1 | 110.2 | 274.4 | 65.3  | 56.9  | 181.4 | 90.1  | 94.0  | 70.1  | 85.0  | 214.4     |
| lambda_cruda_dia                         | 146.3 | 128.0 | 296.4 | 93.5  | 94.1  | 145.9 | 79.0  | 87.3  | 69.6  | 78.6  | 274.3     |
| mu_cruda_dia                             | 102.1 | 108.9 | 269.4 | 63.8  | 56.9  | 170.7 | 87.5  | 89.7  | 66.8  | 79.4  | 211.0     |
| retiros_no_vistos_dia                    | 14.5  | 4.0   | 11.0  | 9.9   | 7.0   | 2.1   | 1.9   | 2.9   | 4.2   | 1.6   | 7.5       |
| arribos_no_vistos_dia                    | 1.6   | 1.3   | 2.7   | 1.5   | 0.0   | 9.9   | 2.7   | 3.7   | 3.3   | 5.2   | 1.5       |
| min_vacia_dia                            | 43.2  | 11.7  | 29.0  | 50.2  | 61.2  | 12.8  | 17.0  | 29.9  | 25.6  | 12.5  | 12.8      |
| min_llena_dia                            | 9.2   | 8.0   | 4.6   | 13.2  | 0.0   | 18.8  | 12.8  | 14.1  | 20.4  | 2.5   | 4.7       |
| min_fuera_servicio_dia                   | 31.0  | 0.0   | 6.5   | 0.0   | 0.0   | 7.2   | 0.0   | 6.9   | 0.0   | 9.5   | 6.4       |
| x0_optimo                                | 33    | 34    | 25    | 27    | 27    | 0     | 0     | 1     | 0     | 0     | 68        |
| fallas_esp_x0_opt                        | 50.3  | 7.7   | 96.6  | 20.6  | 19.5  | 65.5  | 27.8  | 24.5  | 29.3  | 19.4  | 27.3      |
| perdidos_x0_opt                          | 48.4  | 5.1   | 61.6  | 19.9  | 19.0  | 17.6  | 10.2  | 11.2  | 16.9  | 8.9   | 26.5      |
| rechazados_x0_opt                        | 1.9   | 2.6   | 35.1  | 0.7   | 0.5   | 48.0  | 17.6  | 13.3  | 12.4  | 10.5  | 0.8       |
| fallas_esp_mitad                         | 65.3  | 21.1  | 109.4 | 33.6  | 32.4  | 80.0  | 37.6  | 30.4  | 37.7  | 27.5  | 59.0      |
| p_alguna_falla_x0_opt                    | 1.0   | 0.806 | 1.0   | 0.992 | 0.972 | 1.0   | 0.999 | 0.998 | 1.0   | 0.993 | 0.981     |
| hora_mediana_1a_falla                    | 07:47 | 08:59 | 07:55 | 08:29 | 08:37 | 08:58 | 08:58 | 08:52 | 08:36 | 09:10 | 08:24     |
| operador_neto_dia                        | 35.0  | 11.3  | 23.9  | 23.2  | 30.6  | -24.0 | -8.4  | -2.2  | 3.0   | -1.4  | 46.3      |
| min_llena_confirmada_dia                 | 0.0   | 0.0   | 0.9   | 0.0   | 0.0   | 7.1   | 0.0   | 25.5  | 10.6  | 52.1  | 0.0       |
| episodios_vacia                          | 25    | 5     | 16    | 12    | 14    | 4     | 2     | 4     | 4     | 2     | 11        |
| episodios_vacia_bicis_sin_usar           | 6     | 4     | 9     | 8     | 2     | 3     | 3     | 4     | 4     | 2     | 7         |
| huecos_no_explicados                     | 18    | 14    | 23    | 8     | 12    | 11    | 5     | 8     | 3     | 7     | 37        |
| episodios_llena                          | 6     | 3     | 6     | 3     | 0     | 19    | 5     | 4     | 6     | 1     | 6         |
| mediana_max_confirmadas_sobre_K_en_llena | 0.19  | 0.09  | 0.22  | 0.15  | nan   | 0.61  | 0.56  | 0.89  | 0.87  | 0.86  | 0.17      |
| bicis_confirmadas_05h_mediana            | 2.0   | 1.0   | 8.0   | 5.0   | 1.0   | 1.0   | 0.0   | 0.0   | 0.0   | 0.0   | 3.0       |

Hora (cota superior) a la que el operador mete bicis en la subred, mismo día y ventana < 2 h:

|           |   7 |   8 |   9 |   10 |   11 |   12 |   13 |   14 |   15 |   16 |   17 |   18 |   19 |   20 |   21 |   22 |   23 |
|:----------|----:|----:|----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|
| bicis_mes | 237 | 817 | 597 |  240 |   62 |   16 |   15 |    6 |    6 |   29 |  121 |  115 |   39 |   44 |  143 |   13 |    1 |
