"""File and folder management for Existing Conditions outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .input_prompts import get_section_title


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "outputs" / "Existing_Conditions_Output"


def safe_name(value: str, fallback: str = "Unnamed") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "", str(value or "")).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or fallback


def farm_folder(general: dict[str, str], output_root: Path | None = None) -> Path:
    root = output_root or DEFAULT_OUTPUT_ROOT
    return root / safe_name(general.get("farm_name", ""), "Unnamed_Farm")


def section_folder(general: dict[str, str], section_key: str, output_root: Path | None = None) -> Path:
    folder = farm_folder(general, output_root) / safe_name(get_section_title(section_key), section_key)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def final_folder(general: dict[str, str], output_root: Path | None = None) -> Path:
    folder = farm_folder(general, output_root) / "Final_Narratives"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def section_docx_path(general: dict[str, str], section_key: str, output_root: Path | None = None) -> Path:
    farm = safe_name(general.get("farm_name", ""), "Unnamed_Farm")
    section = safe_name(get_section_title(section_key), section_key)
    return section_folder(general, section_key, output_root) / f"{farm}_{section}_Existing_Conditions.docx"


def combined_docx_path(general: dict[str, str], output_root: Path | None = None) -> Path:
    farm = safe_name(general.get("farm_name", ""), "Unnamed_Farm")
    return final_folder(general, output_root) / f"{farm}_Existing_Conditions_Narratives.docx"


def save_project(path: str | Path, data: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_project(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
