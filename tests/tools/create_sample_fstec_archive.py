#!/usr/bin/env python3
"""Формирование минимального архива scanoval.zip для оффлайн-симуляций."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def create_archive(archive: Path, sources: list[Path], prefix: str | None = None) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as zip_file:
        for source in sources:
            if not source.exists():
                raise FileNotFoundError(f"Источник {source} не найден")
            arcname = source.name if not prefix else f"{prefix.rstrip('/')}/{source.name}"
            zip_file.write(source, arcname)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Создание учебного архива scanoval.zip")
    parser.add_argument(
        "--archive",
        required=True,
        type=Path,
        help="Путь к архиву, который необходимо сформировать",
    )
    parser.add_argument(
        "--source",
        required=True,
        action="append",
        type=Path,
        help="XML-файл OVAL, который нужно добавить в архив (можно указать несколько раз)",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Необязательный префикс каталога внутри архива",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    create_archive(args.archive, args.source, args.prefix)
    print(f"Создан учебный архив {args.archive} из {len(args.source)} файлов")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
