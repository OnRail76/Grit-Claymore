## Nota editorial de la release V1.9 — 2026

La portada expresionista pasa a ser oficial. La anterior portada oficial (edición 1.0) se conserva íntegra en la galería de alternativas. La portada nueva se incorpora como primera página del manual actual; el atlas actual se mantiene en su representación visual original. La dirección artística no modifica el TAP ni el motor Z80.

---

# GRIT CLAYMORE · Registro de cambios

## V1.9 — Jefes y tanque (12 de noviembre de 2026)

- **Disparo apuntado** (`hind_fire_now`): con Grit bajo el jefe, recto desde la columna que tiene encima; si no, en diagonal hacia él desde el borde más cercano. Fase 2: además uno recto. Fase 3 sigue en abanico. Cadencia: lancha y camión cada 16 ticks (la lancha antes cada 32), Hind cada 8.
- **Rabia** a mitad de vida (`boss_half` = 8/12/16): parpadeo rojo 16 ticks, movimiento el doble de rápido, cadencia doble en fases 1 y 2 y siempre abanico de tres.
- **Aviso**: el jefe destella en blanco los 4 ticks previos a cada disparo (`boss_tint`, color forzado `force_attr` en `paint_tile`).
- **Tanque**: una casilla cada 4 ticks (antes cada 3; a pie cada 2), casco verde brillante con la celda del cañón en blanco, parpadeo rojo 12 ticks al recibir.
- Memoria: los colores de los 256 gráficos viajan al final de la cinta y se bajan a 0x5D00; variables nuevas en 0x7FF4..0x7FF9.
- Medido con un bot quieto en el centro disparando: la lancha le quita 3 golpes (antes 2), el camión 4 (antes 3), el Hind 3 (igual); la duración del combate apenas cambia (9-15 s).
- `tests/test_v19.py`: puntería, rabia en los tres jefes, aviso, tanque (velocidad, colores, parpadeo) y memoria.
- **No validado en Fuse ni en hardware real.**
- TAP V1.9 SHA-256: `1ddb25648cd64e9fb0b36c7af87c6def9e7620365aa1256920c27c2f6e823127`.

---

## V1.8 — Soldados: correr ya no sale gratis (12 de noviembre de 2026)

- **Generador aleatorio nuevo** (xorshift de 16 bits, `rand`): el de antes (sumar 37 y rotar) repetía la misma columna varias veces seguidas.
- **Tres entradas**: arriba (3 de cada 4), por un lado a media pantalla (filas 5-12, buscando suelo libre desde el borde) y, si Grit lleva un rato avanzando sin parar (`run_meter`), **emboscada por detrás**: de 3 a 6 filas por debajo de él, a partir de 4 columnas a su lado. Nunca encima de Grit.
- **Corriendo** (`run_meter` ≥ 40): aviso antes de disparar de 2 ticks (antes 8 o 5) y refuerzos cada 8 ticks.
- **Balas hacia arriba** a una fila por tick (el doble que Grit) y, si Grit no está en su columna, corrigen una columna hacia él cada dos filas.
- **El rojo (fijo) es tirador**: solo se queda donde tiene 4 filas de vista libres (si no, sale al asalto), ve a 12 columnas (antes 8) y recarga 10 ticks antes.
- Memoria: la tabla de colisiones viaja al final de la cinta y se baja a 0x5B00 (búfer de impresora); las variables nuevas, en 0x7FF0.
- `tests/test_v18.py`: memoria, variedad de apariciones (sin rachas, por los lados, emboscadas, suelo libre, nunca encima de Grit), vista del tirador, balas hacia arriba, y correr hasta el jefe de la fase 1 cuesta 4-6 golpes (V1.7: 1-5).
- **No validado en Fuse ni en hardware real.**
- TAP V1.8 SHA-256: `7983bc1231d6a881a8bbb8069769a1e9b2887f52fc74046dffd85da0c21d0da1`.

---

## V1.7 — Melodía del título una sola vez (12 de noviembre de 2026)

- **La melodía del título suena una vez** cada vez que se llega a la pantalla de título (al cargar y al volver tras Game Over o Victoria). Al acabar queda en silencio hasta pulsar fuego, en lugar de repetirse sin fin con el beeper. Pulsar fuego durante la melodía la corta como antes.
- `tests/test_v17.py`: la melodía suena entera, después no hay ni un cambio más en el altavoz, se puede empezar a jugar y al volver al título suena otra vez, igual.
- **No validado en Fuse ni en hardware real.**
- TAP V1.7 SHA-256: `be23c5192ce6f50b88f4df71ea9ee64833c2e86755f60242a18cf442a9dbffc0`.

---

## V1.6 — Grit ya no se queda atrapado (candidata, 11 de noviembre de 2026)

- **Fallo corregido:** al avanzar con scroll, el terreno bajaba una fila sin comprobar qué caía sobre Grit. En los bordes del camino un arbusto, un muro o una tubería podían quedar encima de él y encerrarlo, como en la captura de Speccy de la V1.4. Ahora el avance con scroll respeta el terreno igual que un paso normal: si la fila que bajaría sobre Grit es sólida, no se avanza y hay que rodear el obstáculo. En el rastreo de 9 sectores había 188 ticks con Grit dentro de un sólido; ahora hay 0.
- **Mapas revisados:** análisis completo de los 12 mapas con las reglas reales (Grit de 2×2, ocho direcciones, la pantalla solo deja bajar 10 filas tras avanzar). La posición de salida está libre en todos y no hay ningún hueco alcanzable sin camino hacia arriba.
- **Arma especial:** confirmado y fijado en pruebas. Al recoger la caja, todo disparo es de plasma hasta agotar las 12 cargas, a toques o con el fuego pulsado. Después vuelve el fusil, y el arma se pierde al morir.
- `tests/test_v16.py`: el scroll nunca entierra a Grit (rastreo y caso dirigido), análisis de trampas en los 12 mapas y plasma hasta agotarse.
- **No validado en Fuse ni en hardware real.**
- TAP V1.6 SHA-256: `8ea29ae17ada3ca62983b48bbac6385f07a5df47c773a7376b5a74d4ee082a8d`.

---

## V1.5 — Cañón de plasma (candidata, 11 de noviembre de 2026)

Arma especial para la fase 3.

- **Dos cajas de armas** en la fase 3, en los sectores 1 y 3, sobre un hueco de 2×2 transitable de la fila 15. La caja (16×16, rayo en un marco) usa el bit FLASH del Spectrum: parpadea en magenta sin gastar CPU.
- **Al recogerla, 12 disparos de plasma.** Atraviesan muros y soldados como el proyectil del tanque, quitan 3 impactos a un mecha (cae con dos disparos en vez de seis) y 2 al Hind. Se ven como una bola magenta y tienen sonido propio. Al agotarse vuelve el fusil.
- **El plasma se pierde con la vida.**
- **Marcador:** en la fase 3, donde no hay tanque, el módulo TANQUE pasa a llamarse ARMA, con la misma tipografía del panel, y sus cuatro celdas cuentan la munición en magenta (3 disparos por celda). En las fases 1 y 2 sigue siendo TANQUE.
- `tests/test_v15.py`: cajas solo en los sectores 1 y 3 de la fase 3, sobre suelo y con FLASH; recogida, munición, marcador, mecha en dos disparos, Hind −2, pérdida al morir y recogida jugando.
- **Memoria:** quedan unos 150 bytes libres bajo la pantalla sombra. Para añadir algo más grande habrá que bajar el banco de jefes a la memoria baja.
- **No validado en Fuse ni en hardware real.**
- TAP V1.5 SHA-256: `f2ceed17daa4b39c2ca4fd38f23dead6eb679724d2e3f03d0861ec9829371be4`.

---

## V1.4 — Raciones y tanque reforzado (candidata, 11 de noviembre de 2026)

Ajuste a la dificultad de la V1.3.

- **Raciones:** una en cada sector, arena del jefe incluida, en una columna transitable al azar. En la fase 3, otra de refuerzo aparece en lo alto cuando la cámara pasa la fila 12, si no queda otra en pantalla. Son 15 por partida (antes 3). Cada una sigue curando 2 puntos de PODER.
- **Tanque de cuatro impactos** (antes dos). El marcador TANQUE pasa a las mismas cuatro celdas de PODER: amarillo con blindaje y rojo vacío. La ventana del panel se ensancha a juego.
- `tests/test_v14.py`: ración en los 12 sectores sobre suelo transitable, refuerzo de la fase 3 y tanque de cuatro impactos con su marcador.
- **No validado en Fuse ni en hardware real.**
- TAP V1.4 SHA-256: `162292bf073b63648d8e146012f2fabc6211f1c620cbf2eaa1f8f184fd4c26fd`.

---

## V1.3 — Más enemigos y más difícil (candidata, 11 de noviembre de 2026)

Mismos gráficos que la V1.2. Cambian el combate, la dificultad, el sonido del tanque y la elección de control.

### Enemigos

- **Cuatro enemigos a la vez** en lugar de tres. Los soldados prueban hasta cuatro columnas antes de renunciar a aparecer: el sector 2 de la jungla pasa de menos de un enemigo de media a casi tres.
- **Los soldados que no salían:** si Grit los adelanta, se dan la vuelta (vista de espaldas, que antes no aparecía nunca) y disparan hacia arriba.
- **Tres tipos de soldado distinguibles:** fijo con casco rojo, patrulla con casco magenta y asalto con casco cian. Los tres reparten de verdad (antes la patrulla casi no salía).
- **Fase 3:** al limpiar un grupo de mechas y avanzar ocho filas aparece otra oleada de tres en lo alto, en V para que sus recorridos no se crucen, dos veces por sector. Son 8–9 mechas por sector en lugar de 2–3, y siempre hay un soldado de apoyo en el cuarto hueco. Cada enemigo lleva ahora su tipo (soldado o mecha) y el motor ya no decide por la fase.

### Dificultad

- Refuerzos: cada 16 ticks en las fases 1 y 3 y cada 8 en la fase 2 (antes 32 y 16).
- Reacción antes de disparar: 8 ticks en la fase 1 y 5 después (antes 10). Recarga: 28 y 20 ticks (antes 36 y 26).
- Balas enemigas en pantalla: hasta 2 en la fase 1 y 3 después. Las de los soldados de la fase 3 ya pueden ir en diagonal.
- Jefes: 16, 24 y 32 impactos (antes 12, 18 y 24).

### Tanque

- **Ruido de motor:** un traqueteo grave en dos tonos cada vez que avanza, solo cuando no suena otro efecto.

### Control

- **Kempston automático:** en el título se comprueba si hay interfaz. Si la partida empieza con el FUEGO del Kempston, se juega con joystick. Si empieza con SPACE (o el 0 de Sinclair), se juega con teclado y el puerto del Kempston ya no se lee, así que no hay movimientos fantasma.

### Rendimiento

- Para que cuatro enemigos quepan en 25 ticks por segundo, cada baja repinta solo las cifras de PUNTOS, cada impacto solo las barras y la animación del escenario se reparte en ocho bandas de tres filas, una por tick.
- Combate estimado: 25 ticks/s en las fases 1 y 2 y 23,8 en la fase 3 con tres mechas y el soldado (la V1.1 daba 24,4 con solo los mechas).

### Pruebas

- `tests/test_v13.py`: cuatro soldados y las cuatro vistas en juego, disparo hacia atrás, colores por tipo, nueve mechas por sector con soldado de apoyo, vida de los jefes y motor del tanque.
- La prueba de Kempston cubre los dos caminos (fuego del joystick o SPACE). Las comparaciones de pantalla esperan al final del ciclo de ocho bandas.

### Sin hacer

- **No validado en Fuse ni en hardware real.**
- TAP V1.3 SHA-256: `73275382dde30a7ea45448e61baa692cb73aab250343d05652c7251b52be8970`.

---

## V1.2 — Remozado gráfico integral (candidata, 11 de noviembre de 2026)

Mismo motor y mismas reglas que la V1.1. Cambia todo lo que se ve dentro de la partida.

### Gráficos

- **Los 256 gráficos del banco, redibujados a mano** en `tools/gfx_v12.py`: rejillas de texto donde cada píxel está escrito, con un atributo por celda. Se conservan los índices, la colisión y el tamaño de cada pieza, así que el motor no cambia.
- **Paleta por fase.** Los fondos van en tinta apagada para que Grit, enemigos y balas destaquen. Jungla en verde y ocre; laboratorio con baldosa magenta, muros grises y pasarelas cian; complejo con placas azules, rejillas cian y tuberías.
- **Personajes:** Grit (boina, 8 direcciones × 2 pasos), soldados con casco rojo y pantalón caqui, tanque con orugas animadas y torreta centrada en el casco, mecha de 24×24 con cabina roja.
- **Escenario:** dosel de selva, matorrales, río en dos fotogramas, puente de tablones, cabañas de techo amarillo, torre de vigía, cubas químicas, barreras de seguridad, consolas, reactor y hangar de mechas.
- **Disparos y explosiones** nuevos: trazadoras orientadas, bala enemiga en rombo y explosión en dos fotogramas (bola de fuego y metralla).

### Jefes

- **Un jefe distinto por fase:** lancha patrullera en el río (fase 1), camión blindado en el muelle de carga (fase 2) y el Hind del Comisario sobre la plataforma (fase 3). Cada uno tiene 32×24 píxeles, dos fotogramas y colores por celda.
- **Hind redibujado como un Mi-24 visto desde arriba:** fuselaje con morro hacia Grit, cabinas en tándem de piloto y artillero, alas cortas con contenedores de cohetes en rojo, botalón de cola con estabilizador y rotor lateral, y palas largas que alternan entre X y cruz.
- Banco aparte de 1.224 bytes (`boss_bank`): al entrar en el sector 4, `load_boss_gfx` copia el jefe de la fase sobre los índices 154–177. Su comportamiento, su vida y sus disparos siguen siendo los de la V1.1.
- **Arenas nuevas:** río ancho con orillas en la jungla, muelle con línea de seguridad en el laboratorio y plataforma con consolas en el complejo. La fila 9 sigue siendo el límite.

### Panel lateral (HUD)

- **Panel de instrumentos:** bisel gris continuo de doble línea, placas remachadas entre módulos y cada contador dentro de una ventana enmarcada.
- **Rótulos** en negro sobre franja de color: PUNTOS en amarillo, VIDAS en cian, PODER en verde y TANQUE en magenta.
- **Vidas:** la cabeza de Grit con boina, en verde. La vida perdida queda como hueco en contorno.
- Celdas de energía con brillo. Las calaveras del autor se mantienen.

### Balas frente al scroll

- En la V1.1, al avanzar, la bala de Grit subía una celda y el scroll la bajaba otra: se quedaba quieta en pantalla. Ahora la bala avanza **dos celdas por tick**, con colisión en cada celda, y **no se desplaza con el scroll**. Al avanzar sube por la pantalla unas 3,7 veces más rápido que baja el terreno.

### Tarjeta de fase

- Marco doble en el color de la fase, nombre de la fase, **retrato animado del jefe** y su nombre, y récord de la sesión. Dura los mismos 2 segundos.

### Motor (solo lo necesario para lo anterior)

- Un diccionario de filas de mapa por fase (`map_rows_p1..p3`, puntero `rows_base`): los mapas redecorados necesitan 150 + 39 + 71 filas únicas y ya no caben en un solo diccionario de 256.
- Memoria: el código acaba en 0xD316 y los buffers en 0xDC00, por debajo de la sombra (0xE000). La cinta crece 1.290 bytes.

### Pruebas

- Las 12 baterías heredadas y las de la V1.1 pasan, incluido el presupuesto de T-states y los 3.120 ticks aleatorios.
- `tests/test_v12.py`: balas más rápidas que el scroll al avanzar, Hind reconocible (cola, cohetes, morro, rotor en dos posiciones) y marco del HUD.
- Las pruebas del HUD se adaptan al panel nuevo (franjas de color, cabezas de Grit). La del joystick Sinclair dispara hacia arriba, porque una bala hacia abajo desde el borde sale de pantalla en el mismo tick.
- `test_v076.py` comprueba la tarjeta nueva (color de fase, retrato con los atributos del jefe y banco cargado). `test_v07.py` y `test_art_v07.py` se adaptan a la paleta nueva y al diccionario por fase.

### Sin cambios

- **Título, Game Over y Victoria** conservan las ilustraciones aprobadas por el autor.
- **No validado en Fuse ni en hardware real.**
- TAP V1.2 SHA-256: `eaccecad76124b21c58538180b2bc1d6b4d782d7184f6d27934eb3a0c2837c88`.
- Manual y atlas en PDF: siguen describiendo la V1.0.x. Las capturas nuevas están en `recursos/V1.2/`; las de `recursos/juego/` son históricas (V1.0).

---

## V1.1 — Motor, reglas y controles (candidata, 11 de noviembre de 2026)

Gráficos, mapas, HUD y pantallas completas son los de la V1.0.1. Cambia el código Z80.

### Fallos corregidos

- **Zona segura de los jefes:** en el sector 4 Grit no puede subir de la fila 9. Antes bastaba colocarse en las filas 3–5 y mantener SPACE.
- **Marcador:** seis cifras decimales reales. Ya no vuelve a 000000 a las 100 bajas ni pinta un carácter inválido al llegar a 100 con el tanque.
- **Soldados:** comprueban el mapa antes de moverse y al aparecer; ya no caminan sobre agua o cabañas.
- **Balas:** los muros paran también las balas de soldados y mechas. El agua (tile 4) no para ninguna bala, tampoco las de Grit.
- **Ración:** se recoge al tocarla con cualquier celda de Grit.

### Motor

- **Scroll en anillo:** la zona de juego de la pantalla sombra es un anillo de 24 filas; avanzar gira el anillo y pinta la fila nueva, sin mover bitmap. La copia a pantalla usa 24 `LDI` por línea y deja fuera el HUD. Cada paso dura 4 fotogramas fijos.
- **Sincronía por `FRAMES`:** un tick caro ya no cuesta fotogramas de más por los dos `HALT` fijos.
- **Animación de tiles** en cuatro bandas de seis filas, con puntero lineal sobre el mapa.
- **Mechas** compuestos de una pasada (tile de fondo, máscara y sprite), sin fase de borrado.
- **Pintado:** direcciones por rotación en vez de sumas de 16 bits, bucles desenrollados y máscara sin `IX`.
- **Memoria:** sombra en `0xE000–0xFAFF` y pila en `0xFB00–0xFFFF`, fuera de la zona contendida. Las tres pantallas RLE viajan al final del bloque y se bajan a `0x5E00` al arrancar; `map_data` y la cola de celdas sucias ya no van en la cinta.
- **Sonido:** una ráfaga corta por tick en lugar de tonos bloqueantes.

### Jugabilidad

- Dos balas propias en pantalla.
- 300 puntos por mecha; 2.000 / 3.000 / 4.000 por jefe; vida extra cada 10.000 (hasta tres); récord de sesión en la tarjeta de fase.
- Joystick Kempston (detección al arrancar) y Sinclair 6-7-8-9-0; pausa con H.
- Ración en columna aleatoria transitable; el generador se siembra al pulsar fuego en el título.
- Secuencia de muerte, explosión del tanque y del jefe, fanfarria de jefe y melodía original en el título.

### Mediciones (estimación de T-states del intérprete parcial; sin contención ni interrupción de ROM)

| Situación | V1.0.1 | V1.1 |
|---|---|---|
| Jungla, combate | 15,3 ticks/s | 25,0 ticks/s |
| Laboratorio, combate | 15,0 ticks/s | 25,0 ticks/s |
| Complejo, tres mechas | 11,6 ticks/s | 24,4 ticks/s |
| Jefe final | 15,0 ticks/s | 24,7 ticks/s |
| Avance con scroll | 6,4 pasos/s | 12,5 pasos/s |
| Tick con disparo (máximo) | 204.000 T | 123.000 T |

### Pruebas

- `tests/test_v110.py`: 12 comprobaciones nuevas (jefes, marcador, terreno, dos balas, entradas, pausa, muerte, anillo, RAM con basura, presupuesto, 3.120 ticks aleatorios en las 12 pantallas y melodía).
- `tests/tstates.py`: estimador de T-states.
- Pruebas heredadas adaptadas a las nuevas direcciones, a las cuatro bandas de animación y al pintado de mechas.
- Ensamblador ampliado con `EQU`, `LDI` e `IN A,(n)`; intérprete con `LDI`, `IN A,(n)`, `AND/OR (IX+d)` y `HALT` que avanza `FRAMES`.

### Sin hacer

- **No validado en Fuse ni en hardware real.** Tiempos, sonido, carga de cinta y detección de Kempston solo están razonados y probados en el intérprete parcial.
- Movimiento a 4 píxeles: pendiente del remozado gráfico (exige sprites predesplazados).
- Cuarto soldado en pantalla: descartado; con las mediciones actuales rompería los 25 ticks/s.
- Posición del tanque: sigue fija, los mapas están dibujados alrededor.
- Manual y atlas en PDF: no regenerados.
- TAP V1.1 SHA-256: `d4dc796e1b433c6d262d0ab3f6f3d72a178a1c6c92ad7ab4325c146cd7373743`.

---

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
