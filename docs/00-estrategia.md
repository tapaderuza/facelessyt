# Estrategia — FacelessYT

## Decisiones tomadas (asunciones, revisables)

| Decisión | Elección | Por qué |
|---|---|---|
| Idioma | **Inglés** | RPM 5–10x superior al español. Un canal en español-LATAM necesita ~20x más views para el mismo ingreso. |
| Formato | **Long-form 20–30 min** | Ahí está el RPM. Shorts pagan $0,05–0,15 por 1.000 views: sirven para descubrimiento, no para ingresos. (Corregido el 2026-09-10: asumí 8–15 min, pero la mediana de los outliers reales del nicho es de 28 min — ver docs/02-hallazgos.) |
| Nicho | **AI automation / indie software business** | RPM alto (anunciantes B2B software), material fuente abundante, afiliación SaaS recurrente, y es el único nicho donde tienes ventaja real: sabes construir. |
| Modelo de ingresos | **Canal como distribución, no AdSense** | AdSense es el suelo, no el objetivo. 40k views/mes bien nicheadas vendiendo algo tuyo > 400k views/mes de entretenimiento. |
| Cara | **Faceless por pantalla**, no por stock footage | Screen recording + voz. Es el faceless que YouTube sí monetiza porque hay trabajo real detrás. |

## El riesgo principal, dicho claro

El nicho de "AI automation" está saturado de canales que **hablan** de construir sin construir nada.
La diferenciación no es el tema, es la prueba: código real, números reales, builds que existen.
Si el vídeo no puede enseñar algo que funciona en pantalla, no se hace.

## Modelo de ingresos, por orden de importancia

1. **Afiliación SaaS recurrente** (20–30% recurrente): la palanca más rápida. Empieza a pagar mucho antes que AdSense.
2. **Producto propio**: plantillas, el propio pipeline, o Pliegora si el público encaja.
3. **AdSense**: $8–18 RPM en este nicho. Llega tarde (1.000 subs + 4.000 horas) y es el ingreso menos controlable.
4. **Servicio / consultoría**: el más rentable por hora, el que menos escala. Opcional.
5. **Venta del canal**: 2–3x beneficio anual. Es la salida, no el plan.

## Test de 90 días

- 1 canal, 1 nicho, **24 vídeos** (2/semana).
- Cero gasto en herramientas de pago hasta pasar el corte.
- Todo lo mecánico automatizado; el ángulo editorial, el título y la miniatura los decides tú (ahí se gana o se pierde y no se automatiza bien).

### Métrica de corte (día 90)

**PASA si: ≥3 de los 24 vídeos superan 10.000 views orgánicas Y la mediana de views del canal sube entre el primer y el último tercio.**

Si pasa → hay señal de formato, escalar es cuestión de volumen.
Si no pasa → se mata el canal. Has perdido 90 días, no 2 años.

### Métricas de diagnóstico (para saber POR QUÉ falla)

| Métrica | Umbral | Si falla, el problema es |
|---|---|---|
| CTR de miniatura | > 4% | El packaging (título + miniatura). Arreglable. |
| Retención a 30s | > 55% | El gancho / los primeros segundos. Arreglable. |
| Retención media | > 40% | El guion o el ritmo. Arreglable. |
| Las tres bien y aún así no crece | — | El nicho o la demanda del tema. No arreglable: se pivota. |

> CTR y retención requieren la **YouTube Analytics API** (OAuth), no la Data API.
> Fase 1 mide solo views (suficiente para el corte). Fase 2 añade OAuth para el diagnóstico.
