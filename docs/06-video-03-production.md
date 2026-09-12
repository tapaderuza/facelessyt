# Vídeo 03 — producción y decisiones

Título elegido: **Stop Trusting Your AI Agent. Make It Prove It.**

Alternativas:
1. I Built an AI Agent That Has to Prove It's Right
2. A Real Source. A Wrong Answer. I Built the Check.
3. The AI Recommendation That Should Never Reach Production

## Qué cambia respecto a los vídeos existentes

01 es el minero; 02 añade historial de temas. Este episodio implementa y demuestra
un verificador de propuestas estructuradas, independiente del uploader. No reutiliza
ninguno de los guiones previos. Incorpora un control válido, cinco fallos inyectados y
un duplicado semántico que las claves exactas no detectan.

Público: desarrolladores que convierten salidas de IA en decisiones o acciones.
Promesa: ejecutar una comprobación pequeña, leer sus rechazos y entender sus límites.
Duración editorial prevista: aproximadamente 10–12 minutos para unas 2.000 palabras.
Es una hipótesis de edición para este contenido; el minado no valida esa duración.

## Trabajo de las tres IAs

- Codex: implementación, pruebas, guion final, realización, render y control de artefactos.
- Antigravity mediante PAL clink, role=planner: revisión del brief, guardada en
  `data/video/03-proof-agent/review-antigravity.json`.
- Claude mediante PAL clink, role=planner: revisión independiente del brief, guardada
  en `data/video/03-proof-agent/review-claude.json`.

Las primeras revisiones son del brief. Claude revisó también el guion completo en
`data/video/03-proof-agent/script-review-claude.json`; se incorporó su sugerencia de
precisar en la promesa inicial que se verifican campos de salida. Su estimación de
duración asume una voz distinta: se usa la duración real de Piper. Estas revisiones
no certifican el vídeo terminado. No se reanudó
ninguna sesión previa de Claude. La ruta Windows del preset Claude perdía las barras
en el parser de PAL; el helper corrige la ruta en memoria para esta llamada.

Ambos revisores propusieron hooks que llamaban erróneo al score 12,65. Se descartó esa
parte: **12,65 es correcto**; el fallo inyectado usa **99,00**. Tampoco se incorporaron
afirmaciones de publicación automática ni de fallos espontáneos observados en modelos.

## Evidencia y alcance

- Snapshot local: `data/outliers-ai-automation-2026-09-10.json`, 26 filas.
- Primera fila: views=182319, channel_baseline=14416, ratio redondeado=12.65.
- Se comprueba consistencia con el baseline guardado; no se reconstruye la mediana
  desde todos los vídeos fuente. Tampoco se prueba causalidad ni se predicen visitas.
- Ventana elegida: 21 días, una regla de trabajo; no una frontera estadística.
- Clock del replay: 2026-09-12 UTC; el caso viejo añade 30 días. No es una fecha actual
  dinámica ni una nueva consulta de YouTube.
- Los siete ejemplos son fixtures inyectados. No son respuestas de modelos usadas
  como benchmark. Las tasas de acierto de modelos no se han medido.
- `ready_for_review` no significa autorización de subida, verdad semántica u originalidad.
- El detector de duplicados usa claves exactas normalizadas; un tema renombrado pasa.

Contexto de selección: docs/02-hallazgos-2026-09-10.md, cluster harnesses (8 outliers,
media 6,0x, 5 canales). Observación histórica; no una predicción para este canal.
Referencia conceptual consultada: [Anthropic, Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
Los números y resultados de la demo proceden del proyecto y de su ejecución local.

## Realización

- Gráficos programáticos 1920×1080, conservando el verde y fondo oscuro de la marca.
- Siete layouts: tarjetas, ecuación, números, diagrama, código, resultado y tipografía.
- Revelado de datos a 1,25 s y desplazamiento de escala suave.
- Estados coloreados y rótulos persistentes para reconocer pruebas inyectadas.
- Voz Piper Lessac del pipeline existente, sin nuevo gasto en TTS externo.
- Subtítulos visibles y SRT separado. Los bloques se estiman por longitud dentro del
  audio real de cada escena; **no hay alineación forzada palabra a palabra**.
- Capítulos calculados con las duraciones de los clips, no escritos de memoria.
- Miniatura diagramática nativa: propuesta 99x tachada, REJECTED, PROVE IT.

## Reproducción

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_proof.py -v
.\.venv\Scripts\python.exe scripts/proof_demo.py --out data/video/03-proof-agent/evidence.json
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' -w /work -e PYTHONPATH=/work/src --entrypoint python facelessyt-video scripts/render_proof.py
```

El render incluye caché por escena, código, evidencia e índice de montaje. Los vídeos
01 y 02 se mantienen intactos. Los cambios de este episodio todavía son locales;
no se debe anunciar que este código ya está publicado en GitHub.

## Evaluación después de publicar

Leer impresiones, fuentes de tráfico, CTR y retención; la captura previa no contiene
esas métricas. Comparar la caída del gancho y de las secciones de código cuando haya
muestra suficiente. Una variación de título o miniatura debe quedar fechada para
evitar atribuir cualquier cambio de views a la edición sin contexto.

No usar las primeras decenas de visitas como prueba de éxito o fracaso. Este episodio
es una prueba editorial concreta, no una garantía de crecimiento.
