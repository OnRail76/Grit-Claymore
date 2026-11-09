# GRIT CLAYMORE

**Un pequeño arcade de disparos para 48K de Spectrum.**

**ZX Spectrum 48K · Código máquina Z80 · Tony C. Ware · 2026 · V1.0**

![Carátula oficial](caratula/GRIT_CLAYMORE_CARATULA_OFICIAL.png)

## El juego

En el presente, Grit Claymore, operativo del **EFEC (European Federation Enforcer Corps)** —organización ficticia vinculada al EU INTCEN dentro de la historia—, se infiltra en una región remota de Vietnam para destruir una red de narcotráfico, desmantelar el armamento experimental del ejército renegado y detener a **El Comisario**.

Tres fases de arcade vertical, scroll por bloques, sprites enmascarados, gráficos propios y animaciones ambientales de dos fotogramas. Un homenaje a la claridad visual de **Who Dares Wins II** y los primeros **Ultima**.

**El mundo no se salvará por sí mismo.**

## Descargar y jugar

**[GRIT CLAYMORE V1.0 para ZX Spectrum 48K (.TAP)](juego/GRIT_CLAYMORE_V1.0_48K.tap)**

Carga el archivo en **Fuse** seleccionando la máquina **Spectrum 48K**. El juego utiliza el sonido beeper y teclado.

| Tecla | Acción |
|---|---|
| Q | Arriba |
| A | Abajo |
| O | Izquierda |
| P | Derecha |
| ESPACIO | Disparo / empezar |

Grit se mueve y dispara en ocho direcciones; el tanque se mueve y dispara en cuatro. Las raciones recuperan energía. Los proyectiles del tanque atraviesan obstáculos y el vehículo arrolla a soldados. La fase 3 se juega a pie, contra mechas y el Hind del Comisario.

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
python3 -m pip install -r requirements.txt
python3 build_all.py
```

Se genera `build/GRIT_CLAYMORE_V078_48K.tap` y se ejecuta el conjunto de pruebas. El directorio `build/` se excluye de Git para evitar artefactos obsoletos.

La V1.0 corregida conserva la jugabilidad aprobada y centra mejor los tres iconos de vidas. **La compilación está verificada mediante pruebas automatizadas; no hay certificación de esta última revisión en Fuse real.**

## Licencias y derechos

El **código fuente y las herramientas** se publican con licencia **MIT**, © 2026 Tony C. Ware. Los **gráficos, sprites, carátula, ilustraciones, logotipo y materiales gráficos** tienen los derechos reservados. El archivo compilado se ofrece para descarga y uso personal. Lee [LICENSE](LICENSE), [LICENCIA_GRAFICOS.md](LICENCIA_GRAFICOS.md) y [DERECHOS.md](DERECHOS.md).

**© 2026 Tony C. Ware.**
