#!/usr/bin/env python3
"""Export Markdown reports to DOCX, PDF, or HWPX format."""

import argparse
import subprocess
import sys
from pathlib import Path


def export_to_docx(input_md: str, output: str) -> None:
    """Convert MD to DOCX using pandoc."""
    subprocess.run(
        ["pandoc", input_md, "-o", output, "--from=markdown"],
        check=True,
    )


def export_to_pdf(input_md: str, output: str, language: str = "ko") -> None:
    """Convert MD to PDF using pandoc + xelatex (with language-aware font)."""
    font_args = []
    if language == "ko":
        font_args = ["-V", "mainfont=NanumGothicOTF"]

    subprocess.run(
        [
            "pandoc",
            input_md,
            "-o",
            output,
            "--from=markdown",
            "--pdf-engine=xelatex",
            *font_args,
            "-V",
            "geometry:margin=2.5cm",
        ],
        check=True,
    )


def export_to_hwpx(input_md: str, output: str) -> None:
    """Convert MD to HWPX using hwpx-convert (no preprocessing)."""
    subprocess.run(
        [
            "hwpx-convert",
            input_md,
            "-o",
            output,
            "--no-preprocess",
        ],
        check=True,
    )


EXPORTERS = {
    "docx": export_to_docx,
    "pdf": export_to_pdf,
    "hwpx": export_to_hwpx,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Markdown report to DOCX/PDF/HWPX"
    )
    parser.add_argument("--input", required=True, help="Input Markdown file")
    parser.add_argument(
        "--format",
        required=True,
        choices=["docx", "pdf", "hwpx"],
        help="Output format",
    )
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument(
        "--language",
        default="ko",
        choices=["ko", "en"],
        help="Report language for font selection (default: ko)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    exporter = EXPORTERS[args.format]

    try:
        if args.format == "pdf":
            exporter(args.input, args.output, language=args.language)
        else:
            exporter(args.input, args.output)
        print(f"Exported: {args.output}")
    except FileNotFoundError as e:
        tool = "pandoc" if args.format in ("docx", "pdf") else "hwpx-convert"
        print(
            f"Error: {tool} not found. Install it first.\n{e}",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Export failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
