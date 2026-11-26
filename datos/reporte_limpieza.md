# Reporte de limpieza — Ecobici septiembre 2026

Archivo: `trips_2026-09.csv` — 1,498,934 registros.  
Catálogo GBFS: `station_information.json` — 677 estaciones.  
**Conservados: 1,173,180 (78.3%) — Descartados: 325,754 (21.7%)**

## Reglas aplicadas (en orden)

`cumplen_regla` = registros del archivo original que cumplen la condición; `eliminados` = los que efectivamente elimina esa regla después de las anteriores.

| # | Regla | Cumplen | Eliminados | Quedan | Justificación |
|---|---|---:|---:|---:|---|
| 0 | `R0_fecha_invalida` | 0 | 0 | 1,498,934 | Fecha u hora que no se pudo interpretar. |
| 1 | `R1_fuera_del_mes` | 270 | 270 | 1,498,664 | Día de servicio fuera de 2026-09: el archivo se arma por fecha de arribo e incluye viajes iniciados en meses anteriores (algunos con duración de días o meses) y los retiros de las 00:00–00:30 del día 1, que pertenecen al último día de servicio del mes anterior. |
| 2 | `R2_duracion_no_positiva` | 0 | 0 | 1,498,664 | Arribo anterior o igual al retiro. |
| 3 | `R3_reenganche_misma_estacion` | 5,088 | 5,088 | 1,493,576 | Retiro y arribo en la misma estación en menos de 5 min: bici defectuosa devuelta de inmediato o reenganche; no es un viaje. |
| 4 | `R4_viaje_muy_corto` | 8,579 | 8,578 | 1,484,998 | Duración menor a 2 min hacia otra estación (mediana ~290 m a la estación vecina): cambio de bici o anclaje en la estación contigua, no un desplazamiento. |
| 5 | `R5_viaje_muy_largo` | 538 | 519 | 1,484,479 | Duración mayor a 180 min (3 h): olvido de anclaje, robo o falla de registro. El sistema cobra penalización desde los 45 min; el percentil 99.9 de duración es ~110 min. |
| 6 | `R6_estacion_no_en_gbfs` | 0 | 0 | 1,484,479 | Código de estación que no existe en station_information.json (estación cerrada o renombrada). |
| 7 | `R7_fin_de_semana` | 286,717 | 283,498 | 1,200,981 | Sábado o domingo (por día de servicio). El alcance del proyecto es días hábiles. |
| 8 | `R8_festivo_oficial` | 28,028 | 27,792 | 1,173,189 | Día de asueto oficial: 16/09: Día de la Independencia (asueto oficial LFT) |
| 9 | `R9_vacaciones_escolares` | 0 | 0 | 1,173,189 | Periodo vacacional escolar SEP dentro del mes (ninguno en este mes). |
| 10 | `R10_fuera_horario_operacion` | 16 | 9 | 1,173,180 | Retiro fuera del horario de operación (05:00–00:30). |

## Parámetros

- Horario de operación: 05:00–00:30 (día de servicio por hora de retiro)
- Duración mínima: 2 min; misma estación: 5 min; máxima: 180 min
- Festivos eliminados: 16/09/2026
- Vacaciones eliminadas: ninguna en el mes
- Días atípicos marcados en `dia_atipico` pero **conservados**: 15/09 (Víspera del Grito: oficinas de gobierno con jornada reducida); 25/09 (Consejo Técnico Escolar SEP (sin clases en básica))

## Registros por día de servicio

| fecha_servicio   | dia   |   conservado |   descartado |
|:-----------------|:------|-------------:|-------------:|
| 2026-02-10       | Tue   |            0 |            1 |
| 2026-05-20       | Wed   |            0 |            1 |
| 2026-06-29       | Mon   |            0 |            1 |
| 2026-08-14       | Fri   |            0 |            1 |
| 2026-08-20       | Thu   |            0 |            1 |
| 2026-08-29       | Sat   |            0 |            2 |
| 2026-08-30       | Sun   |            0 |            1 |
| 2026-08-31       | Mon   |            0 |          262 |
| 2026-09-01       | Tue   |        50092 |          470 |
| 2026-09-02       | Wed   |        52877 |          465 |
| 2026-09-03       | Thu   |        55252 |          499 |
| 2026-09-04       | Fri   |        60165 |          509 |
| 2026-09-05       | Sat   |            0 |        35824 |
| 2026-09-06       | Sun   |            0 |        32131 |
| 2026-09-07       | Mon   |        50171 |          440 |
| 2026-09-08       | Tue   |        58908 |          539 |
| 2026-09-09       | Wed   |        62221 |          556 |
| 2026-09-10       | Thu   |        57635 |          547 |
| 2026-09-11       | Fri   |        53603 |          537 |
| 2026-09-12       | Sat   |            0 |        35327 |
| 2026-09-13       | Sun   |            0 |        36082 |
| 2026-09-14       | Mon   |        50905 |          500 |
| 2026-09-15       | Tue   |        48793 |          492 |
| 2026-09-16       | Wed   |            0 |        28028 |
| 2026-09-17       | Thu   |        57417 |          454 |
| 2026-09-18       | Fri   |        56939 |          502 |
| 2026-09-19       | Sat   |            0 |        37917 |
| 2026-09-20       | Sun   |            0 |        35885 |
| 2026-09-21       | Mon   |        56373 |          486 |
| 2026-09-22       | Tue   |        57396 |          499 |
| 2026-09-23       | Wed   |        61531 |          524 |
| 2026-09-24       | Thu   |        60300 |          575 |
| 2026-09-25       | Fri   |        56771 |          586 |
| 2026-09-26       | Sat   |            0 |        37746 |
| 2026-09-27       | Sun   |            0 |        35802 |
| 2026-09-28       | Mon   |        59016 |          543 |
| 2026-09-29       | Tue   |        61006 |          559 |
| 2026-09-30       | Wed   |        45809 |          460 |

## Notas

- El archivo mensual está organizado por fecha de **arribo**: contiene viajes que iniciaron el mes anterior (eliminados por R1) y no contiene los viajes que iniciaron el último día del mes y terminaron después de medianoche (están en el archivo del mes siguiente). El último día de servicio queda ligeramente censurado en su cola nocturna.
- Los viajes de ida y vuelta a la misma estación con duración ≥ 5 min se conservan: para el modelo de inventario por estación son un retiro y un arribo reales.
- Los códigos dobles tipo `235-236` corresponden a estaciones pareadas que el GBFS publica con ese mismo código.
- Estaciones del GBFS sin viajes en el mes: 699.
