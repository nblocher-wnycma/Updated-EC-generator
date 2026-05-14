"""Section definitions and narrative style guidance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Prompt:
    key: str
    label: str
    example: str = ""
    multiline: bool = True


def P(key: str, label: str, example: str = "", multiline: bool = True) -> Prompt:
    return Prompt(key, label, example, multiline)


GENERAL_PROMPTS = [
    P("farm_name", "Farm name", "Example: Maple Ridge Dairy", False),
    P("owner_operator", "Farm owner/operator", "Example: John Smith", False),
    P("farm_address", "Farm address", "Example: 123 County Road 4, Town, NY", False),
    P("county_state", "County and state", "Example: Wyoming County, New York", False),
    P("operation_type", "Type of operation", "Example: dairy, beef, crop, or mixed livestock/crop", False),
    P("animals", "Number and type of animals", "Example: 85 milk cows, 40 heifers, 20 calves"),
    P("housing_areas", "Main barns or housing areas", "Example: freestall barn, heifer barn, bedded pack"),
    P("manure_system", "Existing manure handling system", "Example: scrape to storage, daily spread, bedded pack stack"),
    P("land_base", "Crop fields, pasture, or both", "Example: 120 acres cropland and 20 acres pasture"),
    P("evaluation_date", "Evaluation date", "Example: May 14, 2026", False),
    P("evaluator", "Evaluator/preparer", "Example: WNY Crop Management", False),
]


SECTION_ORDER = [
    "farmstead", "manure_storage", "barnyards", "heavy_use_areas", "feed_storage", "silage_leachate",
    "roof_runoff_clean_water", "contaminated_runoff", "pasture", "cropland", "nutrient_management",
    "waste_transfer", "mortality_management", "emergency_concerns", "other_resource_concerns",
]


def section(title: str, focus: str, required: list[str], prompts: list[Prompt], runoff: bool = False, animal: bool = False) -> dict:
    return {"title": title, "focus": focus, "required": required, "runoff_required": runoff, "animal_required": animal, "prompts": prompts}


COMMON_YARD_PROMPTS = [
    P("location_size", "Size and location"), P("animals_using", "Number of animals using the area"),
    P("seasonal_use", "Time of year used"), P("surface_condition", "Surface condition"),
    P("vegetative_cover", "Vegetative cover"), P("mud", "Mud concerns"),
    P("manure_accumulation", "Manure accumulation"), P("runoff_direction", "Runoff direction"),
    P("nearby_resources", "Nearby water resource concerns"), P("connections", "Connections to barns, pastures, or manure storage"),
    P("management", "Current management practices"), P("concerns", "Resource concerns observed"),
]


SECTION_TEMPLATES = {
    "farmstead": section(
        "Farmstead",
        "animal housing, manure handling, feed storage, heavy use areas, drainage patterns, and nearby sensitive resources around the production area",
        ["description", "drainage_patterns", "sensitive_features", "observed_concerns"],
        [
            P("description", "Description of the farmstead"), P("animal_housing", "Animal housing areas"),
            P("barnyards", "Barnyards"), P("heavy_use_areas", "Heavy use areas"), P("manure_storage", "Manure storage areas"),
            P("feed_storage", "Feed storage areas"), P("drainage_patterns", "Drainage patterns"),
            P("sensitive_features", "Nearby ditches, streams, wetlands, wells, or surface waters"),
            P("clean_water_contamination", "Areas where clean water becomes contaminated"),
            P("contaminant_exit", "Areas where manure, sediment, leachate, or runoff could leave the production area"),
            P("current_management", "Current management practices"), P("observed_concerns", "Resource concerns observed during evaluation"),
        ], True, True),
    "manure_storage": section(
        "Manure Storage", "existing manure storage, stacking, capacity, leachate control, runoff control, and access for hauling or transfer",
        ["storage_type", "storage_condition", "runoff_control", "concerns"],
        [P("storage_type", "Existing storage type"), P("storage_condition", "Storage condition"), P("adequate_capacity", "Does storage appear adequate?"),
         P("daily_spread", "Is manure daily spread?"), P("temporary_piles", "Are temporary manure piles used?"),
         P("runoff_control", "Is runoff from storage controlled?"), P("engineer_review", "Should an engineer evaluate the storage?"),
         P("access", "Access or traffic concerns"), P("runoff_destination", "Where does runoff or leachate flow?"),
         P("concerns", "Concerns with seepage, overflow, access, or structure")], True, True),
    "barnyards": section("Barnyards", "livestock concentration areas, exposed soil, manure accumulation, and runoff leaving the barnyard", ["location_size", "animals_using", "surface_condition", "runoff_direction", "concerns"], COMMON_YARD_PROMPTS, True, True),
    "heavy_use_areas": section("Heavy Use Areas", "areas receiving repeated animal, feeding, equipment, or manure-handling traffic", ["location_size", "animals_using", "surface_condition", "runoff_direction", "concerns"], COMMON_YARD_PROMPTS, True, True),
    "feed_storage": section(
        "Feed Storage", "stored feed, loading areas, waste feed, leachate, and runoff from feed handling surfaces",
        ["storage_type", "runoff_destination", "concerns"],
        [P("storage_type", "Type of feed storage"), P("size", "Bunk size or pad size if known"), P("leachate", "Is leachate present?"),
         P("runoff_collection", "Is runoff collected or controlled?"), P("runoff_destination", "Does runoff reach a ditch, field, wetland, or other water resource?"),
         P("management", "Current management practices"), P("concerns", "Resource concerns observed")], True, False),
    "silage_leachate": section(
        "Silage Leachate", "silage storage, leachate generation, collection, treatment, and discharge pathways",
        ["storage_area", "leachate_evidence", "destination", "concerns"],
        [P("storage_area", "Silage storage area"), P("silage_type", "Type of silage or feed stored"), P("leachate_evidence", "Evidence of leachate or staining"),
         P("collection", "Is leachate collected or treated?"), P("destination", "Where does leachate or runoff flow?"),
         P("seasonality", "When is the concern most likely?"), P("concerns", "Resource concerns observed")], True, False),
    "roof_runoff_clean_water": section(
        "Roof Runoff / Clean Water", "roof runoff, gutters, clean-water separation, underground outlets, and discharge locations",
        ["roof_areas", "gutters", "separation", "discharge"],
        [P("roof_areas", "Roof areas contributing runoff"), P("gutters", "Do gutters exist and are they functional?"),
         P("separation", "Is clean water separated from contaminated areas?"), P("underground_outlets", "Are underground outlets present or needed?"),
         P("discharge", "Where does clean water discharge?"), P("concerns", "Resource concerns observed")], True, False),
    "contaminated_runoff": section(
        "Contaminated Runoff", "runoff that contacts manure, feed, bedding, barnyards, heavy use areas, or other pollutant sources",
        ["source_areas", "flow_path", "outlet", "concerns"],
        [P("source_areas", "Source areas creating contaminated runoff"), P("flow_path", "Flow path through the farmstead"),
         P("outlet", "Where does contaminated runoff leave or collect?"), P("controls", "Existing controls"),
         P("water_resources", "Nearby water resources"), P("concerns", "Resource concerns observed")], True, True),
    "pasture": section(
        "Pasture", "grazed acres, vegetative condition, water sources, concentrated traffic, stream access, and sacrifice areas",
        ["acreage", "animals", "condition", "water_sources", "concerns"],
        [P("acreage", "Pasture acreage"), P("animals", "Animal numbers using pasture"), P("season", "Grazing season"),
         P("condition", "Pasture condition"), P("water_sources", "Water sources"), P("shade", "Shade"),
         P("concentrated_flow", "Concentrated flow areas"), P("bare_soil", "Bare soil"), P("sacrifice_lot", "Sacrifice lot concerns"),
         P("stream_access", "Stream access if any"), P("management", "Current grazing management"), P("concerns", "Resource concerns observed")], False, True),
    "cropland": section(
        "Cropland", "cropland acres, crop rotation, manure application, sensitive areas, setbacks, and erosion or nutrient transport risk",
        ["acres", "field_conditions", "crop_rotation", "manure_method", "concerns"],
        [P("acres", "Total cropland acres"), P("field_conditions", "Field conditions"), P("crop_rotation", "Crop rotation"),
         P("manure_method", "Manure application method"), P("sensitive_areas", "Sensitive areas"), P("setbacks", "Setbacks"),
         P("soil_tests", "Soil test availability"), P("manure_analysis", "Manure analysis availability"),
         P("concerns", "Concerns with erosion, runoff, or nutrient transport")]),
    "nutrient_management": section(
        "Nutrient Management", "nutrient planning records, soil tests, manure analysis, application timing, rates, setbacks, and sensitive areas",
        ["plan_status", "soil_tests", "manure_analysis", "application_timing", "concerns"],
        [P("plan_status", "Current nutrient management planning status"), P("manure_rates", "Manure application rates or basis"),
         P("soil_tests", "Soil test availability"), P("manure_analysis", "Manure analysis availability"),
         P("application_timing", "Application timing"), P("setbacks", "Setbacks and sensitive areas"), P("records", "Application records"),
         P("concerns", "Resource concerns observed")]),
    "waste_transfer": section(
        "Waste Transfer", "movement of manure, leachate, bedding, or wastewater between barns, storage, fields, and treatment areas",
        ["transfer_method", "routes", "surfaces", "spillage", "concerns"],
        [P("transfer_method", "Transfer method"), P("routes", "Transfer routes"), P("surfaces", "Surface condition along transfer route"),
         P("equipment", "Equipment used"), P("spillage", "Spillage or tracking concerns"), P("runoff_destination", "Where could spilled material or runoff flow?"),
         P("concerns", "Resource concerns observed")], True, True),
    "mortality_management": section(
        "Mortality Management", "mortality collection, temporary holding, composting, disposal, runoff, scavenger access, and biosecurity",
        ["method", "location", "runoff", "concerns"],
        [P("method", "Existing mortality handling method"), P("location", "Location"), P("temporary_storage", "Temporary storage"),
         P("composting", "Composting or disposal details"), P("runoff", "Runoff or leachate control"),
         P("scavenger_access", "Scavenger or biosecurity concerns"), P("concerns", "Resource concerns observed")], True, True),
    "emergency_concerns": section(
        "Emergency Concerns", "spill response, flooding, storage failure, well or water-resource protection, emergency access, and contingency planning",
        ["concerns", "emergency_plan"],
        [P("spills", "Spill or release concerns"), P("flooding", "Flooding or storm vulnerability"), P("wells", "Wells or sensitive water resources"),
         P("storage_failure", "Storage failure risks"), P("access", "Emergency access"), P("emergency_plan", "Existing emergency plan or contact information"),
         P("concerns", "Resource concerns observed")]),
    "other_resource_concerns": section(
        "Other Resource Concerns", "resource concerns identified during evaluation that are not covered by another section",
        ["description", "location", "resource_concern"],
        [P("description", "Description of the concern"), P("location", "Location"), P("resource_concern", "Resource concern"),
         P("runoff_destination", "Runoff destination if applicable"), P("management", "Current management practices"),
         P("needed_followup", "Needed follow-up or documentation")]),
}


STYLE_GUIDANCE = {
    "voice": "professional, conservation-planning focused, specific, and field-observation based",
    "opening": "During the evaluation, it was observed that...",
    "resource_concern": "Explain how animal use, manure, sediment, nutrients, leachate, runoff, and sensitive resources are connected.",
    "missing_information": "Do not guess. State that the detail was not documented and should be confirmed during final review.",
}
