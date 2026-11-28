# yt-auto

Detector de vídeos virales y buscador de nichos para YouTube, con la YouTube Data API v3.

## Qué hace

- `collect`: descarga tendencias (`mostPopular`) de ES, MX y US, y los vídeos más vistos de los últimos 7 días para cada nicho de `config.yaml`. Guarda un snapshot de vistas en SQLite.
- `top`: ordena los vídeos por puntuación de viralidad.
- `niches`: ordena los nichos según dónde canales pequeños consiguen vídeos muy por encima de su media.

## Métrica

- **VPH**: vistas / horas desde la publicación.
- **Outlier**: vistas / mediana de vistas de los últimos 30 vídeos del canal.
- **Aceleración**: VPH entre dos snapshots / VPH medio anterior.
- **Puntuación**: log10(VPH) × min(outlier, 50) × aceleración.

Un nicho tiene oportunidad si muchos vídeos superan 5× la mediana de su canal, sobre todo en canales de menos de 50.000 suscriptores.

## Uso

```bash
pip install -r requirements.txt
cp .env.example .env   # pon tu YOUTUBE_API_KEY
python -m ytauto collect   # ~5.000 unidades de cuota con la config por defecto
python -m ytauto niches
python -m ytauto top --shorts -n 30
```

Ejecuta `collect` dos veces separadas unas horas para obtener la aceleración.

## Cuota

10.000 unidades/día gratis. `search.list` = 100, `videos.list`/`channels.list`/`playlistItems.list` = 1. El presupuesto por ejecución se fija en `quota_budget`.

## Tests

```bash
python -m pytest -q
```

## Panel del canal (aplicación de escritorio)

```bash
pip install pywebview
python -m ytauto.app     # abre la ventana; «Actualizar» pide los datos a YouTube y TikTok
python -m ytauto.panel   # solo escribe reports/panel/*.json, sin ventana
```

**Windows (.exe)**: descarga `DatoCrackPanel.exe` de la última ejecución de la acción «App de escritorio (.exe)» en GitHub (pestaña Actions, apartado Artifacts) y ponlo en la carpeta del repo, junto a `.env`, `token.json` y `data/`. Doble clic para abrirlo. Necesita WebView2, que ya viene en Windows 10 y 11.

En tu PC, añade a `.env` las rutas que no estén en la raíz del repo: `YT_PROJECT_DIR` (carpeta con `shorts/`, `b3d/` y `voces/cache`), `YT_SECRETS_DIR` (tokens de TikTok) y `YT_TOKEN_FILE` (token de YouTube).

Junta YouTube Data API, YouTube Analytics (retención, % visto, suscriptores, tráfico, países), TikTok y el registro local (`data/uploads.json`, guiones, fotogramas 3D, caché de voz Gemini). Los costes son estimaciones: precios en `PRICES` de `ytauto/panel.py`. Las ideas de mejora están en `data/ideas.json`. Los JSON se suben al panel de Claude.
