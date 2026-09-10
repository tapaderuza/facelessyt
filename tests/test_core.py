"""Tests de la logica pura (sin red).

Ejecutar:  .venv/Scripts/python.exe tests/test_core.py
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from facelessyt.miner import analyse_channel
from facelessyt.tracker import evaluate
from facelessyt.youtube import Channel, Video, parse_duration

NOW = datetime.now(timezone.utc)


def video(vid: str, views: int, days_old: float, duration_s: int = 600) -> Video:
    return Video(
        video_id=vid,
        title=f"Video {vid}",
        channel_id="UC1",
        channel_title="Canal",
        published=NOW - timedelta(days=days_old),
        views=views,
        likes=10,
        comments=5,
        duration_s=duration_s,
    )


CHANNEL = Channel("UC1", "Canal", "@canal", 5000, 10, "UU1")


def test_parse_duration():
    assert parse_duration("PT12M31S") == 751
    assert parse_duration("PT1H2M3S") == 3723
    assert parse_duration("PT45S") == 45
    assert parse_duration("P1DT2H") == 93600
    assert parse_duration("") == 0
    assert parse_duration("basura") == 0


def test_outlier_detectado():
    videos = [video(str(i), 1000, 30) for i in range(9)] + [video("hit", 9000, 30)]
    found, base = analyse_channel(
        CHANNEL, videos, min_score=3, max_age_days=180, include_shorts=False
    )
    assert base == 1000
    assert len(found) == 1
    assert found[0].score == 9.0


def test_videos_inmaduros_se_ignoran():
    """Un video de 2 dias no ha acumulado views: no puede puntuar todavia."""
    videos = [video(str(i), 1000, 30) for i in range(9)] + [video("nuevo", 9000, 2)]
    found, _ = analyse_channel(
        CHANNEL, videos, min_score=3, max_age_days=180, include_shorts=False
    )
    assert found == []


def test_shorts_excluidos_del_baseline():
    """Los shorts inflan/deflactan la mediana: fuera salvo que se pidan."""
    videos = [video(str(i), 1000, 30) for i in range(9)]
    videos += [video(f"s{i}", 50_000, 30, duration_s=45) for i in range(5)]
    found, base = analyse_channel(
        CHANNEL, videos, min_score=3, max_age_days=180, include_shorts=False
    )
    assert base == 1000, "los shorts no deben entrar en la mediana"
    assert found == []


def test_canal_con_pocos_videos_se_descarta():
    videos = [video(str(i), 1000, 30) for i in range(3)]
    found, base = analyse_channel(
        CHANNEL, videos, min_score=3, max_age_days=180, include_shorts=False
    )
    assert base is None and found == []


def test_corte_pasa_con_3_hits_y_tendencia():
    videos = [
        video("a", 500, 80), video("b", 800, 70), video("c", 1200, 60),
        video("d", 11_000, 50), video("e", 15_000, 40), video("f", 30_000, 30),
    ]
    result = evaluate(videos)
    assert result.hits == 3
    assert result.trend_up
    assert result.passes


def test_corte_falla_si_plano():
    videos = [
        video("a", 500, 80), video("b", 400, 70), video("c", 600, 60),
        video("d", 450, 50), video("e", 500, 40), video("f", 380, 30),
    ]
    result = evaluate(videos)
    assert result.hits == 0
    assert not result.passes


def test_corte_falla_con_hits_pero_sin_tendencia():
    """Tres pelotazos al principio y luego caida no es un canal viable."""
    videos = [
        video("a", 40_000, 80), video("b", 30_000, 70), video("c", 20_000, 60),
        video("d", 900, 50), video("e", 700, 40), video("f", 500, 30),
    ]
    result = evaluate(videos)
    assert result.hits == 3
    assert not result.trend_up
    assert not result.passes


def test_canal_vacio():
    result = evaluate([])
    assert result.videos_published == 0 and not result.passes


def test_raiz_respeta_override_de_entorno():
    """Instalado en site-packages (contenedor) la raiz no se puede deducir
    subiendo desde __file__: hace falta el override. Regresion del bug que
    solo aparecio al ejecutar en Docker."""
    import importlib
    import os

    from facelessyt import config

    previo = os.environ.get("FACELESSYT_ROOT")
    os.environ["FACELESSYT_ROOT"] = "/tmp/otra-raiz"
    try:
        assert config._detect_root() == Path("/tmp/otra-raiz")
    finally:
        if previo is None:
            os.environ.pop("FACELESSYT_ROOT", None)
        else:
            os.environ["FACELESSYT_ROOT"] = previo
        importlib.reload(config)


def test_raiz_detecta_layout_de_repo():
    from facelessyt import config

    assert (config.ROOT / "niches").is_dir(), "en el repo, niches/ cuelga de la raiz"


# -- clusters -------------------------------------------------------------

def _outlier(title, score=5.0, channel="C1", age=30.0):
    return {"title": title, "score": score, "channel_title": channel, "age_days": age}


def test_cluster_asigna_por_patron():
    from facelessyt.clusters import assign

    assert "agentic engineering / harnesses" in assign("Build an agentic harness")
    assert assign("How I cook pasta") == []


def test_cluster_saturado_cuando_muchos_canales():
    from facelessyt.clusters import summarise

    items = [_outlier("build ai agent", channel=f"C{i}") for i in range(5)]
    estado = summarise(items)[0]
    assert len(estado.channels) == 5
    assert estado.saturated


def test_frescura_es_relativa_a_la_ventana():
    """Regresion: con umbral absoluto de 90 dias, minar 180 dias marcaba como
    agotado casi todo, porque la edad mediana esperada ES 90."""
    from facelessyt.clusters import summarise

    items = [_outlier("agentic harness", age=95.0) for _ in range(3)]

    en_180 = summarise(items, window_days=180)[0]
    assert not en_180.stale, "95 dias dentro de una ventana de 180 es normal"

    en_120 = summarise(items, window_days=120)[0]
    assert en_120.stale, "95 dias dentro de una ventana de 120 si es viejo"


def test_temperatura_sin_historico_es_nuevo():
    from facelessyt.clusters import ClusterState, ClusterTrend

    ahora = ClusterState("x", 3, 5.0, 7.0, ["A"], 20.0, 180.0)
    assert ClusterTrend("x", ahora, None).temperature == "nuevo"


def test_temperatura_detecta_enfriamiento():
    from facelessyt.clusters import ClusterState, ClusterTrend

    antes = ClusterState("x", 8, 6.0, 9.0, ["A", "B"], 40.0, 180.0)
    ahora = ClusterState("x", 5, 4.0, 6.0, ["A"], 60.0, 180.0)
    tr = ClusterTrend("x", ahora, antes)
    assert tr.temperature == "enfriando"
    assert tr.score_delta == -2.0


def test_saturado_y_enfriando_se_evita():
    from facelessyt.clusters import ClusterState, ClusterTrend

    antes = ClusterState("x", 9, 7.0, 9.0, ["A", "B", "C", "D"], 30.0, 180.0)
    ahora = ClusterState("x", 6, 5.0, 7.0, ["A", "B", "C", "D"], 40.0, 180.0)
    assert ClusterTrend("x", ahora, antes).verdict.startswith("evitar")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  OK    {test.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"  FALLO {test.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests pasan")
    raise SystemExit(1 if failed else 0)
