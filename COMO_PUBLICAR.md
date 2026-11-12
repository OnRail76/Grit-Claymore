# GRIT CLAYMORE — Publicación manual y segura

**Estado:** el código y el TAP **V1.6 ya están en la rama `main`**.
La Release `v1.6` se publicará **manualmente por Tony C. Ware** cuando lo decida.
No hace falta reemplazar el repositorio, clonar para copiar archivos ni utilizar scripts
de sincronización destructivos.

## Regla para futuras publicaciones

- Nunca usar `rm -rf`, `git push --force`, `git reset --hard` ni sustituir el árbol de `main` por una carpeta ZIP.
- Los cambios de código se revisan y se suben de forma selectiva, conservando el historial.
- Las Releases y sus etiquetas se crean **separadamente** de los commits de código.
- `LICENSE` y `LICENSE_ES.md` permanecen en la raíz; los gráficos tienen derechos reservados según `LICENCIA_GRAFICOS.md`.
- Una versión histórica publicada no se reemplaza ni se borra.

## V1.6 — Preparación y comprobación

En Bazzite (Konsole), desde una copia **nueva** del repositorio:

```bash
git clone https://github.com/OnRail76/Grit-Claymore.git
cd Grit-Claymore
git pull --ff-only origin main
sha256sum -c <<'SHA'
8ea29ae17ada3ca62983b48bbac6385f07a5df47c773a7376b5a74d4ee082a8d  juego/GRIT_CLAYMORE_V1.6_48K.tap
SHA
gh auth status
```

Estas operaciones **no escriben en GitHub**; verifican que se está usando el TAP correcto.
No hay que compilar ni generar un nuevo TAP para adjuntarlo, pues el oficial ya está en `juego/`.

## Crear la Release v1.6 (solo cuando el autor lo decida)

Desde esa misma carpeta:

```bash
gh release create v1.6 \
  juego/GRIT_CLAYMORE_V1.6_48K.tap \
  caratula/GRIT_CLAYMORE_CARATULA_OFICIAL.png \
  documentacion/ATLAS_VISUAL_Y_MEMORIA.pdf \
  documentacion/MANUAL_DE_INSTRUCCIONES.pdf \
  recursos/V1.5/PLASMA_FASE_3.png \
  recursos/V1.2/TARJETA_FASE_3.png \
  --repo OnRail76/Grit-Claymore \
  --target main \
  --title "GRIT CLAYMORE V1.6" \
  --notes-file RELEASE_NOTES_V1.6.md \
  --latest
```

El comando únicamente **crea la etiqueta y la Release con sus archivos adjuntos**.
No modifica `main`, no altera las Releases `v1.0` y `v1.0.1` y no reescribe el historial.
Si la Release ya existe, `gh` avisará y no habrá que repetir el comando.

Verificar después: [Releases del proyecto](https://github.com/OnRail76/Grit-Claymore/releases).

## Documentación

Las notas específicas se encuentran en [RELEASE_NOTES_V1.6.md](RELEASE_NOTES_V1.6.md).
El manual y el atlas PDF aún describen la V1.0.x; las mejoras posteriores se documentan en
[documentacion/CHANGELOG.md](documentacion/CHANGELOG.md).

Los antiguos scripts de publicación se retiraron de la rama principal para evitar
sobrescrituras accidentales. Pueden consultarse en el historial Git sin afectar a la
publicación actual.
