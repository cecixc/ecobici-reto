# Etapa 2 — Modelo matemático

## Qué representa el modelo

Cada estación es una **cadena de Markov de nacimiento y muerte en tiempo continuo**. El estado X(t) es el número de bicis ancladas y va de 0 a K, donde K son los docks que reporta el GBFS.

- **Nacimiento:** llega una bici con tasa μ(t), siempre que X < K. Si X = K, el usuario no encuentra dock y lo **rechazamos**.
- **Muerte:** alguien retira una bici con tasa λ(t), siempre que X > 0. Si X = 0, el usuario se va sin bici y es un **retiro perdido**.
- λ(t) y μ(t) son constantes por **bloques de 15 minutos**: 78 bloques entre 05:00 y 00:30. Es decir, retiros y arribos son procesos de Poisson no homogéneos.

Cada estación se resuelve por separado. Como vimos en la Etapa 1, solo 7.3% de los viajes son internos, así que la subred no se puede tratar como sistema cerrado. Para cada inventario inicial x0 a las 05:00 resolvemos las ecuaciones de Kolmogorov hacia adelante, p′(t) = p(t)Q(t), con la matriz exponencial minuto a minuto. Así obtenemos la distribución completa de X(t) a lo largo del día. Comparamos esta solución contra una simulación Monte Carlo de 4,000 días y coincide: por ejemplo, para la 204 con x0 = 27 salen 19.9 retiros perdidos esperados en los dos métodos.

**Qué cantidades produce (las fallas que le importan al operador):**

- P(vacía) = P(X(t) = 0) y P(llena) = P(X(t) = K), minuto a minuto.
- E[retiros perdidos] = ∫ λ(t)·P(X(t) = 0) dt y E[arribos rechazados] = ∫ μ(t)·P(X(t) = K) dt.
- La probabilidad de tener al menos una falla en el día y la hora mediana de la primera falla. Para esto agregamos un estado absorbente: se entra ahí cuando alguien llega a una estación vacía o llena.

Estas tres son las que vamos a optimizar en la Etapa 3.

## Supuestos y cómo los probamos

Todo se calcula con `scripts/modelo.py`, con los 21 días hábiles de septiembre.

| Supuesto | Cómo se probó | Resultado | Decisión |
|---|---|---|---|
| Arribos y retiros son Poisson dentro de cada bloque | Índice de dispersión (varianza/media) de los conteos por bloque de 15 min entre los 21 días, con prueba χ² | Arribos: 1.05 (17% de las celdas rechaza). Retiros: 1.24 (33% rechaza) | Arribos: se acepta. Retiros: hay sobredispersión, y viene de la censura (ver más abajo) |
| Los tiempos entre eventos son exponenciales | Reescalamiento del tiempo: si es Poisson con tasa λ(t), los huecos Λ(tₖ) − Λ(tₖ₋₁) son Exp(1). Prueba K-S | Arribos D = 0.022. Retiros D = 0.050 con la tasa cruda y 0.039 corregida. En las que se llenan, 0.029 → 0.022 | Se acepta. Con miles de huecos el p-valor siempre sale chico; D es la distancia máxima entre distribuciones (2 a 4 puntos porcentuales). Lo que queda en las fuentes es la cola de huecos largos (`fig_qq_exponencial.png`) |
| Los viajes llegan uno por uno, no en lotes | Viajes con el mismo origen y destino que salen a menos de 1 min y llegan a menos de 2 min | 4.1% de los viajes son en grupo, casi todos de 2 personas | Se ignora en el modelo analítico. Si se quiere, la simulación de la Etapa 4 puede meter lotes |
| La tasa es constante dentro de cada hora | χ² de homogeneidad entre los 4 cuartos de cada hora | Se rechaza en 37–41% de las horas (se esperaría 5%), sobre todo entre 6–9 h y 17–19 h | Usamos **bloques de 15 min**, no de una hora |
| Todos los días hábiles son iguales | Kruskal-Wallis de los viajes diarios de la subred por día de la semana | p = 0.47 | La misma λ(t) de lunes a viernes. El 15, 25 y 30 se quedan: su volumen (0.86–0.88 del promedio) es igual al del lunes 7 |
| El volumen no cambia de un día a otro | Varianza de los viajes diarios contra la media | Hay un factor diario con desviación estándar de 7.5% (correlación media entre estaciones 0.28) | Para la Etapa 4: los escenarios multiplican λ y μ por un factor diario θ con media 1 y sd 0.075 (Poisson mixta) |
| Lo que vemos es la demanda completa | Contamos huecos sin eventos que bajo Poisson tienen probabilidad < 0.1% y comparamos con los esperados | Retiros en las que se vacían: **156 huecos contra 16 esperados**. Arribos en las que se llenan: **44 contra 10.6** | Hay censura, y justo donde esperábamos. Corregimos la tasa (ver abajo) |
| Las estaciones son independientes | Viajes internos y correlación de las series diarias | 7.3% de viajes internos; correlación 0.28 | Se modelan por separado, con una excepción: 211 y 212 |
| 211 y 212 son dos estaciones distintas | K-S de los retiros de cada una por separado contra juntas | Separadas D = 0.074 y 0.066; juntas 0.041. Cuando la 211 está vacía, la gente se va a la 212 | Agregamos un **nodo 211+212 con K = 70**. Están en la misma esquina; en la Etapa 3 conviene usar el nodo |
| K = docks del GBFS y todas las bicis sirven | Rastreo por ID de bici (ver abajo) | En 45 huecos de "vacía" había 1 o 2 bicis ancladas que nadie tomó en plena hora pico | La K efectiva puede ser menor. Hay que meterlo como sensibilidad en la Etapa 3 |

## Cómo corregimos la censura

El CSV no registra a quien llega y no encuentra bici, así que la tasa cruda de retiros es baja justo en las estaciones que se vacían. Lo corregimos así:

1. Estimamos λ(t) por bloque de 15 min.
2. Marcamos los huecos entre retiros con Λ > 6.9 (probabilidad de 0.1% de no ver ningún retiro).
3. Quitamos esos minutos de la exposición y volvemos a estimar λ = retiros / minutos expuestos. Repetimos 4 veces. Hacemos lo mismo con los arribos para detectar estaciones llenas.

Si faltan retiros y arribos al mismo tiempo, no es una estación vacía ni llena: la estación estaba **fuera de servicio**. Esos minutos tampoco cuentan como exposición, pero no los contamos como falla. Pasa sobre todo en la 211, unos 31 min por día.

**Verificación con el ID de la bici.** Si una bici llega a la estación A y su siguiente viaje sale de A, sabemos que estuvo anclada ahí todo ese tiempo. Con eso armamos una cota inferior del inventario minuto a minuto, y con ella revisamos cada hueco:

- Un hueco de "vacía" con 3 o más bicis ancladas todo el tiempo no es censura. Tampoco lo es si en ese hueco llegaron 3 o más bicis y nadie las tomó. En los dos casos lo dejamos como demanda normal.
- Con 1 o 2 bicis quietas en plena demanda, lo más probable es que estén dañadas. Esos sí cuentan como vacía, de bicis útiles.
- Para estaciones llenas aplicamos lo mismo al revés. Además, los minutos en que las bicis confirmadas ya son ≥ K cuentan como llena segura. En la 225 eso pasa unos 52 min por día.

**Con esta regla, 109 huecos no pasaron la verificación y se quedaron sin corregir.** Por eso preferimos una corrección conservadora.

Resultado de la corrección:

| | Cruda (viajes/día) | Corregida | Demanda que no se ve |
|---|---|---|---|
| Retiros en las que se vacían (5) | 758 | 815 | ~46 retiros/día |
| Arribos en las que se llenan (5) | 494 | 521 | ~25 arribos/día |

Estas cifras son una **cota inferior**, porque solo detectamos huecos largos. La censura está concentrada en dos franjas: de 7 a 9 h, las fuentes vacías y luego los sumideros llenos; y de 18 a 20 h, otra vez las fuentes vacías (`fig_censura_por_hora.png`).

## Lo que hoy hace el operador

Con el mismo rastreo por bici, si una bici llega a A y su siguiente viaje sale de B ≠ A, alguien la movió. Así reconstruimos la redistribución actual, aunque nadie la publique:

- El operador mete en neto **124 bicis por día** a las cinco que se vacían y saca 33 de las que se llenan.
- La 211 recibe +35, la 210 +31, la 208 +24, la 204 +23 y la 212 +11.
- La mayoría las mete entre 8 y 9 h (`fig_operador_actual.png`).

Esta es la **política actual** contra la que vamos a comparar en la Etapa 3. Ya no tenemos que suponerla.

## Qué dice el modelo sin redistribución

Probamos el mejor inventario posible a las 05:00, que es poner las fuentes llenas y los sumideros vacíos. Aun así:

- La subred tendría **~361 fallas esperadas al día**: 195 en las fuentes y 167 en los sumideros. Es ~17% de los 2,156 viajes diarios.
- Con todas las estaciones a la mitad serían 475.
- En casi todas las estaciones la probabilidad de al menos una falla es prácticamente 1, y la primera falla llega entre las 07:47 y las 09:10.

Esto quiere decir que **ningún inventario inicial resuelve el día solo**: hacen falta movimientos durante el día, y eso es la Etapa 3.

Dos cosas salen directo del modelo:

1. **La 208 hay que vaciarla en la tarde.** Aunque empiece llena, en la tarde se satura igual (35 arribos rechazados al día). Necesita bicis en la mañana y quitarle bicis en la tarde.
2. **Juntar 211 y 212 baja a la mitad las fallas de esa esquina.** Por separado tienen 58 fallas esperadas; como nodo de 70 docks, 27.

Figuras: `fig_prob_falla.png` y `fig_fallas_vs_inventario.png`.

## Dónde deja de ser válido

- **La λ corregida es una cota inferior.** Los huecos cortos de estación vacía no se detectan.
- **Un usuario rechazado en una estación llena aparece como arribo en la vecina.** Eso infla un poco la μ de las vecinas, y el modelo no lo reacomoda.
- **Las estaciones no están acopladas en el modelo.** Un retiro perdido en la 208 no se convierte en el arribo que iba a llegar a la 217. Con 7.3% de viajes internos el efecto es chico.
- **Las tasas no dependen del estado.** Suponemos que la gente no deja de ir a una estación porque "siempre está vacía". Si eso pasa, hay demanda latente que ningún dato registra. Esto importa para la Etapa 5, porque al mejorar el servicio podría haber más viajes de los que estimamos.
- **La capacidad efectiva puede ser menor que K** por bicis dañadas o docks bloqueados.
- **Es un solo mes, en temporada de lluvias.** Falta revisar la estabilidad contra septiembre 2025.

## Para la Activity 2 (menos de 10 min)

1. **Qué es:** una cadena de nacimiento y muerte por estación, de 0 a K bicis, con λ(t) y μ(t) por bloques de 15 min. Una diapositiva con el diagrama de estados.
2. **Supuestos probados:** Poisson y exponencial se aceptan para arribos y casi para retiros. Las tasas cambian dentro de la hora, por eso los bloques de 15 min. El día de la semana no importa.
3. **El hallazgo fuerte:** la censura se ve en los datos (156 huecos contra 16 esperados) y la verificamos con el ID de la bici.
4. **La política actual del operador** reconstruida: +124 bicis por día a las fuentes, entre 8 y 9 h.
5. **Las cantidades de falla** que salen del modelo y por qué ningún inventario inicial alcanza.
