# Episodio 05 — preproducción gamificada v2

[Paquete actualizado](../production/05-worker-bottleneck/README.md).

Título: **I Doubled the Workers. The Bottleneck Didn't Move.**

Esta revisión sustituye los targets anteriores de 6 minutos/2 segundos de pausa.
Ahora son **4 minutos, 8 escenas, 669 palabras y 96 beats**. No hay capítulos de
teoría: cada frase exige una acción visible. No es una promesa de retención.

- [Guion](../production/05-worker-bottleneck/GUION.md) reescrito por cues.
- [YAML](../production/05-worker-bottleneck/episode.yaml) con pregunta exacta,
  3 segundos/90 frames de countdown, efectos y comentarios editoriales.
- [Renderer canvas](../production/05-worker-bottleneck/renderer.js) implementado:
  pila de bloques bajo gravedad, rebote amortiguado, vibración localizada,
  aviso ámbar acotado, modo reducido y resultado oculto hasta acabar la traza.
- [Preview](../production/05-worker-bottleneck/lab.html) interactivo con elección A/B,
  búsqueda por frame y ticks activados tras Play.
- Simulador numérico sin cambios: 4 → 8 workers mantiene 12,5 s y lleva el pico
  de cola de 2 a 6. Es atasco, no crash o pérdida de trabajos.
- Easter eggs solo en la capa editorial, nunca en métricas o evidencia.

Los tests recorren los 7.200 frames, además de validar el modelo y los contratos.
La fase audiovisual posterior produjo un máster de 230,933 s con voz medida,
cuenta atrás de 90 frames y ocho capítulos. Los resultados de QA y sus límites
están en [PRODUCTION.md](../production/05-worker-bottleneck/PRODUCTION.md).

Se mantiene la advertencia de demanda: un outlier adyacente de 4,01×, no validación
específica. El selector y el snapshot no cambian. Tras autorización explícita se
publicó [el Episodio 05](https://www.youtube.com/watch?v=eqO9IN3eGPI), verificado como
público y procesado en HD con JPG personalizado. Solo entonces se actualizó el
catálogo de publicados. La miniatura nueva también fue autorizada expresamente.
