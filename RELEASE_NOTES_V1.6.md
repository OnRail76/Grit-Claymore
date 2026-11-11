# GRIT CLAYMORE V1.6

**ZX Spectrum 48K · © 2026 Tony C. Ware · By Tony and Claude A.I.**

Primera publicación desde la V1.0.1. Reúne seis revisiones de motor, gráficos y jugabilidad.

## Gráficos (V1.2)

- **Los 256 gráficos redibujados a mano**, con color por celda y una paleta propia para cada fase: jungla en verde y ocre, laboratorio en magenta, gris y cian, y complejo en azul y cian.
- **Un jefe por fase:** lancha patrullera en el río, camión blindado en el muelle de carga y el Hind Mi-24 del Comisario.
- **Panel lateral nuevo:** bisel remachado, rótulos sobre franja de color y la cabeza de Grit como icono de vida.
- **Tarjetas de fase** enmarcadas, con el retrato del jefe y el récord.
- Título, Game Over y Victoria conservan las ilustraciones aprobadas.

## Jugabilidad

- **Más enemigos (V1.3):** hasta cuatro a la vez y refuerzos más frecuentes. Los soldados se dan la vuelta y disparan si Grit los adelanta. Tres tipos de soldado distinguibles por el casco. En la fase 3 hay oleadas de mechas (8–9 por sector) con un soldado de apoyo.
- **Jefes más duros:** 16, 24 y 32 impactos. Ya no tienen zona segura.
- **Cañón de plasma (V1.5):** dos cajas de armas en la fase 3. Todo disparo es de plasma hasta agotar las 12 cargas: atraviesa muros y soldados, y un mecha cae con dos disparos. Se pierde al morir.
- **Raciones (V1.4):** una en cada sector y otra de refuerzo en la fase 3.
- **Tanque (V1.4):** aguanta cuatro impactos y suena al moverse.
- **Marcador real de seis cifras**, puntos por mecha y jefe, vida extra cada 10.000 y récord de la sesión.
- Dos balas en pantalla, más rápidas que el scroll.

## Control

- Teclado Q/A/O/P + SPACE, joystick Sinclair (6-7-8-9-0) y **Kempston automático**: si empiezas con el fuego del joystick juegas con él; con SPACE, con teclado.
- **Pausa** con H.

## Motor

- Scroll en anillo (el doble de pasos por segundo) y pantalla sombra fuera de la memoria contendida.
- Sonido que no congela el juego. Melodía en el título.
- **V1.6:** Grit ya no se queda atrapado en el escenario: el scroll respeta el terreno. Los 12 mapas están revisados.

## Verificación

13 baterías de pruebas automáticas sobre el Z80 ensamblado, con un intérprete parcial: no modela tiempos reales, contención de memoria, carga de cinta ni sonido. No hay certificación de esta versión en Fuse ni en hardware real. El manual y el atlas en PDF todavía describen la V1.0.x; el detalle de cada revisión está en `documentacion/CHANGELOG.md`.

**Archivo:** `GRIT_CLAYMORE_V1.6_48K.tap` (cargar en un emulador en modo Spectrum 48K).

**SHA-256 TAP:** `8ea29ae17ada3ca62983b48bbac6385f07a5df47c773a7376b5a74d4ee082a8d`

*El mundo no se salvará por sí mismo.*
