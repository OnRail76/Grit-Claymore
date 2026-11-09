# GRIT CLAYMORE · Registro de cambios

## V1.0.1 — Controles en la pantalla de título (9 de noviembre de 2026)

- Instrucciones **Q/A/O/P MOVER  SPACE FUEGO  PULSA SPACE**, con fuente nativa de 5×7 píxeles, centradas en la última franja negra (Y=184–190) de la pantalla de 256×192.
- Primera ilustración y créditos protegidos: las 184 líneas anteriores y las primeras 23 filas de atributos son **idénticas byte a byte** a V1.0; comprobado por SHA-256.
- Pantalla `.SCR` regenerada desde el generador original y comprimida como datos RLE del Z80: no es una imagen falsificada ni una rutina de superposición durante el juego.
- Prueba nueva `tests/test_v101_title.py`: comprueba pantalla, descompresión Z80, arranque con SPACE y preservación de la V1.0.
- No se han alterado los controles, jugabilidad, HUD, fases, carátula ni los PDF de V1.0. La etiqueta y Release V1.0 continúan como versión histórica.
- Archivo TAP v1.0.1 SHA-256: `a233e7a176bbad3aa49e26579b8c965da45f9cc1152a6144a9230b1df3d27de3`.

---

## V1.0 — Edición corregida

Se conserva el juego aprobado. Esta edición aplica exclusivamente una corrección geométrica al campo VIDAS y arreglos de maquetación a la documentación y la carátula.

## Juego Z80

- Los tres smileys se dibujan ahora en posiciones **centradas con precisión de 4 píxeles**, mediante dos mitades gráficas por icono.
- El conjunto queda con simetría exacta alrededor del centro del HUD: **x = 31,5 píxeles** de una columna de 64 píxeles.
- No se modifica ninguna otra mecánica, gráfica del escenario, sonido, texto del juego, colisión o temporizador.
- Las pruebas del intérprete Z80 parcial incluyen una prueba nueva de centrado por píxel y pruebas de regresión funcional. **No es una prueba de rendimiento o compatibilidad en Fuse real**.

## Atlas visual (14 páginas)

- HUD de la página de interfaz remaquetado con rótulo y captura separados.
- Corregidos todos los cruces de rótulos con imágenes detectados en las demás páginas, incluida la evolución histórica y el registro de 12 sectores.
- La documentación ahora usa capturas de RAM Z80 del binario recién compilado, para que los smileys sean los mismos que en el TAP.
- No se sustituyeron las capturas por mockups.

## Folleto de instrucciones (9 páginas)

- Reajustada «¿Cómo se ve en pantalla?».
- Corregidos los rótulos, imágenes y textos de «Tres fases».
- Corregida «Pantallas y reglas».
- Revisión automatizada de superposición entre texto e imágenes y de texto fuera de página: sin incidencias detectadas.

## Carátula

- Eliminada únicamente la línea duplicada «Tony C. Ware 2026» situada entre el título y el logotipo oficial; se conservó el resto de la portada original.

## Procedencia de los gráficos

El arte promocional es la portada. Capturas, sprites, tiles y pantallas del interior proceden de los datos del código Z80 compilado. Las escenas jugables se reconstruyeron con el **intérprete Z80 parcial**, no con Fuse ni hardware real.
