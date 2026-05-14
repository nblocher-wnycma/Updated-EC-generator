"""Generate CNMP Existing Conditions narratives from entered farm facts."""

from __future__ import annotations

import re

from .input_prompts import get_section_template, get_section_title
from .quality_control import is_known


UNIT_REPLACEMENTS = [
    (r"\bsq\.?\s*ft\.?\b|\bsqf\b|\bsf\b", "square feet"),
    (r"\bln\.?\s*ft\.?\b|\blf\b|\bl\.?\s*f\.?\b", "linear feet"),
    (r"\bac\.?\b", "acres"),
]
TERM_REPLACEMENTS = [
    (r"\bstorm\s+water\b", "stormwater"),
    (r"\brun\s+off\b", "runoff"),
    (r"\bfarm\s+stead\b", "farmstead"),
    (r"\bbarn\s+yard\b", "barnyard"),
]


def generate_section_narrative(
    general: dict[str, str],
    section_key: str,
    section_data: dict[str, str],
) -> str:
    template = get_section_template(section_key)
    title = get_section_title(section_key)
    farm_name = _value(general, "farm_name", "the farm")
    operation = _value(general, "operation_type", "the agricultural operation")
    animals = _first_known(
        section_data.get("animals"),
        general.get("animals"),
        fallback="the documented livestock inventory",
    )
    location_context = _location_context(general)

    paragraphs = [
        _opening_paragraph(farm_name, title, template["focus"], operation, location_context),
        _observation_paragraph(farm_name, title, section_key, section_data, animals),
        _runoff_and_resource_paragraph(farm_name, title, section_key, section_data),
        _management_paragraph(farm_name, title, section_data),
        _documentation_paragraph(title, section_data, template.get("required", [])),
    ]
    return proofread_text("\n\n".join(p for p in paragraphs if p.strip()))


def generate_multiple_narratives(
    general: dict[str, str],
    sections: dict[str, dict[str, str]],
    selected_sections: list[str],
) -> dict[str, str]:
    return {
        section_key: generate_section_narrative(general, section_key, sections.get(section_key, {}))
        for section_key in selected_sections
    }


def proofread_text(text: str) -> str:
    text = str(text or "")
    for pattern, replacement in TERM_REPLACEMENTS + UNIT_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\b([A-Za-z][A-Za-z'-]*)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([.!?]){2,}", r"\1", text)
    text = re.sub(r"(?<!\d)\.(?=[A-Za-z])", ". ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = _remove_duplicate_sentences(text)
    text = _capitalize_sentences(text)
    return text.strip()


def _opening_paragraph(
    farm_name: str,
    title: str,
    focus: str,
    operation: str,
    location_context: str,
) -> str:
    section_label = _section_label(title)
    return (
        f"During the evaluation, conditions for the {section_label} section at {farm_name} were reviewed in relation to "
        f"{focus}. {farm_name} is described as {operation}{location_context}. The purpose of this section is to "
        "document the existing condition, identify the resource concern where one is present, and connect the "
        "observed farmstead or field condition to the potential movement of manure, sediment, nutrients, leachate, "
        "or contaminated runoff."
    )


def _observation_paragraph(
    farm_name: str,
    title: str,
    section_key: str,
    section_data: dict[str, str],
    animals: str,
) -> str:
    facts = _known_field_sentences(section_key, section_data, category="observation")
    if facts:
        return (
            f"The entered field notes document the following existing conditions. {facts} These conditions were considered in relation to "
            f"{animals} and the normal operation of {farm_name}."
        )
    return (
        f"Detailed field notes for the {title.lower()} section were not entered. The section should remain in draft "
        "form until the evaluator confirms the area location, animal use, surface condition, and any visible signs "
        "of manure, sediment, leachate, or runoff movement."
    )


def _runoff_and_resource_paragraph(
    farm_name: str,
    title: str,
    section_key: str,
    section_data: dict[str, str],
) -> str:
    runoff = _known_field_sentences(section_key, section_data, category="runoff")
    concerns = _concern_text(section_data)
    if runoff and concerns:
        return (
            f"Runoff and drainage conditions were described as follows. {runoff} Based on the entered information, "
            f"the resource concern is that {concerns}. This creates a potential pathway for contaminated runoff or "
            "transported material to move away from the production area during rainfall, snowmelt, thaw conditions, "
            "or routine farm traffic."
        )
    if runoff:
        return (
            f"Runoff and drainage conditions were described as follows. {runoff} The evaluator should add a specific "
            "resource concern statement before final export so the narrative explains whether manure, sediment, "
            "nutrients, leachate, or other agricultural waste could leave the evaluated area."
        )
    if concerns:
        return (
            f"The resource concern entered for this section is that {concerns}. The final evaluation should also "
            "document where runoff from this area flows and whether a ditch, stream, wetland, well, field, or other "
            "sensitive feature could be affected."
        )
    return (
        f"No clear runoff destination or resource concern was entered for the {title.lower()} section. The program "
        "has not assumed a drainage pathway. The evaluator should confirm whether water leaves this area, where it "
        "flows, and whether it contacts manure, feed, bedding, sediment, leachate, or other agricultural waste."
    )


def _management_paragraph(farm_name: str, title: str, section_data: dict[str, str]) -> str:
    management_keys = [
        "current_management",
        "management",
        "daily_spread",
        "temporary_piles",
        "adequate_capacity",
        "engineer_review",
        "runoff_collection",
        "collection",
        "separation",
        "underground_outlets",
        "setbacks",
        "records",
        "emergency_plan",
        "needed_followup",
    ]
    items = []
    for key in management_keys:
        value = section_data.get(key)
        if is_known(value):
            items.append(f"{_labelize(key)}: {_clean_value(value)}")
    if not items:
        return (
            f"Current management for the {title.lower()} section was not fully documented. Before the narrative is "
            f"finalized for {farm_name}, the evaluator should confirm routine operation, maintenance, and any "
            "seasonal management that affects the resource concern."
        )
    return (
        "Current management information entered for this section includes " + "; ".join(items) + ". "
        "These practices should be verified against field observations and adjusted if the final CNMP identifies "
        "additional treatment needs."
    )


def _documentation_paragraph(title: str, section_data: dict[str, str], required: list[str]) -> str:
    missing = [_labelize(key) for key in required if not is_known(section_data.get(key))]
    if not missing:
        return (
            f"The {_section_label(title)} narrative is based on the entered field information and should be reviewed by the "
            "planner before final delivery to confirm that the wording matches the completed evaluation document."
        )
    return (
        "The following information was not documented or was marked unknown: "
        + ", ".join(missing)
        + ". These items should be confirmed before this section is considered final."
    )


def _section_label(title: str) -> str:
    label = title.lower()
    replacements = {
        "barnyards": "barnyard",
        "heavy use areas": "heavy use area",
        "emergency concerns": "emergency concerns",
        "other resource concerns": "other resource concern",
    }
    return replacements.get(label, label)


OBSERVATION_KEYS = {
    "description", "animal_housing", "barnyards", "heavy_use_areas", "manure_storage", "feed_storage",
    "storage_type", "storage_condition", "location_size", "animals_using", "seasonal_use", "surface_condition",
    "vegetative_cover", "mud", "manure_accumulation", "storage_area", "silage_type", "leachate_evidence",
    "roof_areas", "gutters", "source_areas", "acreage", "animals", "season", "condition", "water_sources",
    "shade", "bare_soil", "sacrifice_lot", "stream_access", "acres", "field_conditions", "crop_rotation",
    "manure_method", "plan_status", "manure_rates", "soil_tests", "manure_analysis", "application_timing",
    "transfer_method", "routes", "surfaces", "equipment", "spillage", "method", "location", "temporary_storage",
    "composting", "scavenger_access", "spills", "flooding", "wells", "storage_failure", "access", "resource_concern",
}

RUNOFF_KEYS = {
    "drainage_patterns", "sensitive_features", "clean_water_contamination", "contaminant_exit", "runoff_control",
    "runoff_destination", "runoff_direction", "nearby_resources", "connections", "leachate", "runoff_collection",
    "destination", "discharge", "flow_path", "outlet", "controls", "water_resources", "concentrated_flow",
    "sensitive_areas", "runoff",
}


def _known_field_sentences(section_key: str, section_data: dict[str, str], category: str) -> str:
    allowed = OBSERVATION_KEYS if category == "observation" else RUNOFF_KEYS
    parts = []
    prompts = get_section_template(section_key).get("prompts", [])
    for prompt in prompts:
        if prompt.key not in allowed:
            continue
        value = section_data.get(prompt.key)
        if is_known(value):
            parts.append(_field_phrase(prompt.key, prompt.label, value))
    return " ".join(part.rstrip(".") + "." for part in parts)


FIELD_PHRASES = {
    "description": "field notes state that {value}",
    "animal_housing": "animal housing notes state that {value}",
    "barnyards": "barnyard notes state that {value}",
    "heavy_use_areas": "heavy use area notes state that {value}",
    "manure_storage": "manure storage notes state that {value}",
    "feed_storage": "feed storage notes state that {value}",
    "storage_type": "the existing storage type is {value}",
    "storage_condition": "the storage condition is {value}",
    "location_size": "the evaluated area is {value}",
    "animals_using": "animal use notes state that {value}",
    "seasonal_use": "the area is used {value}",
    "surface_condition": "the surface condition is {value}",
    "vegetative_cover": "vegetative cover is {value}",
    "mud": "mud concerns note that {value}",
    "manure_accumulation": "manure accumulation notes state that {value}",
    "roof_areas": "roof runoff notes state that {value}",
    "gutters": "gutter condition is described as {value}",
    "source_areas": "source areas include {value}",
    "acreage": "pasture acreage is {value}",
    "animals": "pasture animal use includes {value}",
    "season": "the grazing season is {value}",
    "condition": "pasture condition is {value}",
    "water_sources": "livestock water is provided by {value}",
    "shade": "shade is described as {value}",
    "bare_soil": "bare soil conditions include {value}",
    "sacrifice_lot": "sacrifice lot conditions include {value}",
    "stream_access": "stream access was documented as {value}",
    "acres": "cropland acreage is {value}",
    "field_conditions": "field conditions are described as {value}",
    "crop_rotation": "crop rotation is {value}",
    "manure_method": "manure application is handled by {value}",
    "plan_status": "nutrient management planning status is {value}",
    "manure_rates": "manure rates or rate basis are described as {value}",
    "soil_tests": "soil test information is {value}",
    "manure_analysis": "manure analysis information is {value}",
    "application_timing": "application timing is {value}",
    "transfer_method": "waste transfer occurs by {value}",
    "routes": "transfer routes include {value}",
    "surfaces": "transfer-route surfaces are described as {value}",
    "equipment": "equipment used for transfer includes {value}",
    "spillage": "spillage or tracking concerns include {value}",
    "method": "mortality handling is described as {value}",
    "location": "the location is {value}",
    "temporary_storage": "temporary storage is described as {value}",
    "composting": "composting or disposal details include {value}",
    "scavenger_access": "scavenger or biosecurity concerns include {value}",
    "spills": "spill or release concerns include {value}",
    "flooding": "flooding or storm vulnerability is {value}",
    "wells": "wells or sensitive water resources include {value}",
    "storage_failure": "storage failure risks include {value}",
    "access": "access is described as {value}",
    "resource_concern": "the resource concern is {value}",
    "drainage_patterns": "drainage patterns were described as {value}",
    "sensitive_features": "nearby sensitive features include {value}",
    "clean_water_contamination": "clean-water contamination is described as {value}",
    "contaminant_exit": "potential contaminant movement is described as {value}",
    "runoff_control": "runoff control is described as {value}",
    "runoff_destination": "runoff or leachate flows toward {value}",
    "runoff_direction": "runoff notes state that {value}",
    "nearby_resources": "nearby water resource concerns include {value}",
    "connections": "connections are described as {value}",
    "leachate": "leachate conditions are described as {value}",
    "runoff_collection": "runoff collection is described as {value}",
    "destination": "leachate or runoff flows toward {value}",
    "discharge": "clean-water discharge is described as {value}",
    "flow_path": "the flow path is {value}",
    "outlet": "contaminated runoff leaves or collects at {value}",
    "controls": "existing controls include {value}",
    "water_resources": "nearby water resources include {value}",
    "concentrated_flow": "concentrated flow areas include {value}",
    "sensitive_areas": "sensitive areas include {value}",
    "runoff": "runoff or leachate control is described as {value}",
}


def _field_phrase(key: str, label: str, value: object) -> str:
    template = FIELD_PHRASES.get(key, f"{label.lower()} is described as {{value}}")
    phrase = template.format(value=_clean_value(value))
    phrase = re.sub(r"\b(runoff flows)\s+\1\b", r"\1", phrase, flags=re.IGNORECASE)
    phrase = re.sub(r"\b(gutters are)\s+gutters are\b", r"\1", phrase, flags=re.IGNORECASE)
    return phrase


def _concern_text(section_data: dict[str, str]) -> str:
    for key in ["observed_concerns", "concerns", "resource_concern"]:
        if is_known(section_data.get(key)):
            return _clean_value(section_data[key]).rstrip(".")
    return ""


def _location_context(general: dict[str, str]) -> str:
    parts = []
    if is_known(general.get("farm_address")):
        parts.append(_clean_value(general["farm_address"]))
    if is_known(general.get("county_state")):
        parts.append(_clean_value(general["county_state"]))
    if not parts:
        return ""
    return " located at " + ", ".join(parts)


def _first_known(*values: str, fallback: str) -> str:
    for value in values:
        if is_known(value):
            return _clean_value(value)
    return fallback


def _value(data: dict[str, str], key: str, fallback: str) -> str:
    value = data.get(key)
    return _clean_value(value) if is_known(value) else fallback


def _clean_value(value: object) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    if re.match(r"^(main|primary|south|north|east|west|old|new)\b", text, flags=re.IGNORECASE):
        text = "the " + text
    return text.rstrip(".")


def _labelize(key: str) -> str:
    return key.replace("_", " ")


def _remove_duplicate_sentences(text: str) -> str:
    paragraphs = []
    for paragraph in text.split("\n"):
        paragraph = re.sub(r"(\d)\.(\d)", r"\1<DECIMAL>\2", paragraph)
        seen: set[str] = set()
        kept: list[str] = []
        for sentence in re.findall(r"[^.!?]+[.!?]|[^.!?]+$", paragraph):
            sentence = sentence.replace("<DECIMAL>", ".")
            key = re.sub(r"[^a-z0-9 ]+", "", sentence.lower()).strip()
            if len(key) > 35 and key in seen:
                continue
            seen.add(key)
            kept.append(sentence.strip())
        paragraphs.append(" ".join(kept).strip())
    return "\n".join(p for p in paragraphs if p)


def _capitalize_sentences(text: str) -> str:
    chars = []
    start = True
    for char in text:
        if start and char.isalpha():
            chars.append(char.upper())
            start = False
        else:
            chars.append(char)
            if char.isalnum():
                start = False
        if char in ".!?\n":
            start = True
    return "".join(chars)
