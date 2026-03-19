"""Image vision utilities - resize, encode, build content blocks."""

from __future__ import annotations

import base64
import io
from pathlib import Path

from loguru import logger
from PIL import Image

_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

_IMAGE_EXTENSIONS = set(_MIME_TYPES.keys())


def is_image(path: str) -> bool:
    """Check if a file path has a known image extension."""
    return Path(path).suffix.lower() in _IMAGE_EXTENSIONS


def encode_image(
    path: str,
    max_long_edge: int = 1024,
    jpeg_quality: int = 85,
) -> tuple[str, str]:
    """Resize and base64-encode an image file.

    Returns (data_uri, mime_type).
    """
    p = Path(path)
    mime = _MIME_TYPES.get(p.suffix.lower(), "image/jpeg")

    with Image.open(p) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            mime = "image/jpeg"

        w, h = img.size
        if max(w, h) > max_long_edge:
            scale = max_long_edge / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        buf = io.BytesIO()
        fmt = "PNG" if mime == "image/png" else "JPEG"
        save_kwargs = {"quality": jpeg_quality} if fmt == "JPEG" else {}
        img.save(buf, format=fmt, **save_kwargs)

    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:{mime};base64,{b64}", mime


def build_vision_content(
    text: str,
    media_paths: list[str],
    *,
    max_images: int = 5,
    max_long_edge: int = 1024,
    detail: str = "low",
) -> list[dict]:
    """Build OpenAI multipart content blocks from text + image paths.

    Non-image files are skipped. Encoding errors become text placeholders.
    """
    parts: list[dict] = []

    if text:
        parts.append({"type": "text", "text": text})

    image_count = 0
    for path in media_paths:
        if not is_image(path):
            continue
        if image_count >= max_images:
            remaining = sum(1 for p in media_paths if is_image(p)) - max_images
            parts.append({"type": "text", "text": f"[{remaining} more image(s) omitted]"})
            break
        try:
            data_uri, _ = encode_image(path, max_long_edge=max_long_edge)
            parts.append({
                "type": "image_url",
                "image_url": {"url": data_uri, "detail": detail},
            })
            image_count += 1
        except Exception as e:
            logger.warning(f"Failed to encode image {path}: {e}")
            parts.append({"type": "text", "text": "[image: failed to process]"})

    return parts
