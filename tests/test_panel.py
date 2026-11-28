from ytauto.app import NAMES, Api
from ytauto.panel import _iso_dur


def test_iso_dur():
    assert _iso_dur("PT47S") == 47
    assert _iso_dur("PT1M5S") == 65
    assert _iso_dur("") == 0


def test_datos_devuelve_todas_las_fuentes_o_error():
    r = Api().datos()
    assert "error" in r or set(NAMES) <= set(r)
