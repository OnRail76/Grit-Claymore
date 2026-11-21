# Publicación oficial GRIT CLAYMORE v1.14

Usar el script incluido en el paquete de publicación: `PUBLICAR_GRIT_V1_14.sh`.

La rama `main` está protegida. Subir primero cambios mediante Pull Request, esperar la verificación automática y fusionar por GitHub. Solo después crear la release v1.14. Una vez confirmados TODOS sus assets y la conservación artística, retirar la release anterior v1.9 y su tag; así queda una única release vigente.

El TAP no se recompila ni se modifica durante la publicación, y debe coincidir con SHA-256:
`3088339d7a9f822c072f0377abc9872db931b7daa4a6de8498b252c61b7727f3`.

No hacer push forzado ni borrar manuales, atlas o carátulas vigentes. La documentación de nuevas versiones se mantiene en `documentacion/CHANGELOG.md` y una sola `RELEASE_NOTES_V1.14.md`.
