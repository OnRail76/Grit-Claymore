# Publicar todos los archivos en GitHub

El repositorio remoto existe en <https://github.com/OnRail76/Grit-Claymore>.

Como los conectores de publicación de esta sesión solo permiten escribir ficheros de texto, el TAP, los dos PDF, la carátula y los recursos necesitan un envío desde un equipo autenticado en GitHub. **Este paquete ya está completamente preparado.**

## Linux

1. Descomprime `GRIT_CLAYMORE_GITHUB_V1.0_LIMPIO.zip`.
2. Abre una terminal dentro de la carpeta `Grit-Claymore_GitHub_LISTO`.
3. Ejecuta:

```bash
bash PUBLICAR_EN_GITHUB.sh
```

El script clona el repositorio, copia los archivos correctos, realiza el commit y ejecuta `git push origin main` sin forzar ni borrar el historial. Requiere una sesión GitHub autenticada (`gh auth login`, por ejemplo) y una identidad de Git configurada. No solicita contraseñas ni tokens dentro del script.

El script **no compila** ni altera el TAP: publica exactamente el archivo corregido y comprobado. Los fuentes se pueden reconstruir ejecutando `python3 build_all.py` (Pillow + NumPy).

### Comprobación

Archivo: `juego/GRIT_CLAYMORE_V1.0_48K.tap`

SHA-256: `2cc7b6e59ecf1acef6763edf47b4dafe09367339ad796bdf521108b2e1d24dbd`

```
sha256sum juego/GRIT_CLAYMORE_V1.0_48K.tap
```
