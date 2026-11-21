# GRIT CLAYMORE — v1.14 «Suministros»

**ZX Spectrum 48K · 21 de noviembre de 2026 · © Tony C. Ware**

La nueva edición afina la colocación de enemigos y suministros, conserva el desafío del arcade y mejora la claridad del combate contra mechas sin alterar los jefes aprobados.

## Cambios jugables

- **Soldados:** posiciones de entrada transitables, con salida para que no queden incrustados en los decorados. Refuerzos y emboscadas al avanzar por Jungla y Laboratorio.
- **Mechas:** destello de carga, puntería fijada durante el aviso, ráfagas de tres tiros sin seguir al jugador entre proyectiles, turnos coordinados y formación en V o escalonada.
- **Raciones:** buscan huecos 2×2 utilizables y se pueden recoger desde el tanque o durante el scroll. 12 iniciales más 2 refuerzos en Laboratorio y 3 en Complejo.
- **Plasma:** 3 cajas, una por sector del Complejo antes del jefe Hind; cada caja entrega 12 disparos.
- **Conservado:** tres fases, lancha, camión, Hind, tanque, beeper, efectos, controles, dificultad progresiva y puntuación.

## Material publicado

- `GRIT_CLAYMORE_V1.14_48K.tap` — juego para Spectrum 48K.
- `GRIT_CLAYMORE_V1.14_JUEGO.zip` — TAP e instrucciones de carga.
- `GRIT_CLAYMORE_V1.14_COMPLETO_CON_FUENTES.zip` — fuentes, gráficos, pruebas, licencias y documentación vigente.
- `GRIT_CLAYMORE_MANUAL_V1_14_OFICIAL.pdf` — manual de 11 páginas con carátula oficial y actualización v1.14.
- `GRIT_CLAYMORE_ATLAS_VISUAL_V1_14.pdf` — atlas de 6 páginas, capturas del proyecto y actualización v1.14.
- `GRIT_CLAYMORE_CARATULA_OFICIAL.png` — carátula expresionista oficial, sin cambios.
- `GRIT_CLAYMORE_CARATULAS_ALTERNATIVAS.zip` — tres portadas aprobadas, incluida la militar clásica.

**Integridad:** SHA-256 del TAP v1.14: `3088339d7a9f822c072f0377abc9872db931b7daa4a6de8498b252c61b7727f3`.

### Verificación

El código fuente recompila exactamente el TAP recibido. Se han superado las comprobaciones específicas de soldados, raciones, plasma, jefes y mechas mediante el intérprete Z80 parcial del proyecto. GitHub Actions comprobó satisfactoriamente la compilación y las regresiones de la v1.14 tanto en la Pull Request como en `main`, verificando la identidad exacta del TAP. La batería histórica extensa permanece disponible con `python3 build_all.py`; la verificación de publicación usa `python3 build_all.py --ci`. **No se afirma certificación sobre hardware físico ni partida completa en Fuse.**

### Créditos

Diseño, dirección creativa y decisiones finales: Tony C. Ware. Código y herramientas MIT. Material artístico bajo reserva de derechos según los documentos de licencia del proyecto.

*El mundo no se salvará por sí mismo.*
