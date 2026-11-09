#!/usr/bin/env bash
# GRIT CLAYMORE V1.0.1 - publica código y assets, y crea la Release oficial.
# Bazzite/Linux: requiere git + gh autenticado (gh auth login; gh auth setup-git).
set -euo pipefail
export GIT_PAGER=cat
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE="https://github.com/OnRail76/Grit-Claymore.git"
REPO="OnRail76/Grit-Claymore"
for command in git gh; do
  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'Falta %s en el sistema.\n' "$command" >&2
    exit 1
  fi
done
[ -f "$ROOT/juego/GRIT_CLAYMORE_V1.0.1_48K.tap" ] || {
  echo 'No encuentro el TAP V1.0.1. Extrae el ZIP completo antes de ejecutar el script.' >&2
  exit 1
}
gh auth status >/dev/null
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
printf '\nClonando %s ...\n' "$REMOTE"
git clone --branch main "$REMOTE" "$TMP/repo"
# No modificamos .git ni eliminamos otros archivos de terceros.
cp -a "$ROOT/." "$TMP/repo/"
# Tras la copia, retirar la V1.0 antigua aunque el ZIP se haya extraído
# sobre una carpeta local V1.0 previa. Su tag y Release siguen intactos.
rm -f "$TMP/repo/juego/GRIT_CLAYMORE_V1.0_48K.tap"
cd "$TMP/repo"
git add -A
if git diff --cached --quiet; then
  echo 'La rama main ya contiene esta versión.'
else
  echo 'Cambios que se van a publicar:'
  git --no-pager diff --cached --stat
  git commit -m 'release: GRIT CLAYMORE V1.0.1 - controles en el titulo'
  git push origin HEAD:main
fi
if gh release view v1.0.1 --repo "$REPO" >/dev/null 2>&1; then
  echo 'La Release v1.0.1 ya existe; no se modifica para evitar duplicados.'
else
  echo 'Creando Release publica v1.0.1 ...'
  gh release create v1.0.1 \
    "$ROOT/juego/GRIT_CLAYMORE_V1.0.1_48K.tap" \
    "$ROOT/recursos/juego/TITULO.png" \
    "$ROOT/caratula/GRIT_CLAYMORE_CARATULA_OFICIAL.png" \
    "$ROOT/documentacion/ATLAS_VISUAL_Y_MEMORIA.pdf" \
    "$ROOT/documentacion/MANUAL_DE_INSTRUCCIONES.pdf" \
    --repo "$REPO" --target main \
    --title 'GRIT CLAYMORE V1.0.1' \
    --notes-file "$ROOT/RELEASE_NOTES_V1.0.1.md" \
    --latest
fi
printf '\nPUBLICADO: https://github.com/OnRail76/Grit-Claymore/releases/tag/v1.0.1\n'
