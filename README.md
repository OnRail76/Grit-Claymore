# GRIT CLAYMORE

**Un pequeño arcade de disparos para 48K de Spectrum.**

**ZX Spectrum 48K · Código máquina Z80 · Tony C. Ware · 2026 · V1.0.1**

![Carátula oficial](caratula/GRIT_CLAYMORE_CARATULA_OFICIAL.png)

## El juego

En el presente, Grit Claymore, operativo del **EFEC (European Federation Enforcer Corps)** —organización ficticia vinculada al EU INTCEN dentro de la historia—, se infiltra en una región remota de Vietnam para destruir una red de narcotráfico, desmantelar el armamento experimental del ejército renegado y detener a **El Comisario**.

Tres fases de arcade vertical, scroll por bloques, sprites enmascarados, gráficos propios y animaciones ambientales de dos fotogramas. Un homenaje a la claridad visual de **Who Dares Wins II** y los primeros **Ultima**.

**El mundo no se salvará por sí mismo.**

## Descargar y jugar

**[Descargar la Release oficial V1.0.1 (juego, manual, atlas y carátula)](https://github.com/OnRail76/Grit-Claymore/releases/tag/v1.0.1)**

También puedes obtener [solo el TAP V1.0.1](juego/GRIT_CLAYMORE_V1.0.1_48K.tap). La [Release V1.0 original](https://github.com/OnRail76/Grit-Claymore/releases/tag/v1.0) se conserva sin cambios.

Carga el archivo en **Fuse** seleccionando la máquina **Spectrum 48K**. El juego utiliza el sonido beeper y teclado.

| Tecla | Acción |
|---|---|
| Q | Arriba |
| A | Abajo |
| O | Izquierda |
| P | Derecha |
| ESPACIO | Disparo / empezar |

Grit se mueve y dispara en ocho direcciones; el tanque se mueve y dispara en cuatro. Las raciones recuperan energía. Los proyectiles del tanque atraviesan obstáculos y el vehículo arrolla a soldados. La fase 3 se juega a pie, contra mechas y el Hind del Comisario.

### Pantalla de título actualizada (V1.0.1)

![Pantalla de título ZX Spectrum con controles visibles](recursos/juego/TITULO.png)

La pantalla de título muestra **Q/A/O/P MOVER · SPACE FUEGO · PULSA SPACE** en la última fila negra, sin modificar la ilustración, los créditos ni la rutina de inicio. El resto del juego permanece como en V1.0. La Release V1.0 se conserva en el historial.

## Documentación ilustrada

- [**Manual de instrucciones (PDF)**](documentacion/MANUAL_DE_INSTRUCCIONES.pdf)
- [**Atlas visual y memoria del desarrollo (PDF)**](documentacion/ATLAS_VISUAL_Y_MEMORIA.pdf)
- [**Carátula oficial (PNG)**](caratula/GRIT_CLAYMORE_CARATULA_OFICIAL.png)
- [**Capturas y recursos gráficos reales**](recursos/juego/)
- [**Historial de la edición corregida**](documentacion/CHANGELOG.md)

Las capturas jugables de la documentación se han generado a partir de la RAM de pantalla mediante un **intérprete Z80 parcial**, **no** son capturas de Fuse ni de hardware real. Los sprites y tiles se han extraído del código del juego, sin utilizar mockups.

## Código fuente y compilación

El proyecto incluye el ensamblador Z80, mapas, generadores de gráficos y herramientas de pruebas.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python build_all.py
```

El banco genera `build/GRIT_CLAYMORE_V1.0.1_48K.tap` (y un TAP de compatibilidad para las pruebas heredadas), y ejecuta el conjunto de regresiones. La [verificación automática de GitHub Actions](.github/workflows/verificar-grit.yml) comprueba que el TAP reconstruido sea **idéntico byte por byte** al publicado y no modifica las Releases. El directorio `build/` se excluye de Git para evitar artefactos obsoletos.

La V1.0.1 conserva la jugabilidad aprobada en V1.0, incluido el centrado exacto de los tres iconos de vidas. **La compilación está verificada mediante pruebas automatizadas; no hay certificación de esta última revisión en Fuse real.**

El archivo [MANIFIESTO_SHA256.json](MANIFIESTO_SHA256.json) documenta las huellas del **paquete de publicación V1.0.1**, no pretende ser un inventario actualizado de cambios posteriores en textos de mantenimiento.

## Licencias y derechos

El **código fuente y las herramientas** se publican con licencia **MIT**, © 2026 Tony C. Ware. Los **gráficos, sprites, carátula, ilustraciones, logotipo y materiales gráficos** tienen los derechos reservados. El archivo compilado se ofrece para descarga y uso personal. La **Licencia MIT (edición asistida por IA)** está disponible en [inglés (LICENSE)](LICENSE) y [castellano (LICENSE_ES.md)](LICENSE_ES.md). Para los recursos gráficos y las condiciones de distribución, consulta [LICENCIA_GRAFICOS.md](LICENCIA_GRAFICOS.md) y [DERECHOS.md](DERECHOS.md).

**© 2026 Tony C. Ware.**

## Carátulas alternativas

Además de la portada oficial, hay una [galería de tres carátulas alternativas con el logo Tony C. Ware](caratula/alternativas/README.md). Son ilustraciones promocionales; no son capturas del juego y mantienen sus derechos reservados.
