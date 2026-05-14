"""Prompt helpers for the Tkinter app and future CLI workflows."""

from __future__ import annotations

from .section_templates import GENERAL_PROMPTS, SECTION_ORDER, SECTION_TEMPLATES


def get_general_prompts():
    return GENERAL_PROMPTS


def get_section_keys() -> list[str]:
    return list(SECTION_ORDER)


def get_section_title(section_key: str) -> str:
    return SECTION_TEMPLATES[section_key]["title"]


def get_section_prompts(section_key: str):
    return SECTION_TEMPLATES[section_key]["prompts"]


def get_section_template(section_key: str) -> dict:
    return SECTION_TEMPLATES[section_key]
