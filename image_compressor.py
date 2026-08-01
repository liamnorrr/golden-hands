#!/usr/bin/env python3
"""Convert JPG images to WebP, targeting a specific output file size range."""

import argparse
import sys
from pathlib import Path

from PIL import Image

TARGET_MIN_KB = 150
TARGET_MAX_KB = 300
MIN_QUALITY = 20
MAX_QUALITY = 95


def compress_to_target(src: Path, dst: Path, target_min_kb: int, target_max_kb: int) -> None:
    img = Image.open(src).convert("RGB")

    target_min = target_min_kb * 1024
    target_max = target_max_kb * 1024

    best_bytes = None
    best_quality = None
    lo, hi = MIN_QUALITY, MAX_QUALITY

    while lo <= hi:
        quality = (lo + hi) // 2
        img.save(dst, format="WEBP", quality=quality, method=6)
        size = dst.stat().st_size

        if best_bytes is None or abs(size - (target_min + target_max) / 2) < abs(
            best_bytes - (target_min + target_max) / 2
        ):
            best_bytes = size
            best_quality = quality

        if size < target_min:
            lo = quality + 1
        elif size > target_max:
            hi = quality - 1
        else:
            break

    if best_quality != quality:
        img.save(dst, format="WEBP", quality=best_quality, method=6)
        size = dst.stat().st_size
    else:
        size = dst.stat().st_size

    status = "OK" if target_min <= size <= target_max else "closest match"
    print(
        f"{src.name} -> {dst.name}: quality={best_quality}, "
        f"{size / 1024:.1f} KB ({status})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="JPG files or directories to compress")
    parser.add_argument(
        "-o", "--output-dir", type=Path, default=None,
        help="Directory to write .webp files to (default: alongside source)",
    )
    parser.add_argument("--min-kb", type=int, default=TARGET_MIN_KB)
    parser.add_argument("--max-kb", type=int, default=TARGET_MAX_KB)
    args = parser.parse_args()

    files = []
    for raw in args.inputs:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(p.glob("*.jpg")) + sorted(p.glob("*.jpeg")))
        elif p.is_file():
            files.append(p)
        else:
            print(f"skip: {p} not found", file=sys.stderr)

    if not files:
        print("No JPG files found.", file=sys.stderr)
        sys.exit(1)

    for src in files:
        out_dir = args.output_dir or src.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        dst = out_dir / (src.stem + ".webp")
        compress_to_target(src, dst, args.min_kb, args.max_kb)


if __name__ == "__main__":
    main()
