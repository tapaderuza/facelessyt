"""Bounded public-thumbnail retrieval + OpenCV descriptors + auditable OCR.

No competitor CTR is available here. Current thumbnails may differ from those
used when the view snapshot was collected. Measurements are not design scores.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 4_000_000


def video_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"www.youtube.com", "youtube.com", "youtu.be"}:
        raise ValueError("Not an HTTPS YouTube video URL")
    value = parsed.path.strip("/") if parsed.hostname == "youtu.be" else parse_qs(parsed.query).get("v", [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        raise ValueError("Invalid YouTube video ID")
    return value


def validate_thumbnail_url(url: str, vid: str) -> None:
    p = urlparse(url)
    if (p.scheme != "https" or p.hostname != "i.ytimg.com" or p.port not in (None, 443)
            or p.username or p.password or p.query or p.fragment
            or not re.fullmatch(rf"/vi(?:_webp)?/{re.escape(vid)}/[A-Za-z0-9_-]+\.(?:jpg|webp)", p.path)):
        raise ValueError("Thumbnail URL outside allowlisted YouTube CDN/video")


def check_image(raw: bytes):
    from PIL import Image
    if len(raw) > MAX_BYTES:
        raise ValueError("Thumbnail exceeds byte limit")
    with Image.open(io.BytesIO(raw)) as im:
        if im.format not in {"JPEG", "PNG", "WEBP"} or im.width * im.height > MAX_PIXELS:
            raise ValueError("Unsupported or oversized image")
        if im.width < 300 or im.height < 160:
            raise ValueError("Thumbnail is tiny/placeholder")
        im.load()
        return im.convert("RGB")


def fetch_thumbnail(row: dict, directory: Path, *, session=None, refresh=False) -> tuple[Path, dict]:
    vid = video_id(row["url"])
    directory.mkdir(parents=True, exist_ok=True)
    target, meta = directory / f"{vid}.jpg", directory / f"{vid}.capture.json"
    if not refresh and target.exists() and meta.exists():
        raw = target.read_bytes()
        record = json.loads(meta.read_text(encoding="utf-8"))
        if hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("Thumbnail cache hash mismatch; use --refresh")
        check_image(raw)
        return target, record
    urls = [row["thumbnail_url"]] if row.get("thumbnail_url") else []
    urls += [f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg", f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"]
    errors = []
    client = session or requests.Session()
    try:
        for url in dict.fromkeys(urls):
            validate_thumbnail_url(url, vid)
            try:
                with client.get(url, stream=True, timeout=(5, 20), allow_redirects=False) as response:
                    if response.status_code != 200:
                        raise ValueError(f"HTTP {response.status_code}; redirects disallowed")
                    if int(response.headers.get("Content-Length", "0")) > MAX_BYTES:
                        raise ValueError("Thumbnail exceeds byte limit")
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise ValueError("Thumbnail exceeds byte limit")
                        chunks.append(chunk)
                raw = b"".join(chunks)
                check_image(raw)
                record = {"video_id": vid, "source_url": url, "captured_at": datetime.now(timezone.utc).isoformat(),
                          "sha256": hashlib.sha256(raw).hexdigest(), "historical_thumbnail_verified": False}
                target.write_bytes(raw)
                meta.write_text(json.dumps(record, indent=2), encoding="utf-8")
                return target, record
            except (requests.RequestException, ValueError, OSError) as exc:
                errors.append(f"{type(exc).__name__}: {str(exc)[:180]}")
        raise ValueError("No usable thumbnail: " + "; ".join(errors))
    finally:
        if session is None:
            client.close()


def ocr_words(data: dict, threshold=50) -> list[dict]:
    words = []
    for i, text in enumerate(data["text"]):
        confidence = float(data["conf"][i])
        if confidence < threshold or not any(c.isalnum() for c in text):
            continue
        words.append({"text": text.strip(), "confidence": round(confidence, 2),
                      "box": [int(data[k][i]) for k in ("left", "top", "width", "height")]})
    return words


def analyse(path: Path) -> dict:
    import cv2
    import numpy as np
    import pytesseract
    rgb = np.array(check_image(path.read_bytes()))
    grey = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    report = {"width": rgb.shape[1], "height": rgb.shape[0],
        "contrast_std_0_1": round(float(grey.std()) / 255, 4),
        "contrast_p95_p05_0_1": round(float(np.percentile(grey, 95) - np.percentile(grey, 5)) / 255, 4),
        "mean_saturation_0_1": round(float(hsv[:, :, 1].mean()) / 255, 4),
        "ocr_word_count": None, "ocr_words": [], "ocr_status": "unavailable",
        "ocr_prominent_word_count": None,
        "ocr_prominent_rule": "Accepted word box height >=6% of image height; heuristic, not verified headline text",
        "ocr_config": {"language": "eng", "psm": 11, "min_confidence": 50},
        "opencv_version": cv2.__version__, "ctr": None,
        "ctr_reason": "Competitor impression CTR is not provided by public thumbnail/Data API",
        "human_review_required": True}
    try:
        report["tesseract_version"] = str(pytesseract.get_tesseract_version())
        data = pytesseract.image_to_data(rgb, lang="eng", config="--psm 11", timeout=20,
                                        output_type=pytesseract.Output.DICT)
        words = ocr_words(data)
        report.update(ocr_status="ok", ocr_word_count=len(words), ocr_words=words)
        report["ocr_prominent_word_count"] = sum(w["box"][3] >= rgb.shape[0] * .06 for w in words)
    except (pytesseract.TesseractNotFoundError, pytesseract.TesseractError, RuntimeError) as exc:
        report["ocr_error"] = str(exc)[:200]
    return report


def research(rows: list[dict], directory: Path, *, refresh=False) -> dict:
    # Import before network so missing optional dependencies fail clearly.
    try:
        import cv2, pytesseract  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Install facelessyt[vision] and Tesseract, or use Dockerfile.research") from exc
    results = []
    for row in {r["url"]: r for r in rows}.values():
        result = {"video_url": row["url"], "title": row["title"], "channel_title": row["channel_title"]}
        try:
            path, capture = fetch_thumbnail(row, directory, refresh=refresh)
            metrics = analyse(path)
            result.update(status="ok" if metrics["ocr_status"] == "ok" else "partial",
                          file=path.name, capture=capture, metrics=metrics)
        except (requests.RequestException, ValueError, OSError) as exc:
            result.update(status="error", error=f"{type(exc).__name__}: {exc}", ctr=None)
        results.append(result)
    report = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
              "claim": "Current thumbnail descriptors, not historic winning design or CTR predictors", "results": results}
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
