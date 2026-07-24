#!/usr/bin/env python3
"""Scan text, metadata, images, PDFs, and archives for identity leaks."""
from __future__ import annotations

import argparse
import os
import re
import shutil
import struct
import subprocess
import tempfile
import zipfile
import zlib
from pathlib import Path


TEXT_SUFFIXES = {
    ".txt", ".md", ".tex", ".py", ".m", ".r", ".csv", ".json",
    ".yaml", ".yml", ".ipynb",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


def command_text(command: list[str]) -> tuple[str, str, int]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        return "", "tool unavailable", 127
    return result.stdout, result.stderr, result.returncode


def find_tool(name: str) -> str | None:
    primary = shutil.which(name)
    if (
        primary is None
        or os.name != "nt"
        or Path(primary).suffix.casefold() not in {".cmd", ".bat"}
    ):
        return primary
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / f"{name}.exe"
        try:
            if candidate.is_file():
                return str(candidate)
        except OSError:
            continue
    return primary


def png_text_metadata(path: Path) -> list[str]:
    """Read textual PNG chunks without requiring an imaging dependency."""
    values: list[str] = []
    try:
        with path.open("rb") as handle:
            if handle.read(8) != b"\x89PNG\r\n\x1a\n":
                return values
            while True:
                length_raw = handle.read(4)
                if len(length_raw) != 4:
                    break
                length = struct.unpack(">I", length_raw)[0]
                chunk_type = handle.read(4)
                data = handle.read(length)
                handle.read(4)
                if chunk_type == b"tEXt":
                    values.append(data.replace(b"\x00", b": ").decode("utf-8", errors="replace"))
                elif chunk_type == b"zTXt" and b"\x00" in data:
                    key, compressed = data.split(b"\x00", 1)
                    if compressed[:1] == b"\x00":
                        values.append(
                            key.decode("latin-1", errors="replace")
                            + ": "
                            + zlib.decompress(compressed[1:]).decode("utf-8", errors="replace")
                        )
                elif chunk_type == b"iTXt":
                    values.append(data.replace(b"\x00", b": ").decode("utf-8", errors="replace"))
                if chunk_type == b"IEND":
                    break
    except (OSError, struct.error, zlib.error):
        return values
    return values


def pillow_metadata(path: Path) -> tuple[list[str], str | None]:
    try:
        from PIL import ExifTags, Image
    except ImportError:
        return [], "Pillow unavailable; JPEG/TIFF/WebP embedded metadata received no built-in decoding"
    values: list[str] = []
    try:
        with Image.open(path) as image:
            for key, value in image.info.items():
                if isinstance(value, (str, int, float)):
                    values.append(f"{key}: {value}")
            for key, value in image.getexif().items():
                name = ExifTags.TAGS.get(key, str(key))
                values.append(f"{name}: {value}")
    except (OSError, ValueError):
        return [], f"image metadata could not be decoded: {path.name}"
    return values, None


def ocr_image(path: Path, language: str) -> tuple[str, str | None]:
    tool = find_tool("tesseract")
    if tool is None:
        return "", "tesseract unavailable; requested OCR was not performed"
    stdout, stderr, returncode = command_text(
        [tool, str(path), "stdout", "-l", language]
    )
    if returncode != 0:
        return "", f"OCR failed for {path.name}: {stderr[-240:]}"
    return stdout, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--term", action="append", default=[])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("--ocr-lang", default="eng+chi_sim")
    parser.add_argument("--ocr-dpi", type=int, default=150)
    args = parser.parse_args()
    defaults = [
        r"C:\\Users\\", r"/home/", r"/Users/", r"file://", r"school",
        r"university", r"college", r"institute", "学院", "大学", "学校", "赛区",
    ]
    patterns = [re.compile(value, re.I) for value in defaults + args.term]
    findings: list[str] = []
    limitations: list[str] = []
    notes = [
        "Automated PASS is scoped to inspected filenames, readable text/metadata, "
        "archives, and requested OCR; it is not a complete anonymity guarantee."
    ]

    def add_limitation(message: str) -> None:
        if message not in limitations:
            limitations.append(message)

    def scan(label: str, text: str) -> None:
        for number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in patterns):
                findings.append(f"{label}:{number}: {line[:240]}")

    root = args.root.resolve()
    image_paths: list[Path] = []
    pdf_paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(pattern.search(str(relative)) for pattern in patterns):
            findings.append(f"PATH {relative}")
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in TEXT_SUFFIXES:
            scan(
                f"TEXT {relative}",
                path.read_text(encoding="utf-8", errors="ignore"),
            )
        if suffix in IMAGE_SUFFIXES:
            image_paths.append(path)
            if suffix == ".png":
                scan(f"IMAGE_METADATA {relative}", "\n".join(png_text_metadata(path)))
            metadata, limitation = pillow_metadata(path)
            scan(f"IMAGE_METADATA {relative}", "\n".join(metadata))
            if limitation:
                add_limitation(limitation)
            exiftool = find_tool("exiftool")
            if exiftool:
                stdout, stderr, returncode = command_text(
                    [exiftool, "-j", "-a", "-G1", "-s", str(path)]
                )
                if returncode == 0:
                    scan(f"IMAGE_METADATA {relative}", stdout)
                else:
                    add_limitation(
                        f"exiftool failed for {relative}: {stderr[-240:]}"
                    )
        if suffix == ".pdf":
            pdf_paths.append(path)
            pdfinfo = find_tool("pdfinfo")
            if pdfinfo:
                stdout, stderr, returncode = command_text([pdfinfo, str(path)])
                if returncode == 0:
                    scan(f"PDF_METADATA {relative}", stdout)
                else:
                    add_limitation(f"pdfinfo failed for {relative}: {stderr[-240:]}")
            else:
                add_limitation("pdfinfo unavailable; PDF metadata was not inspected")
            pdftotext = find_tool("pdftotext")
            if pdftotext:
                stdout, stderr, returncode = command_text(
                    [pdftotext, str(path), "-"]
                )
                if returncode == 0:
                    scan(f"PDF_TEXT {relative}", stdout)
                else:
                    add_limitation(
                        f"pdftotext failed for {relative}: {stderr[-240:]}"
                    )
            else:
                add_limitation("pdftotext unavailable; PDF text was not inspected")
        if suffix in {".docx", ".xlsx", ".pptx", ".zip"}:
            try:
                with zipfile.ZipFile(path) as archive:
                    for name in archive.namelist():
                        if any(pattern.search(name) for pattern in patterns):
                            findings.append(f"ARCHIVE_PATH {relative}!{name}")
                        if (
                            name in {"docProps/core.xml", "docProps/app.xml"}
                            or name.endswith(".xml")
                        ):
                            scan(
                                f"ARCHIVE_TEXT {relative}!{name}",
                                archive.read(name).decode("utf-8", errors="ignore"),
                            )
            except zipfile.BadZipFile:
                findings.append(f"UNREADABLE_ARCHIVE {relative}")

    if args.ocr:
        if find_tool("tesseract") is None:
            add_limitation("tesseract unavailable; requested OCR was not performed")
        else:
            for path in image_paths:
                relative = path.relative_to(root)
                text, limitation = ocr_image(path, args.ocr_lang)
                scan(f"IMAGE_OCR {relative}", text)
                if limitation:
                    add_limitation(limitation)
            if pdf_paths:
                pdftoppm = find_tool("pdftoppm")
                if pdftoppm is None:
                    add_limitation(
                        "pdftoppm unavailable; requested rendered-page PDF OCR was not performed"
                    )
                else:
                    with tempfile.TemporaryDirectory(prefix="anonymity-ocr-") as raw:
                        temp_root = Path(raw)
                        for pdf_index, path in enumerate(pdf_paths, 1):
                            relative = path.relative_to(root)
                            prefix = temp_root / f"pdf-{pdf_index}-page"
                            _, stderr, returncode = command_text(
                                [
                                    pdftoppm,
                                    "-png",
                                    "-r",
                                    str(args.ocr_dpi),
                                    str(path),
                                    str(prefix),
                                ]
                            )
                            rendered = sorted(temp_root.glob(f"{prefix.name}-*.png"))
                            if returncode != 0 or not rendered:
                                add_limitation(
                                    f"PDF rendering for OCR failed for {relative}: {stderr[-240:]}"
                                )
                                continue
                            for page_number, image in enumerate(rendered, 1):
                                text, limitation = ocr_image(image, args.ocr_lang)
                                scan(
                                    f"PDF_OCR {relative} page {page_number}",
                                    text,
                                )
                                if limitation:
                                    add_limitation(limitation)
    else:
        notes.append("OCR was not requested; text embedded only in pixels was not inspected.")

    status = "FAIL" if findings else ("LIMITED" if limitations else "PASS")
    lines = [
        f"STATUS {status}",
        "SCOPE scoped automated anonymity scan; not a full guarantee",
    ]
    lines.extend(f"NOTE {note}" for note in notes)
    lines.extend(f"LIMITATION {item}" for item in limitations)
    lines.extend(findings)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{status} findings={len(findings)} limitations={len(limitations)}")
    return 1 if findings else (2 if limitations else 0)


if __name__ == "__main__":
    raise SystemExit(main())
