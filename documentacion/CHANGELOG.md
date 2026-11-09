# GRIT CLAYMORE · V1.0 corregida

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
