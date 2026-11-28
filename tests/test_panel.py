from ytauto.app import NAMES, Api
from ytauto.panel import _iso_dur


def test_iso_dur():
    assert _iso_dur("PT47S") == 47
    assert _iso_dur("PT1M5S") == 65
    assert _iso_dur("") == 0


def test_datos_devuelve_todas_las_fuentes_o_error():
    r = Api().datos()
    assert "error" in r or set(NAMES) <= set(r)


def test_consejos_marca_gancho_flojo():
    from ytauto.panel import consejos
    base = dict(estado="Publicado", pct_visto=60.0, likes_pct=1.0, vph=50.0, edad_h=48, subs=1,
                vistas=1000, comentarios=2, tiktok="Borrador")
    videos = [dict(base, id=f"v{i}") for i in range(5)]
    ret = [{"id": f"v{i}", "t": t, "retencion": 1.0} for i in range(5) for t in (0.1, 0.5, 1.0)]
    ret = [dict(r, retencion=0.5) if r["id"] == "v0" and r["t"] == 0.1 else r for r in ret]
    consejos(videos, ret)
    assert any(m["tema"] == "Gancho" and m["nivel"] == "alta" for m in videos[0]["mejoras"])
    assert not any(m["tema"] == "Gancho" for m in videos[1]["mejoras"])
