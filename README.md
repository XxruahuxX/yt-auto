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
