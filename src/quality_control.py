"""Quality-control checks for generated Existing Conditions narratives."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .input_prompts import get_section_template, get_section_title


UNKNOWN_VALUES = {"", "unknown", "unk", "n/a", "na", "none", "not sure", "not documented"}
PLACEHOLDER_RE = re.compile(r"\[[^\]]+\]|\bTBD\b|\bTODO\b|<[^>]+>", re.IGNORECASE)
FORBIDDEN_EXAMPLE_NAMES = [
    "A&M Hideaway",
    "Big Z Beef",
    "Ketch Farm",
    "Yousett Farm",
]


@dataclass
class QualityIssue:
    severity: str
    message: str


def is_known(value: object) -> bool:
    text = str(value or "").strip().lower()
    return text not in UNKNOWN_VALUES


def run_quality_checks(
    general: dict[str, str],
    section_key: str,
    section_data: dict[str, str],
    narrative: str,
) -> list[QualityIssue]:
    template = get_section_template(section_key)
    issues: list[QualityIssue] = []
    farm_name = str(general.get("farm_name", "")).strip()

    for field, label in [
        ("farm_name", "Farm name"),
        ("owner_operator", "Farm owner/operator"),
        ("county_state", "County and state"),
        ("operation_type", "Operation type"),
    ]:
        if not is_known(general.get(field)):
            issues.append(QualityIssue("error", f"{label} is missing."))

    if farm_name and farm_name not in narrative:
        issues.append(QualityIssue("error", "Generated narrative does not include the current farm name."))

    for old_name in FORBIDDEN_EXAMPLE_NAMES:
        if old_name.lower() in narrative.lower() and old_name.lower() != farm_name.lower():
            issues.append(QualityIssue("error", f"Possible old/example farm name found: {old_name}."))

    if PLACEHOLDER_RE.search(narrative):
        issues.append(QualityIssue("error", "Placeholder text remains in the narrative."))

    for required_key in template.get("required", []):
        if not is_known(section_data.get(required_key)):
            label = _prompt_label(section_key, required_key)
            issues.append(QualityIssue("warning", f"{get_section_title(section_key)} is missing: {label}."))

    if template.get("animal_required") and not (
        is_known(section_data.get("animals"))
        or is_known(section_data.get("animals_using"))
        or is_known(general.get("animals"))
    ):
        issues.append(QualityIssue("warning", "Animal numbers/types are missing for this livestock-related section."))

    if template.get("runoff_required") and not _has_runoff_destination(section_data):
        issues.append(QualityIssue("warning", "Runoff destination or discharge location is missing."))

    if not _has_concern_explanation(section_data, narrative):
        issues.append(QualityIssue("warning", "Resource concern explanation may be missing or too thin."))

    duplicate_count = _count_duplicate_sentences(narrative)
    if duplicate_count:
        issues.append(QualityIssue("warning", f"Repeated or nearly repeated sentences found: {duplicate_count}."))

    if _looks_generic(section_data, narrative):
        issues.append(QualityIssue("warning", "Narrative may be too generic; add more field-specific facts before export."))

    contradiction = _find_basic_contradiction(section_data, narrative)
    if contradiction:
        issues.append(QualityIssue("warning", contradiction))

    return issues


def format_issues(issues: list[QualityIssue]) -> str:
    if not issues:
        return "No quality-control warnings."
    return "\n".join(f"{issue.severity.upper()}: {issue.message}" for issue in issues)


def has_errors(issues: list[QualityIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)


def _prompt_label(section_key: str, prompt_key: str) -> str:
    for prompt in get_section_template(section_key).get("prompts", []):
        if prompt.key == prompt_key:
            return prompt.label
    return prompt_key.replace("_", " ")


def _has_runoff_destination(section_data: dict[str, str]) -> bool:
    keys = [
        "runoff_direction",
        "runoff_destination",
        "destination",
        "discharge",
        "outlet",
        "flow_path",
        "drainage_patterns",
        "contaminant_exit",
    ]
    return any(is_known(section_data.get(key)) for key in keys)


def _has_concern_explanation(section_data: dict[str, str], narrative: str) -> bool:
    concern_keys = ["concerns", "observed_concerns", "resource_concern"]
    if any(is_known(section_data.get(key)) for key in concern_keys):
        return True
    concern_terms = ["resource concern", "potential to transport", "water quality", "sediment", "nutrient"]
    return sum(term in narrative.lower() for term in concern_terms) >= 2


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.findall(r"[^.!?]+[.!?]|[^.!?]+$", text) if s.strip()]


def _sentence_key(sentence: str) -> str:
    key = re.sub(r"[^a-z0-9 ]+", "", sentence.lower())
    return re.sub(r"\s+", " ", key).strip()


def _count_duplicate_sentences(text: str) -> int:
    seen: set[str] = set()
    duplicates = 0
    for sentence in _split_sentences(text):
        key = _sentence_key(sentence)
        if len(key) < 35:
            continue
        if key in seen:
            duplicates += 1
        seen.add(key)
    return duplicates


def _looks_generic(section_data: dict[str, str], narrative: str) -> bool:
    if len(narrative.split()) < 120:
        return True
    known_values = [v for v in section_data.values() if is_known(v) and len(str(v).split()) >= 3]
    used = 0
    lower = narrative.lower()
    for value in known_values:
        words = [w for w in re.findall(r"[a-z0-9]+", str(value).lower()) if len(w) > 4]
        if words and sum(word in lower for word in words[:8]) >= min(2, len(words)):
            used += 1
    return used < min(3, len(known_values))


def _find_basic_contradiction(section_data: dict[str, str], narrative: str) -> str:
    text = " ".join(section_data.values()).lower() + " " + narrative.lower()
    if "no leachate" in text and ("leachate is present" in text or "leachate was observed" in text):
        return "Possible contradiction: narrative mentions both no leachate and observed leachate."
    if "no manure storage" in text and ("manure storage" in text and "storage" in text and "overflow" in text):
        return "Possible contradiction: manure storage is described as absent and also as having storage concerns."
    if "no stream access" in text and "stream access" in text and "cattle" in text and "uncontrolled" in text:
        return "Possible contradiction: stream access may be both denied and described as uncontrolled."
    return ""
