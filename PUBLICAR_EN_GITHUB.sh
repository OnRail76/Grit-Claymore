#!/usr/bin/env bash
# Publica el proyecto completo sobre el repositorio previamente creado.
# Necesita git y acceso de escritura a GitHub configurado en este equipo.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE="${REPO_URL:-https://github.com/OnRail76/Grit-Claymore.git}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
printf 'Clonando: %s\n' "$REMOTE"
git clone --branch main "$REMOTE" "$TMP/repo"
# Copiar contenido manteniendo .git; evita ficheros antiguos de compilación.
cp -a "$ROOT/." "$TMP/repo/"
cd "$TMP/repo"
git add -A
if git diff --cached --quiet; then
    echo 'El repositorio ya contiene estos archivos; nada que publicar.'
    exit 0
fi
printf '\nFicheros a publicar:\n'
git diff --cached --stat
printf '\n'
git commit -m "release: GRIT CLAYMORE V1.0 corregida, juego y documentación"
git push origin HEAD:main
printf '\nPublicado en https://github.com/OnRail76/Grit-Claymore\n'
