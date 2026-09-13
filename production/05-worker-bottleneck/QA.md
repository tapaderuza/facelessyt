# QA — revisión gamificada del Episodio 05

Fecha: 2026-09-13. Alcance: código de preproducción y preview local.

Este informe conserva la revisión previa. La comprobación posterior del máster
con voz medida se registra en [PRODUCTION.md](PRODUCTION.md).

## Código y fuente visual

- 60 tests unittest y 17 tests core: pasan; incluyen 12 tests del Episodio 5.
- Animatic del Episodio 4: sus 13 aserciones siguen pasando.
- Renderer del Episodio 5: 7.200 fotogramas recorridos con canvas simulado,
  45.167 aserciones. Conservación de trabajos, capacidad, posiciones, efectos,
  replay determinista, ausencia de respuesta anticipada y modo reducido.
- Cuenta atrás: exactamente 90 frames, tres ticks declarados; voz vacía.
- Máximo estado de fuente sin avance: 90 frames, correspondiente a la pausa
  explícita del reto. La firma excluye shake, avisos, logo y captions; incluye
  estados de jobs, progreso de tareas y cambio de fase del minijuego.
- No se ha modificado el simulador ni introducido chistes en los datos numéricos.

Estos tests NO son un análisis de frames de un MP4 codificado ni una prueba de
sincronización con voz. Los cues actuales son targets editoriales.

## Navegador local

Se usó Edge headless con perfil dedicado bajo `data/qa-episode05/`; sin cuentas,
credenciales ni páginas de producción. Se cerró el navegador de QA al terminar.
Script reproducible: `browser_qa.cjs`, que se conecta solo al puerto de depuración
del navegador dedicado. No utilizarlo contra una sesión de usuario.

Comprobado mediante CDP:

- Carga del renderer sin excepciones JavaScript registradas.
- Jump to challenge, elección B y conservación de la elección durante countdown.
- Bloqueo de elecciones al comenzar la ejecución; resultado oculto antes de tiempo.
- Resultado visible tras acabar la traza.
- Play/pausa y cambio a movimiento reducido.
- Sin overflow horizontal de la página a 375 px.

Capturas de la cuenta atrás y la pila revisadas en escritorio; captura a 375 px
también revisada. El timer se distingue; los detalles del diagrama quedan pequeños
a ese ancho. Antes de publicar hay que revisar encuadre/tamaño de rótulos para
consumo móvil; ausencia de overflow no equivale a legibilidad de todos los datos.

Los recibos y capturas se guardan en `data/qa-episode05/` (ignorado por Git).
La prueba de navegador es un smoke test funcional, no una certificación WCAG,
medición de Core Web Vitals o escucha de los ticks.

**Regresión visual: INCONCLUSIVE**, porque no existe baseline aprobada para este
nuevo estilo. La revisión de imágenes confirma los estados inspeccionados, no
la calidad audiovisual del futuro vídeo entero.

## Pendiente antes de entregar un vídeo final

Locución y anclajes medidos, tamaño de textos/encuadre móvil, mezcla sonora,
codificación, revisión de sincronía y efectos sobre MP4, capítulos regenerados y
revisión audiovisual completa. La publicación requiere autorización específica.
No se afirma mejora demostrada de retención ni accesibilidad certificada.
