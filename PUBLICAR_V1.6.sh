#!/usr/bin/env bash
# GRIT CLAYMORE V1.6 - publica el código en main y crea la Release v1.6.
# Requiere git + gh autenticado (gh auth login; gh auth setup-git).
# Se ejecuta desde la carpeta extraída del paquete de publicación V1.6.
set -euo pipefail
export GIT_PAGER=cat
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOTE="https://github.com/OnRail76/Grit-Claymore.git"
REPO="OnRail76/Grit-Claymore"
TAG="v1.6"
TAP="$ROOT/juego/GRIT_CLAYMORE_V1.6_48K.tap"
SHA="8ea29ae17ada3ca62983b48bbac6385f07a5df47c773a7376b5a74d4ee082a8d"
for command in git gh sha256sum; do
  command -v "$command" >/dev/null 2>&1 || { printf 'Falta %s en el sistema.\n' "$command" >&2; exit 1; }
done
[ -f "$TAP" ] || { echo 'No encuentro el TAP V1.6. Extrae el paquete completo antes de ejecutar el script.' >&2; exit 1; }
echo "$SHA  $TAP" | sha256sum -c - >/dev/null || { echo 'El TAP no coincide con la V1.6 publicada.' >&2; exit 1; }
gh auth status >/dev/null

# Protección: si la Release v1.6 ya existe no se toca nada.
if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  echo "La Release $TAG ya está publicada. No se modifica main ni se reemplazan archivos."
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
printf '\nClonando %s ...\n' "$REMOTE"
git clone --branch main "$REMOTE" "$TMP/repo"
# El paquete ya es el árbol completo de main: se sustituye entero (sin tocar .git).
find "$TMP/repo" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -a "$ROOT/." "$TMP/repo/"
rm -rf "$TMP/repo/build" "$TMP/repo/.venv"
cd "$TMP/repo"
git add -A
if git diff --cached --quiet; then
  echo 'La rama main ya contiene esta versión.'
else
  echo 'Cambios que se van a publicar:'
  git --no-pager diff --cached --stat | tail -5
  git commit -q -F - <<'MSG'
release: GRIT CLAYMORE V1.6

Remozado gráfico integral, un jefe por fase, más enemigos y dificultad,
cañón de plasma en la fase 3, raciones por sector, tanque de cuatro
impactos, Kempston automático y scroll que ya no atrapa a Grit.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
MSG
  git push origin HEAD:main
fi
echo "Creando Release pública $TAG ..."
gh release create "$TAG" \
  "$TAP" \
  "$ROOT/recursos/V1.5/PLASMA_FASE_3.png" \
  "$ROOT/recursos/V1.2/TARJETA_FASE_3.png" \
  "$ROOT/caratula/GRIT_CLAYMORE_CARATULA_OFICIAL.png" \
  "$ROOT/documentacion/ATLAS_VISUAL_Y_MEMORIA.pdf" \
  "$ROOT/documentacion/MANUAL_DE_INSTRUCCIONES.pdf" \
  --repo "$REPO" --target main \
  --title 'GRIT CLAYMORE V1.6' \
  --notes-file "$ROOT/RELEASE_NOTES_V1.6.md" \
  --latest
printf '\nPUBLICADO: https://github.com/OnRail76/Grit-Claymore/releases/tag/%s\n' "$TAG"
