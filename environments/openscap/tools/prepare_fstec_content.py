#!/usr/bin/env python3
"""Утилита подготовки OVAL-контента ФСТЭК для OpenSCAP и Kaspersky KEA/KSC."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NAMESPACES = {
    "oval-def": "http://oval.mitre.org/XMLSchema/oval-definitions-5",
    "oval": "http://oval.mitre.org/XMLSchema/oval-common-5",
}


@dataclass
class Definition:
    identifier: str
    title: str
    severity: str | None
    family: str | None
    platforms: list[str]


def sanitize_relative_path(member: str) -> Path:
    """Гарантированно формирует безопасный относительный путь."""
    relative = Path(member)
    parts = []
    for part in relative.parts:
        if part in {"", ".", ".."}:
            continue
        parts.append(part)
    if not parts:
        raise ValueError(f"Некорректный путь внутри архива: {member}")
    return Path(*parts)


def parse_definitions(xml_bytes: bytes) -> list[Definition]:
    """Извлекает метаданные определений из XML."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:  # pragma: no cover - диагностика для реальной базы
        raise ValueError(f"Не удалось разобрать OVAL XML: {exc}") from exc

    definitions: list[Definition] = []
    for definition in root.findall("oval-def:definitions/oval-def:definition", NAMESPACES):
        identifier = definition.get("id", "")
        title = definition.findtext("oval-def:metadata/oval-def:title", default="", namespaces=NAMESPACES)
        severity = definition.findtext(
            "oval-def:metadata/oval:advisory/oval:severity", default="", namespaces=NAMESPACES
        )
        severity = severity or None
        family = definition.findtext("oval-def:metadata/oval-def:affected/oval-def:family", namespaces=NAMESPACES)
        family = family or None
        platforms = [
            platform.text.strip()
            for platform in definition.findall(
                "oval-def:metadata/oval-def:affected/oval-def:platform", NAMESPACES
            )
            if platform.text
        ]
        definitions.append(
            Definition(
                identifier=identifier,
                title=title.strip() if title else "",
                severity=severity.strip() if severity else None,
                family=family.strip() if family else None,
                platforms=platforms,
            )
        )
    return definitions


def filter_definitions(definitions: Iterable[Definition], products: list[str] | None) -> list[Definition]:
    if not products:
        return list(definitions)
    lowered = [item.lower() for item in products]
    filtered: list[Definition] = []
    for definition in definitions:
        haystacks = [definition.title.lower(), " ".join(definition.platforms).lower()]
        if definition.family:
            haystacks.append(definition.family.lower())
        if any(term in hay for hay in haystacks for term in lowered):
            filtered.append(definition)
    return filtered


def ensure_clean_directory(directory: Path, clean: bool) -> None:
    if clean and directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)


def write_manifest(manifest_path: Path, archive: Path, files: list[dict]) -> None:
    manifest = {
        "source_archive": str(archive),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def write_ansible_vars(ansible_path: Path, files: list[dict]) -> None:
    lines = ["# Автоматически сгенерированные переменные для интеграции ФСТЭК OVAL", "fstec_oval_definitions:"]
    for item in files:
        lines.append(f"  - {item['relative_path']}")
    ansible_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def process_archive(
    archive: Path,
    output_dir: Path,
    *,
    products: list[str] | None,
    limit: int | None,
) -> list[dict]:
    extracted_files: list[dict] = []
    with ZipFile(archive) as zip_file:
        for member in zip_file.infolist():
            if member.is_dir():
                continue
            if not member.filename.lower().endswith(".xml"):
                continue
            data = zip_file.read(member)
            definitions = parse_definitions(data)
            definitions = filter_definitions(definitions, products)
            if limit is not None and limit > 0:
                definitions = definitions[:limit]
            if not definitions:
                continue
            relative_path = sanitize_relative_path(member.filename)
            destination = output_dir / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            extracted_files.append(
                {
                    "relative_path": str(relative_path).replace("\\", "/"),
                    "definition_count": len(definitions),
                    "definitions": [
                        {
                            "id": definition.identifier,
                            "title": definition.title,
                            "severity": definition.severity,
                            "family": definition.family,
                            "platforms": definition.platforms,
                        }
                        for definition in definitions
                    ],
                }
            )
    return extracted_files


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Подготовка OVAL базы ФСТЭК для OpenSCAP")
    parser.add_argument("--archive", type=Path, required=True, help="Путь к архиву scanoval.zip")
    parser.add_argument(
        "--output", type=Path, required=True, help="Каталог, в который необходимо извлечь отфильтрованный контент"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Путь к JSON-манифесту (по умолчанию output/manifest.json)",
    )
    parser.add_argument(
        "--ansible-vars",
        type=Path,
        default=None,
        help="Путь к YAML с переменными Ansible (по умолчанию output/fstec_oval.yml)",
    )
    parser.add_argument(
        "--product",
        action="append",
        dest="products",
        help="Фильтрация по названию платформы, семейству или заголовку (можно указывать несколько раз)",
    )
    parser.add_argument(
        "--definition-limit",
        type=int,
        default=None,
        help="Ограничение количества определений на файл (для отладки)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Очистить целевой каталог перед извлечением",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    archive = args.archive
    if not archive.exists():
        print(f"Архив {archive} не найден", file=sys.stderr)
        return 1

    output_dir: Path = args.output
    ensure_clean_directory(output_dir, args.clean)

    files = process_archive(
        archive,
        output_dir,
        products=args.products,
        limit=args.definition_limit,
    )

    if not files:
        print("Не удалось извлечь ни одного OVAL-определения по заданным критериям", file=sys.stderr)
        return 2

    manifest_path = args.manifest or (output_dir / "manifest.json")
    write_manifest(manifest_path, archive, files)

    ansible_path = args.ansible_vars or (output_dir / "fstec_oval.yml")
    write_ansible_vars(ansible_path, files)

    print(f"Извлечено {sum(item['definition_count'] for item in files)} определений в {output_dir}")
    print(f"Манифест: {manifest_path}")
    print(f"Ansible vars: {ansible_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
