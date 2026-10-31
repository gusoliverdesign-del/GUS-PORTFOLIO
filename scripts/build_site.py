#!/usr/bin/env python3
"""Build the public JSON feed and derived Media list from Pages CMS entries."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def read_json(path: Path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def asset_path(value) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lstrip("/")


def safe_filename(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9-]+", "-", value.lower()).strip("-")
    return value or "item"


def main() -> None:
    categories_dir = DATA / "categories"
    works_dir = DATA / "work"
    media_index_dir = DATA / "media-index"
    categories = {}

    for path in sorted(categories_dir.glob("*.json")):
        category = read_json(path)
        if category.get("status") != "Live":
            continue
        label = category.get("title", "").strip()
        if label:
            categories[f"data/categories/{path.name}"] = label
            categories[path.stem] = label
            categories[label] = label

    projects = []
    media_records = {}
    for path in sorted(works_dir.glob("*.json")):
        work = read_json(path)
        if work.get("status") != "Live":
            continue

        slug = str(work.get("slug") or path.stem).strip()
        category_names = []
        for reference in work.get("categories", []):
            name = categories.get(str(reference))
            if name is None:
                name = categories.get(Path(str(reference)).stem)
            if name and name not in category_names:
                category_names.append(name)

        gallery = [asset_path(item) for item in work.get("gallery", [])]
        gallery = [item for item in gallery if item]
        project = {
            "id": slug,
            "title": work.get("title", ""),
            "status": "Live",
            "year": work.get("year", ""),
            "cats": category_names,
            "image": asset_path(work.get("cover")),
            "logo": asset_path(work.get("logo")),
            "heroImage": asset_path(work.get("hero")) or asset_path(work.get("cover")),
            "desc": work.get("description", ""),
            "info": work.get("info", ""),
            "client": work.get("client", ""),
            "credits": work.get("credits", ""),
            "gallery": gallery,
        }
        projects.append(project)

        assets = []
        if project["image"]:
            assets.append(("Capa da home", project["image"]))
        if work.get("hero") and asset_path(work.get("hero")):
            assets.append(("Capa do topo", asset_path(work["hero"])))
        assets.extend((f"Imagem {index:02d}", image) for index, image in enumerate(gallery, start=1))
        for index, (label, image) in enumerate(assets, start=1):
            media_records[f"{safe_filename(slug)}-{index:03d}.json"] = {
                "title": f"{work.get('title', slug)} — {label}",
                "project": work.get("title", slug),
                "category": " · ".join(category_names),
                "work": slug,
                "asset": image,
            }

    write_json(DATA / "projects.json", projects)
    media_index_dir.mkdir(parents=True, exist_ok=True)
    for old_record in media_index_dir.glob("*.json"):
        old_record.unlink()
    for filename, record in media_records.items():
        write_json(media_index_dir / filename, record)

    output = ROOT / "site-dist"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    shutil.copy2(ROOT / "index.html", output / "index.html")
    shutil.copytree(DATA, output / "data", ignore=shutil.ignore_patterns(".gitkeep"))
    cname = ROOT / "CNAME"
    if cname.exists():
        shutil.copy2(cname, output / "CNAME")
    media_dir = ROOT / "media"
    if media_dir.exists():
        shutil.copytree(media_dir, output / "media", ignore=shutil.ignore_patterns(".gitkeep"))


if __name__ == "__main__":
    main()
