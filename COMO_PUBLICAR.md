# GRIT CLAYMORE v1.9 — Publicación segura

La rama `main` de `OnRail76/Grit-Claymore` está protegida. Los cambios deben presentarse por una Pull Request, sin reescribir el historial ni sustituir la release v1.6.

1. Ejecutar `PUBLICAR_GRIT_V1_9.sh --comprobar` desde el paquete de publicación externo.
2. Ejecutar `PUBLICAR_GRIT_V1_9.sh --preparar`. Crea una rama nueva y una Pull Request; **no publica todavía**.
3. Revisar y fusionar esa Pull Request en GitHub, tras verificar el resultado de los tests.
4. Ejecutar `PUBLICAR_GRIT_V1_9.sh --publicar` para generar la release v1.9 en el commit exacto de `main` y adjuntar los siete recursos.

No usar `git push --force`, `git clean` sobre el repositorio original, ni herramientas que reemplacen `main` por un ZIP. No borrar etiquetas, versiones o publicaciones antiguas.

**Carátula oficial:** expresionista. La antigua pasa a tercera alternativa. Ambos PNG conservan sus píxeles originales.

**TAP oficial, SHA-256:** `1ddb25648cd64e9fb0b36c7af87c6def9e7620365aa1256920c27c2f6e823127`.
