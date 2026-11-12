# GRIT CLAYMORE — Control de versiones y publicación segura

## Estado del proyecto

- **V1.6 publicada:** [Release oficial v1.6](https://github.com/OnRail76/Grit-Claymore/releases/tag/v1.6), con TAP, fuentes completos en ZIP, carátula, atlas, manual y capturas.
- **V1.0 y V1.0.1:** Releases históricas, conservadas sin modificaciones.
- **Próximas versiones:** se revisarán y publicarán por separado; una nueva versión no modifica retroactivamente una Release histórica.

**No ejecutes otra vez un comando de creación de `v1.6`: la etiqueta y la Release ya existen.**

## Protocolo para futuras versiones

1. **Auditar** el paquete recibido: fuentes, TAP, recursos, documentación y dependencias. Apartar scripts de publicación que copien un ZIP entero sobre el repositorio.
2. **Verificar** los TAP por SHA-256, las pruebas y la reconstrucción reproducible antes de subir cambios.
3. **Actualizar selectivamente** en GitHub solo los archivos pertinentes. Nada de vaciar carpetas, reescribir el historial, borrar etiquetas, forzar `push` ni sustituir `main` con un ZIP.
4. **Conservar** en la raíz `LICENSE` y `LICENSE_ES.md`, y mantener por separado los derechos del arte según `LICENCIA_GRAFICOS.md`.
5. **Preparar una Release nueva** con etiqueta específica para esa versión, su TAP oficial, ZIP completo con fuentes, notas, carátula y documentación. Publicarla manualmente tras revisar el resultado.
6. **Comprobar** los enlaces del README, la lista de archivos adjuntos, la automatización de solo lectura y la continuidad de Releases anteriores.

## Comprobaciones de lectura

Desde una terminal con `gh` autenticado:

```bash
gh release view v1.6 --repo OnRail76/Grit-Claymore
gh release list --repo OnRail76/Grit-Claymore
```

Estos comandos **solo consultan GitHub** y no cambian archivos ni Releases.

La V1.6 es verificable con el SHA-256 del TAP documentado en
[RELEASE_NOTES_V1.6.md](RELEASE_NOTES_V1.6.md). El [historial técnico](documentacion/CHANGELOG.md)
describe los cambios desde V1.0.1. El manual y atlas PDF incluidos son documentos
históricos de V1.0.x, sin actualizar todavía a los cambios jugables de V1.6.

Los viejos scripts de sincronización/publicación se eliminaron de `main`.
El historial Git permite consultarlos sin riesgo de ejecutarlos accidentalmente.
