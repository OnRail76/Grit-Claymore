# Publicar GRIT CLAYMORE V1.6

Desde la carpeta extraída del paquete V1.6, con `git` y `gh` autenticados (`gh auth login` y `gh auth setup-git`):

```bash
./PUBLICAR_V1.6.sh
```

El script comprueba el SHA-256 del TAP, sustituye el contenido de `main` por el del paquete (sin tocar el historial), hace el commit y el push, y crea la Release `v1.6` con el TAP, dos capturas, la carátula, el atlas y el manual. Si la Release `v1.6` ya existe, no toca nada. Las Releases `v1.0` y `v1.0.1` no se modifican.

---

# Publicación histórica de GRIT CLAYMORE V1.0.1

**Estado: publicada y cerrada.** [Descargar la Release V1.0.1](https://github.com/OnRail76/Grit-Claymore/releases/tag/v1.0.1).

**No es necesario volver a ejecutar el script de publicación.** El script `PUBLICAR_EN_GITHUB.sh` es específico de V1.0.1 y, desde esta revisión, no modifica el repositorio si esa Release ya existe. Para próximas versiones será necesario crear un nuevo procedimiento específico, sin reutilizar paquetes antiguos.

## Procedimiento utilizado originalmente

La Release original **v1.0 permanece intacta**. Esta actualización contiene el TAP con los controles visibles en la pantalla del título, su captura auténtica y el cambio del generador de gráficos.

## Publicar desde Bazzite (KDE)

1. Descargar y extraer el ZIP completo V1.0.1.
2. Entrar en `Grit-Claymore_GitHub_LISTO` en Dolphin y pulsar **F4**.
3. Comprobar que GitHub CLI está conectado como `OnRail76` (`gh auth status`).
4. Ejecutar:

```bash
bash PUBLICAR_EN_GITHUB.sh
```

El script clona `OnRail76/Grit-Claymore`, retira el TAP V1.0 solo de la rama principal, copia la V1.0.1 y sus fuentes, realiza commit y push, y crea la Release **v1.0.1** con TAP y materiales oficiales.

**Sin trucos:** no utiliza `--force`, no borra tags ni Releases anteriores y no abre el paginador `less` (usa `GIT_PAGER=cat`). Para ejecutarlo requiere `git` y `gh` autenticado. Si aparece un error, se detendrá sin afirmar que ha terminado.

**Comprobación:** [Release v1.0.1](https://github.com/OnRail76/Grit-Claymore/releases/tag/v1.0.1) (el enlace aparecerá cuando se publique).
