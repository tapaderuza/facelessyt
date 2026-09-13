# Episodio 05 — Guess the Output (revisión gamificada)

La fase audiovisual posterior se documenta en [PRODUCTION.md](PRODUCTION.md).
El reloj de este laboratorio sigue siendo editorial; el MP4 se retima a Piper.

**I Doubled the Workers. The Bottleneck Didn't Move.**

Este paquete sustituye íntegramente la preproducción anterior de 6 minutos y pausa
de 2 segundos. Ahora: **4:00 objetivo, 8 escenas, 669 palabras, 96 beats y cuenta
atrás de 3 segundos**. Inglés para narración, dirección en español. No hay voz
medida en este laboratorio editorial; el máster retimado y su estado de entrega
se documentan en [PRODUCTION.md](PRODUCTION.md).

## Abrir y probar

Abrir [lab.html](lab.html) en un navegador. Play inicia la línea visual; **Jump to
challenge** lleva al minuto 2. Se puede elegir A/B, buscar cualquier fotograma y
activar movimiento reducido. Los ticks requieren iniciar Play y tener sonido
activado. Las elecciones son reales en este HTML, no botones clicables del MP4.

Archivos fuente:
- [GUION.md](GUION.md): guion reescrito, con timestamps por frase y acción visible.
- [episode.yaml](episode.yaml): autoridad de escenas, cues, reto, física y comentarios.
- [renderer.js](renderer.js): estado por frame, gravedad, rebote, transiciones, efectos,
  cuenta atrás, captions provisionales y recibos calculados.
- [render-spec.json](render-spec.json): contrato regenerado, no editar manualmente.
- [simulate.py](simulate.py): motor numérico anterior, sin alterar.
- [simulation-evidence.json](simulation-evidence.json): trazas y métricas, sin chistes.
- [test_lab.cjs](test_lab.cjs): recorre los 7.200 frames usando canvas simulado.

## Historia: carreras, no clases

| Tiempo editorial | Acción |
|---|---|
| 00:00–00:30 | Entramos en una pila naranja que cae y se vacía de dos en dos |
| 00:30–01:00 | Carrera baseline: 4 workers; 12,5 s simulados como marca a batir |
| 01:00–01:30 | Quitamos workers; aparecen huecos en la puerta; 15 s |
| 01:30–02:00 | Seguimos J04 mientras prepara, espera y pasa por la herramienta |
| 02:00–02:12 | Cambio preparado 4 → 8; desafío directo; replay baseline rotulado |
| 02:12–02:15 | Simulación congelada y **3 → 2 → 1**, tres ticks discretos |
| 02:15–02:25 | Ejecución 8 workers a 1,25×: pila de seis y misma salida |
| 02:25–02:30 | Resultado: 12,5 s, atasco sin caída; respuesta B |
| 02:30–03:00 | La espera cambia de sitio; ambas colas permanecen visibles |
| 03:00–03:30 | Abrimos cuatro plazas; oleadas de cuatro; 6,5 s |
| 03:30–04:00 | Revancha con preparación más lenta; CTA sobre el experimento activo |

Pregunta exacta:

> I just doubled the workers from 4 to 8. Does the processing speed double, or does
> the system choke? Lock in your guess.

La cuenta atrás ocupa 90 frames: 3 en [132,133), 2 en [133,134), 1 en [134,135).
No se muestra 0 ni se revela respuesta durante ese intervalo. Sin voz; tres ticks
de 70 ms, a bajo nivel. El flujo se reanuda a 135 s y el resultado aparece a 145 s,
después de completar 12,5 segundos lógicos a 1,25×. Antes de congelar se conserva
un replay baseline, con **NEXT RUN: 4 -> 8**, para no anticipar el resultado nuevo.

La respuesta corrige deliberadamente la dicotomía: **TRAFFIC JAM. NOT A CRASH.**
Ni doble velocidad ni caída total: mismo tiempo de lote, más cola en la herramienta.
“Choke” es el atasco visual, no un timeout, deadlock o fallo real.

## Show, don't lecture

Se han eliminado las secciones de definiciones, explicación del heap, pseudocódigo
de semáforos y listas teóricas de limitaciones. Cada cue de voz exige un identificador
de acción visual. Los límites importantes aparecen junto al control simulado,
mientras siguen pasando trabajos. No se usan párrafos de voz sobre una diapositiva.

Las frases son objetivos editoriales. El preview divide cada cue en frases para
captions; eso **no equivale a alineación con una voz real**. Antes del render final
se deben medir las frases, retimar el flujo y revisar qué palabra coincide con cada
entrada/salida. La pausa de 90 frames se conserva después de “Lock in your guess”.

## Atasco físico y efectos

- Los jobs de la cola son bloques con ID: dos columnas, apilado desde abajo, caída
  bajo gravedad y rebote amortiguado. No se generan partículas que se hagan pasar
  por solicitudes extra.
- La física es analítica, calculada desde timestamps: mismo frame produce el mismo
  dibujo, incluso al buscar hacia atrás. Gravedad 6.000 px/s² y restitución 0,18.
- Los cambios de estado fuera de la pila se desplazan durante 180 ms.
- Cada oleada inicial de cola profunda puede producir un impulso de hasta **3 px**
  durante 350 ms. Solo vibra la zona de la cola, no captions, resultados o timer.
- Aviso ámbar localizado, periodo 2 s y opacidad máxima 0,18; **sin estrobos ni
  flashes de pantalla completa**. No hay fuego que finja un incidente real.
- Movimiento reducido desactiva caída/rebote, vibración y pulsos, sin cambiar
  resultados, IDs, contador de predicción o capacidad.
- La escena de J04 atenúa los demás jobs sin detenerlos. El contador de completados,
  las plazas y la cola no se confunden con decoración.

Los efectos son una capa de presentación; no alteran capacidad, orden FIFO,
tiempos, solicitudes o resultados. El motor sigue dando:

| Workers | Plazas | Tiempo simulado del lote | Pico de cola |
|---:|---:|---:|---:|
| 2 | 2 | 15 s | 0 |
| 4 | 2 | 12,5 s | 2 |
| 8 | 2 | 12,5 s | 6 |
| 8 | 4 | 6,5 s | 4 |

No afirmar que 4 → 8 empeora la latencia total: las terminaciones son idénticas.
La pila visible representa espera real en la traza, no un error de conexión.

## Easter eggs

Comentarios sutiles, visibles 4–5 s en una banda separada:

- `// queue.exe has entered its stacking era`
- `// Worker 4 is questioning its existence`
- `// more_workers != wider_door`
- `// TODO: negotiate with the doorway`

El prefijo **EDITORIAL** impide confundirlos con logs de una ejecución real. Se
conservan en YAML/render, nunca en los datos de evidencia o el simulador.
No se fuerza una pausa del vídeo para leerlos. No usamos “connection refused”
porque aquí no hubo una conexión rechazada.

## Evidencia de demanda y originalidad

Se conserva [selection-evidence.json](selection-evidence.json) de la selección
anterior: snapshot del 10 de septiembre, señal adyacente de Cole Medin
(`UbylWXukvR8`, 60.721 views, 4,01×, 225.000 suscriptores).
Es interés en mejoras de agentes, no validación de este ángulo de concurrencia.
El selector seguía devolviendo null; no se han cambiado sus umbrales. El nuevo
empaquetado no convierte esa señal en certeza ni promete retención.

El episodio no repite minería, temperatura temática, validación de evidencias o
memoria KV. Tampoco se añade al catálogo de publicados sin publicación real.

## Verificación y siguiente fase

```powershell
.\.venv\Scripts\python.exe production/05-worker-bottleneck/build_package.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_episode05.py -v
node production/05-worker-bottleneck/test_lab.cjs
```

El test canvas recorre los 7.200 frames: conservación de jobs, capacidad,
coordenadas, efectos acotados, 90 frames de countdown, no filtración del resultado,
determinismo y movimiento reducido. Revisa además una firma semántica de fuente:
sin contar shake, pulses, captions o logo. El cambio de fase frozen/run sí es un
cambio de estado de la interacción. Por sí solo, este test no certifica el MP4.

La revisión de navegador se documenta aparte en [QA.md](QA.md). Ese informe de
preview no certifica accesibilidad ni el audio y vídeo del máster posterior.

El máster audiovisual está [publicado en YouTube](https://www.youtube.com/watch?v=eqO9IN3eGPI),
con privacidad pública, procesado en HD y miniatura realista generada con autorización
del usuario. La duración final medida es 3:50,933. El detalle y los límites de
revisión están en [PRODUCTION.md](PRODUCTION.md).
