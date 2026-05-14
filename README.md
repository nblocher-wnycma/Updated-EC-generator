# CNMP Existing Conditions Narrative Generator

This project generates editable Existing Conditions narratives for CNMP evaluations from user-entered farm information. It is intentionally separate from older CNMP/Farmstead generator projects so it can be developed independently.

The generator uses completed Existing Conditions evaluations as a style and structure guide, but it does not copy farm-specific facts from example documents. New narratives are built from the information entered for the current farm.

## Features

- Tkinter desktop workflow
- Section-by-section prompts so the user is not asked for everything at once
- Flexible section selection; not every farm needs every section
- Editable preview before export
- One-section or multi-section generation
- Word export using `python-docx`
- Farm-specific output folders
- Quality-control warnings for missing fields, placeholders, repeated sentences, missing farm name, missing runoff destination, missing animal numbers, and generic narratives
- Template folders for future completed example narratives and prompt templates

## Supported Sections

- Farmstead
- Manure Storage
- Barnyards
- Heavy Use Areas
- Feed Storage
- Silage Leachate
- Roof Runoff / Clean Water
- Contaminated Runoff
- Pasture
- Cropland
- Nutrient Management
- Waste Transfer
- Mortality Management
- Emergency Concerns
- Other Resource Concerns

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run The App

```powershell
python -m src.app
```

Or double-click:

```text
Run_Existing_Conditions_Generator.bat
```

## Generate From The Sample Input

```powershell
python -m src.app --sample
```

The sample output is written under:

```text
outputs/Existing_Conditions_Output/
```

## Output Structure

```text
outputs/
  Existing_Conditions_Output/
    Farm_Name/
      Farmstead/
      Manure_Storage/
      Heavy_Use_Areas/
      Feed_Storage/
      Final_Narratives/
```

## Adding Completed Example Narratives

Place future completed, reviewed Existing Conditions examples in:

```text
templates/existing_conditions_examples/
```

Do not paste old farm names or site-specific facts directly into templates used for new output. Examples should be used to improve structure, tone, section coverage, and professional wording.

## Important Quality Rule

The program does not guess important farm-specific facts. If the user does not know an answer, enter `Unknown`. The narrative will continue with review-needed wording, and quality control will warn that the detail should be confirmed.
