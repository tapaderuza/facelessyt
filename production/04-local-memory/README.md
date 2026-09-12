# Vídeo 4: decisión y paquete de preproducción

**Producir “Your AI Model Fits. Your Conversation Doesn't.”**

Tema: el presupuesto de memoria para IA local cambia con contexto y concurrencia,
aunque no cambien los pesos. Es una demostración de ingeniería ejecutable y
autónoma, no otro capítulo sobre nuestro minero ni una noticia de un modelo concreto.

## Por qué este y no el outlier de mayor score

Se usó el último `generated_at` del nicho, no la fecha de modificación del fichero:
`data/outliers-ai-automation-2026-09-10.json`, generado el 10 de septiembre a las
09:21:40 UTC. No se reescribió ni se sustituyó por datos actuales.

| Evidencia del cluster local | Suscriptores en snapshot | Score | Edad en snapshot |
|---|---:|---:|---:|
| IndyDevDan — `00Y-p62sk0s` | 147.000 | 5,27× | 142,8 días |
| AICodeKing — `CpMCYO2oWBI` | 132.000 | 3,69× | 14,0 días |

Mediana equilibrada por canal: **4,48×**. Cobertura observada: **0 micro, 0 pequeños,
2 medianos, 0 grandes, 0 desconocidos**. No quiere decir que ningún canal grande haya
tratado el tema: solo describe los outliers guardados, no todos los vídeos de YouTube.
La señal reciente proviene de un único vídeo; el otro tiene más de cuatro meses.

Separamos micro <10k, pequeño 10k–100k, mediano >100k–250k y grande >250k.
El documento original llamaba pequeños a todos los <=250k; aquí no usamos esa etiqueta
para presentar canales de 132k y 147k como equivalentes a nuestro canal nuevo.
No existe validación en microcanales en esta evidencia.

El selector aplica una política editorial explícita: excluye temas producidos o
adyacentes, etiquetas que son solo formatos, exige dos canales distintos <=250k,
una fuente de <=30 días al ejecutar el análisis y snapshot de <=21 días. Luego
ordena por menos canales grandes observados y mediana por canal. Los umbrales
son decisiones de selección, **no una fórmula validada de probabilidad de éxito**.

El catálogo bloquea los episodios 1 (minero), 2 (temperatura de temas) y 3
(validación/harness de evidencia). Los clusters generales de agentes/harnesses se
excluyen conservadoramente para este episodio. Los otros candidatos no pasan la
combinación de frescura y repetición en canales no grandes. El informe conserva sus
razones, fuentes y conteos; no borra los candidatos rechazados.

El snapshot apoya investigar **IA local**. El ángulo específico de memoria es nuestra
inferencia editorial: no fingimos que se haya medido su demanda por separado.
Su ventaja faceless propuesta es mostrar cálculo, código y cambios de estado que
el espectador puede reproducir, sin depender de autoridad prestada ni de carisma.
No damos por demostrado que esa propuesta vaya a superar a un presentador humano.

## Audiencia, promesa y empaquetado

Audiencia: desarrolladores y creadores técnicos que quieren probar modelos locales
y necesitan entender qué cabe en su hardware antes de invertir tiempo en instalar.
No se presupone que conozcan el canal ni los tres vídeos anteriores.

Promesa: construir un presupuesto explícito y ver qué cambia al modificar contexto
y concurrencia. No recomendar un ordenador ni prometer compatibilidad, velocidad o
calidad de un modelo que no hayamos ejecutado.

Título principal: **Your AI Model Fits. Your Conversation Doesn't.**

Alternativas:

1. Local AI Has a Memory Bill You're Not Counting
2. Before You Run AI Locally, Check This Budget
3. Why Model Size Isn't Your AI Memory Budget

Duración objetivo: **6:30**, 917 palabras, unas 141 palabras/minuto. Los timestamps
son de edición, no duraciones medidas de locución. Acortar/retimar con el audio real;
no alargar planos para cumplir el número. La duración es una decisión creativa,
no una conclusión de retención extraída de los dos vídeos de referencia.

Hook 0:00–0:30, locución lista en inglés:

> Four gibibytes of model weights. Eight available. This budget still goes red.
> The weights did not change. The conversation did.
> Watch the blue section: a longer context pushes this example from six to nine.
> This is a calculated budget, not a crash recording.
> I'm going to build the calculation, change one input at a time, and show you
> why a model that fits is not the same thing as a workload that fits.

Imagen desde el primer fotograma: 9 GiB frente a un límite de 8, etiqueta
“ILLUSTRATIVE BUDGET / NOT A HARDWARE BENCHMARK”, pesos fijos y caché que cambia
al modificar el contexto. Sin saludo, logo de entrada ni stacktrace ficticio.

| Tiempo objetivo | Acción / avance |
|---|---|
| 00:00 | Conflicto: los pesos caben, el presupuesto completo no |
| 00:30 | Tres partidas: pesos, caché, reserva |
| 00:55 | Tokens generan estado de caché en un diagrama dinámico |
| 01:35 | Construcción de la fórmula en terminal |
| 02:10 | Primer caso: 6 GiB; bajo presupuesto, no verificado |
| 02:50 | Más contexto: 9 GiB sin cambiar pesos |
| 03:30 | Reducir contexto: 7 GiB, con su contrapartida |
| 04:00 | Segunda secuencia: vuelve a 9 GiB |
| 04:35 | Límites de la calculadora, reservas y arquitecturas |
| 05:10 | Checklist del workload real y mediciones pendientes |
| 05:45 | Resultado de los cuatro casos |
| 06:10 | CTA: ejecutar el cálculo; conexión al episodio de evidencia |

Miniatura: **IT FITS?** y contenedor de memoria cuyo bloque de conversación rebasa
el techo. La jerarquía procede del análisis de las miniaturas reales; el dibujo es
propio. Ver [revisión visual](visual-review.md). CTA concreto: ejecutar la calculadora,
cambiar contexto y observar qué partida crece. Enlace de código público pendiente:
no se debe narrar ni publicar una URL inexistente. La pantalla final puede llevar
al Episodio 03, previa comprobación de su ID publicado, sin volver a subirlo.

## Archivos y ejecución

- [Guion completo](GUION.md): texto listo para locución, con capítulos.
- [Spec fuente](episode.yaml): guion + 12 escenas + beats de 3–6 s + reglas de movimiento/audio.
- [Spec JSON](render-spec.json): exportación para el renderizador; no es compatible automáticamente con el antiguo renderer de diapositivas.
- [Animatic local](animatic.html): prueba SVG del hook de 30 s, sin voz ni mezcla, con pausa y búsqueda por fotograma.
- [Evidencia](memory-evidence.json): cuatro cálculos ejecutados; no es un benchmark de LLM.
- [QA](preproduction-qa.json): comprobación estructural y hashes; no certifica un vídeo final.

Desde `D:\FacelessYT`:

```powershell
.\.venv\Scripts\python.exe -m facelessyt.memory_budget --out production/04-local-memory/memory-evidence.json
.\.venv\Scripts\python.exe production/04-local-memory/build_package.py
node production/04-local-memory/test_animatic.cjs
docker build -f Dockerfile.research -t facelessyt-research .
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' -w /work facelessyt-research research --all-thumbnails --out data/research/04-local-memory
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' -w /work --entrypoint python facelessyt-research -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests/test_core.py
```

La calculadora usa caché densa de contexto completo, 32 capas, 8 KV heads, dimensión
128 y 2 bytes por valor; dos tensores (K y V). Son inputs ilustrativos explícitos,
no las especificaciones atribuidas a GLM, Gemma u otro modelo del snapshot.
4 GiB de pesos residentes, 1 GiB de reserva y límite de 8 GiB también son supuestos.
No se descargó ni se ejecutó un modelo local. No se asignó memoria real para simular
un OOM. No sumamos RAM y VRAM como si fueran un único pool.

Base técnica comprobada: [Hugging Face, estructura y crecimiento de caché](https://huggingface.co/docs/transformers/main/en/cache_explanation),
[estrategias de caché y sus diferencias](https://huggingface.co/docs/transformers/v4.50.0/kv_cache),
[llama.cpp, documentación de rendimiento](https://github.com/ggml-org/llama.cpp/blob/master/docs/development/token_generation_performance_tips.md).
Estas fuentes apoyan el mecanismo técnico; no aportan cifras de demanda o resultados
de nuestro canal. El cálculo y la narrativa son propios y reproducibles.

## Riesgos y condiciones antes del render final

1. Solo tenemos outliers y canales semilla: ni densidad de mercado ni tasa de éxito
   por tamaño. El nuevo minero guarda no-outliers para corregir el denominador en
   futuras muestras; no rellena retroactivamente el snapshot antiguo.
2. Siguen presentes autoridad, pericia, producto/marca, antigüedad y sesgo de selección.
   Dos creadores distintos no equivalen a dos experimentos controlados.
3. Las miniaturas son actuales. OCR puede omitir titulares y contar texto de interfaz;
   contraste/saturación no son proxies de CTR. El CTR ajeno permanece null.
4. No tenemos nueva retención o CTR propios de Studio en esta tarea. “Mejor hook” es
   una hipótesis de edición que habrá que evaluar, no una caída medida ya corregida.
5. La fórmula no cubre todas las arquitecturas ni determina picos reales o velocidad.
   No introducir resultados de hardware en narración/terminal sin una captura verificable.
6. Adaptar el renderer a los tracks dinámicos del spec: el anterior montaje de imágenes
   estáticas no cumple. El animatic demuestra el movimiento del hook, no el vídeo entero.
7. Antes de publicar: locución y timings reales, subtítulos alineados, revisión completa
   de audio/vídeo, lectura móvil de miniatura y un enlace válido al código. No se
   publica ni se vuelve a subir ninguno de los tres episodios anteriores en esta tarea.

Después: observar impresiones/CTR y retención a 30 s de este vídeo cuando haya datos
suficientes y comparables. No fijar una promesa de visitas ni concluir nada a partir
de un solo suscriptor o una captura temprana del canal.
