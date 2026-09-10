"""Interfaz de linea de comandos.

  python -m facelessyt mine   --niche ai-automation
  python -m facelessyt track
  python -m facelessyt check
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from . import config
from .youtube import Client, YouTubeError

# La consola de Windows usa cp1252 por defecto y no sabe pintar los apostrofes
# tipograficos ni los guiones largos que traen los titulos de YouTube: los datos
# son correctos, pero se veian como "?". Forzar UTF-8 en la salida lo arregla.
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

console = Console()

# Por debajo de esto, el handle resuelve pero casi seguro no es el canal buscado
# (handles abandonados que ocupa otra cuenta).
MIN_SEED_VIDEOS = 20


def _fmt(n: int | None) -> str:
    if n is None:
        return "oculto"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def cmd_mine(args: argparse.Namespace) -> int:
    from . import miner

    niche = config.load_niche(args.niche)
    client = Client(key=config.api_key())

    console.print(
        f"[bold]Minando '{niche['name']}'[/bold] - "
        f"{len(niche['seed_channels'])} canales semilla, "
        f"score minimo {args.min_score}, ultimos {args.days:.0f} dias\n"
    )

    outliers, warnings = miner.mine(
        client,
        niche,
        min_score=args.min_score,
        max_age_days=args.days,
        per_channel=args.per_channel,
        include_shorts=args.shorts,
    )

    for warning in warnings:
        console.print(f"[yellow]aviso[/yellow] {warning}")
    if warnings:
        console.print()

    if not outliers:
        console.print(
            "[yellow]Ningun outlier.[/yellow] O el nicho esta plano, o los canales semilla "
            "no son representativos. Prueba --min-score 2 o revisa el yaml del nicho."
        )
    else:
        table = Table(title=f"{len(outliers)} temas con demanda probada")
        table.add_column("Score", justify="right", style="bold green")
        table.add_column("Views", justify="right")
        table.add_column("Titulo", max_width=58, overflow="ellipsis")
        table.add_column("Canal", max_width=22, overflow="ellipsis")
        table.add_column("Subs", justify="right")
        table.add_column("Dias", justify="right")
        table.add_column("Min", justify="right")

        for o in outliers[: args.limit]:
            table.add_row(
                f"{o.score:.1f}x",
                _fmt(o.views),
                o.title,
                o.channel_title,
                _fmt(o.channel_subs),
                f"{o.age_days:.0f}",
                f"{o.duration_min:.0f}",
            )
        console.print(table)

        console.print("\n[dim]Enlaces de los 10 primeros:[/dim]")
        for o in outliers[:10]:
            console.print(f"  [dim]{o.score:5.1f}x[/dim]  {o.url}")

    path = miner.save(outliers, niche["name"])
    console.print(f"\nGuardado en [cyan]{path}[/cyan]")
    console.print(f"[dim]Cuota consumida: {client.quota_used} / 10000 unidades[/dim]")
    return 0


def cmd_track(args: argparse.Namespace) -> int:
    from . import tracker

    client = Client(key=config.api_key())
    channel_id = args.channel or config.my_channel_id()
    verdict, title = tracker.snapshot(client, channel_id)

    console.print(f"\n[bold]{title}[/bold]\n")

    if verdict.videos_published == 0:
        console.print("[yellow]Todavia no hay videos long-form publicados.[/yellow]")
        return 0

    table = Table(show_header=False, box=None)
    table.add_column(style="dim", width=28)
    table.add_column()
    table.add_row("Videos publicados", f"{verdict.videos_published} / {tracker.TARGET_VIDEOS}")
    table.add_row("Dias desde el primero", f"{verdict.days_elapsed:.0f} / {tracker.TEST_DAYS}")
    table.add_row("Al ritmo previsto", "si" if verdict.on_pace else "[red]NO[/red]")
    table.add_row("", "")
    table.add_row(
        f"Hits (mas de {tracker.HIT_THRESHOLD} views)",
        f"{verdict.hits} / {tracker.HITS_REQUIRED} necesarios",
    )
    table.add_row("Mejor video", _fmt(verdict.best_views))
    table.add_row("Mediana primer tercio", _fmt(int(verdict.median_first_third)))
    table.add_row("Mediana ultimo tercio", _fmt(int(verdict.median_last_third)))
    table.add_row("Tendencia", "subiendo" if verdict.trend_up else "[red]plana o bajando[/red]")
    console.print(table)

    console.print("\n[dim]Top 5:[/dim]")
    for t, v in verdict.top:
        console.print(f"  {_fmt(v):>7}  {t[:64]}")

    console.print()
    if verdict.passes:
        console.print("[bold green]PASA EL CORTE[/bold green] - hay senal. Escalar volumen.")
    elif verdict.days_elapsed < tracker.TEST_DAYS:
        falta = tracker.TEST_DAYS - verdict.days_elapsed
        console.print(f"[yellow]En curso[/yellow] - quedan {falta:.0f} dias para decidir.")
    else:
        console.print(
            "[bold red]NO PASA EL CORTE[/bold red] - se mata el canal.\n"
            "Antes de pivotar, mira CTR y retencion en YouTube Studio "
            "(docs/00-estrategia.md, tabla de diagnostico)."
        )
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Verifica que la configuracion y los canales semilla funcionan."""
    client = Client(key=config.api_key())
    console.print("[green]OK[/green] clave de API leida")

    niche = config.load_niche(args.niche)
    console.print(f"[green]OK[/green] nicho '{niche['name']}' cargado\n")

    table = Table(title="Canales semilla")
    table.add_column("Referencia")
    table.add_column("Estado")
    table.add_column("Canal")
    table.add_column("Subs", justify="right")
    table.add_column("Videos", justify="right")

    bad = 0
    for ref in niche["seed_channels"]:
        try:
            channel = client.resolve_channel(ref)
        except YouTubeError as exc:
            table.add_row(ref, "[red]ERROR[/red]", str(exc)[:40], "", "")
            bad += 1
            continue
        if channel is None:
            table.add_row(ref, "[red]NO EXISTE[/red]", "", "", "")
            bad += 1
        elif channel.video_count < MIN_SEED_VIDEOS:
            # Un handle libre lo ocupa cualquiera: resuelve, pero no es el canal
            # que buscabas. Falla en verde si no se comprueba el volumen.
            table.add_row(
                ref,
                "[red]SOSPECHOSO[/red]",
                channel.title,
                _fmt(channel.subscribers),
                str(channel.video_count),
            )
            bad += 1
        else:
            table.add_row(
                ref,
                "[green]OK[/green]",
                channel.title,
                _fmt(channel.subscribers),
                str(channel.video_count),
            )
    console.print(table)
    console.print(f"\n[dim]Cuota consumida: {client.quota_used} / 10000[/dim]")

    if bad:
        console.print(
            f"\n[yellow]{bad} referencia(s) con problemas.[/yellow] "
            f"Corrigelas en niches/{args.niche}.yaml - los handles cambian, y los "
            f"abandonados los ocupa otra cuenta (por eso el aviso SOSPECHOSO)."
        )
    return 1 if bad else 0


def cmd_auth(args: argparse.Namespace) -> int:
    """Da consentimiento OAuth una vez y guarda el token."""
    from . import auth

    console.print("Se va a abrir el navegador para autorizar el acceso al canal.")
    console.print(
        "[dim]Veras un aviso de 'app no verificada'. Es lo esperado: la "
        "verificacion de Google solo hace falta para autorizar a terceros.\n"
        "Avanzado -> Ir a Outlier Engineering.[/dim]\n"
    )
    try:
        auth.credentials(interactive=True)
    except auth.AuthError as exc:
        console.print(f"[red]{exc}[/red]")
        return 2
    except Exception as exc:  # el flujo envuelve el error de Google
        if "access_denied" in str(exc) or "403" in str(exc):
            console.print(
                "[red]Google ha bloqueado el acceso (403 access_denied).[/red]\n\n"
                "La app esta en modo Testing y tu cuenta no esta en la lista de "
                "usuarios de prueba.\n\n"
                "[bold]Arreglo:[/bold] Google Auth Platform -> Audience -> "
                "Test users -> Add users -> el correo dueno del canal.\n\n"
                "[dim]En modo Testing el refresh token caduca a los 7 dias, asi "
                "que habra que repetir esto de vez en cuando. Solo afecta a "
                "'upload' y 'diagnose': 'track', 'mine' y 'check' van con la "
                "clave de API y no se enteran.\n"
                "Pasar a produccion evitaria la caducidad, pero exige URL de "
                "homepage y de politica de privacidad, que para un unico usuario "
                "no compensa.[/dim]"
            )
            return 3
        raise

    yt = auth.youtube(interactive=False)
    me = yt.channels().list(part="snippet,statistics", mine=True).execute()
    item = (me.get("items") or [{}])[0]
    console.print(
        f"[green]Autorizado[/green] como [bold]{item.get('snippet', {}).get('title', '?')}[/bold]"
    )
    console.print(f"[dim]Token guardado en {auth.TOKEN}[/dim]")
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    """CTR y retencion: por que un video funciona o no."""
    from . import analytics

    results = analytics.diagnose(days=args.days)
    if not results:
        console.print(
            "[yellow]Sin datos todavia.[/yellow] Analytics tarda 24-48h en reportar "
            "un video recien publicado."
        )
        return 0

    for r in results:
        console.print(f"\n[bold]{r.title[:70]}[/bold]")
        table = Table(show_header=False, box=None)
        table.add_column(style="dim", width=24)
        table.add_column()

        def mark(value, threshold, unit="%"):
            if value is None:
                return "[dim]sin datos[/dim]"
            ok = value >= threshold
            colour = "green" if ok else "red"
            return f"[{colour}]{value}{unit}[/{colour}] [dim](minimo {threshold}{unit})[/dim]"

        table.add_row("Views", str(r.views))
        table.add_row("Impresiones", str(r.impressions) if r.impressions else "[dim]-[/dim]")
        table.add_row("CTR", mark(r.ctr, analytics.CTR_MIN))
        table.add_row("Retencion 30s", mark(r.retention_30s, analytics.RETENTION_30S_MIN))
        table.add_row("Retencion media", mark(r.avg_view_percentage, analytics.RETENTION_AVG_MIN))
        table.add_row("Subs ganados", str(r.subscribers_gained or 0))
        console.print(table)
        console.print(f"  -> [bold]{r.verdict}[/bold]")
    return 0


def cmd_upload(args: argparse.Namespace) -> int:
    """Sube el video al canal, SIEMPRE como privado."""
    from . import upload as up

    video = Path(args.video)
    thumb = Path(args.thumbnail) if args.thumbnail else None
    description = Path(args.description).read_text(encoding="utf-8") if args.description else ""

    console.print(f"Subiendo [cyan]{video.name}[/cyan] ({video.stat().st_size / 1e6:.0f} MB)")
    console.print("[dim]Se subira como PRIVADO. Publicar es decision tuya.[/dim]\n")

    last = {"pct": -1}

    def progress(pct: int) -> None:
        if pct >= last["pct"] + 10:
            last["pct"] = pct
            console.print(f"  {pct}%")

    try:
        result = up.upload(
            video,
            title=args.title,
            description=description,
            tags=[t.strip() for t in (args.tags or "").split(",") if t.strip()],
            thumbnail=thumb,
            on_progress=progress,
        )
    except up.PreflightError as exc:
        console.print(f"[red]No se sube:[/red] {exc}")
        return 4
    console.print(f"\n[green]Subido[/green] como {result.privacy}")
    console.print(f"  {result.url}")
    if result.thumbnail_error:
        console.print(f"\n[yellow]La miniatura no se puso:[/yellow] {result.thumbnail_error}")
    console.print("[dim]Revisalo entero antes de hacerlo publico.[/dim]")
    return 0


def cmd_thumbnail(args: argparse.Namespace) -> int:
    from . import upload as up

    up.set_thumbnail(args.video_id, Path(args.thumbnail))
    console.print("[green]Miniatura puesta[/green]")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    from . import upload as up

    url = up.publish(args.video_id, privacy=args.privacy)
    console.print(f"[green]Visibilidad cambiada a {args.privacy}[/green]")
    console.print(f"  {url}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="facelessyt", description="Operativa de canal faceless")
    sub = parser.add_subparsers(dest="command", required=True)

    p_mine = sub.add_parser("mine", help="busca temas con demanda probada en un nicho")
    p_mine.add_argument("--niche", default="ai-automation")
    p_mine.add_argument("--min-score", type=float, default=3.0)
    p_mine.add_argument("--days", type=float, default=180, help="antiguedad maxima del video")
    p_mine.add_argument("--per-channel", type=int, default=60)
    p_mine.add_argument("--limit", type=int, default=40, help="filas a mostrar")
    p_mine.add_argument("--shorts", action="store_true", help="incluir shorts")
    p_mine.set_defaults(func=cmd_mine)

    p_track = sub.add_parser("track", help="evalua la metrica de corte de los 90 dias")
    p_track.add_argument("--channel", help="ID del canal; por defecto MY_CHANNEL_ID del .env")
    p_track.set_defaults(func=cmd_track)

    p_check = sub.add_parser("check", help="verifica clave de API y canales semilla")
    p_check.add_argument("--niche", default="ai-automation")
    p_check.set_defaults(func=cmd_check)

    p_auth = sub.add_parser("auth", help="autoriza el acceso al canal (una sola vez)")
    p_auth.set_defaults(func=cmd_auth)

    p_diag = sub.add_parser("diagnose", help="CTR y retencion de tus videos")
    p_diag.add_argument("--days", type=int, default=28)
    p_diag.set_defaults(func=cmd_diagnose)

    p_up = sub.add_parser("upload", help="sube un video al canal, como privado")
    p_up.add_argument("--video", required=True)
    p_up.add_argument("--title", required=True)
    p_up.add_argument("--description", help="fichero con la descripcion")
    p_up.add_argument("--thumbnail")
    p_up.add_argument("--tags", help="separadas por comas")
    p_up.set_defaults(func=cmd_upload)

    p_thumb = sub.add_parser("thumbnail", help="pone la miniatura de un video ya subido")
    p_thumb.add_argument("--video-id", required=True)
    p_thumb.add_argument("--thumbnail", required=True)
    p_thumb.set_defaults(func=cmd_thumbnail)

    p_pub = sub.add_parser("publish", help="cambia la visibilidad de un video subido")
    p_pub.add_argument("--video-id", required=True)
    p_pub.add_argument("--privacy", default="public",
                       choices=["public", "unlisted", "private"])
    p_pub.set_defaults(func=cmd_publish)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except config.ConfigError as exc:
        console.print(f"[red]Configuracion:[/red] {exc}")
        return 2
    except YouTubeError as exc:
        console.print(f"[red]API de YouTube:[/red] {exc}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
