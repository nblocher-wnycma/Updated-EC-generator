"""Tkinter app and command-line entry point for the EC narrative generator."""

from __future__ import annotations

import argparse
import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .export_to_word import export_combined_docx, export_section_docx
from .file_manager import load_project, save_project
from .input_prompts import get_general_prompts, get_section_keys, get_section_prompts, get_section_title
from .narrative_generator import generate_multiple_narratives, generate_section_narrative
from .quality_control import format_issues, has_errors, run_quality_checks


class ExistingConditionsApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("CNMP Existing Conditions Narrative Generator")
        self.root.geometry("1180x820")
        self.general_widgets: dict[str, tk.Entry | ScrolledText] = {}
        self.section_widgets: dict[str, dict[str, ScrolledText]] = {}
        self.section_enabled: dict[str, tk.BooleanVar] = {}
        self.current_section_key: str | None = None
        self.current_issues = []
        self._build()

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)
        top = ttk.Frame(outer)
        top.pack(fill="both", expand=True)
        self.notebook = ttk.Notebook(top)
        self.notebook.pack(side="left", fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", lambda _event: self._on_tab_change())
        self._build_general_tab()
        for section_key in get_section_keys():
            self._build_section_tab(section_key)
        preview_frame = ttk.Frame(top, padding=(10, 0, 0, 0))
        preview_frame.pack(side="right", fill="both", expand=True)
        ttk.Label(preview_frame, text="Editable Preview").pack(anchor="w")
        self.preview_text = ScrolledText(preview_frame, wrap="word", height=26)
        self.preview_text.pack(fill="both", expand=True)
        ttk.Label(preview_frame, text="Quality-Control Warnings").pack(anchor="w", pady=(8, 0))
        self.warning_text = ScrolledText(preview_frame, wrap="word", height=9)
        self.warning_text.pack(fill="both", expand=False)
        self._build_buttons(outer)

    def _build_general_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="General Farm Info")
        for prompt in get_general_prompts():
            ttk.Label(tab, text=prompt.label).pack(anchor="w", pady=(5, 1))
            if prompt.example:
                ttk.Label(tab, text=prompt.example).pack(anchor="w")
            widget = ScrolledText(tab, height=3, wrap="word") if prompt.multiline else ttk.Entry(tab)
            widget.pack(fill="x", pady=(0, 3))
            self.general_widgets[prompt.key] = widget

    def _build_section_tab(self, section_key: str) -> None:
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text=get_section_title(section_key))
        enabled = tk.BooleanVar(value=False)
        self.section_enabled[section_key] = enabled
        ttk.Checkbutton(tab, text="Include this section in generated output", variable=enabled).pack(anchor="w")
        self.section_widgets[section_key] = {}
        for prompt in get_section_prompts(section_key):
            ttk.Label(tab, text=prompt.label).pack(anchor="w", pady=(5, 1))
            widget = ScrolledText(tab, height=3 if prompt.multiline else 1, wrap="word")
            widget.pack(fill="x", pady=(0, 3))
            self.section_widgets[section_key][prompt.key] = widget

    def _build_buttons(self, parent: ttk.Frame) -> None:
        buttons = ttk.Frame(parent, padding=(0, 8, 0, 0))
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Load Sample", command=self._load_sample).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Load Project", command=self._load_project).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Save Project", command=self._save_project).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Generate Current Section", command=self._generate_current).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Generate All Included", command=self._generate_all).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Export Current Preview", command=self._export_current).pack(side="right", padx=(6, 0))
        ttk.Button(buttons, text="Export All Included", command=self._export_all).pack(side="right", padx=(6, 0))

    def _on_tab_change(self) -> None:
        index = self.notebook.index(self.notebook.select())
        self.current_section_key = None if index == 0 else get_section_keys()[index - 1]

    def _collect_general(self) -> dict[str, str]:
        return {key: _widget_text(widget) for key, widget in self.general_widgets.items()}

    def _collect_sections(self) -> dict[str, dict[str, str]]:
        return {section_key: {key: _widget_text(widget) for key, widget in widgets.items()} for section_key, widgets in self.section_widgets.items()}

    def _selected_sections(self) -> list[str]:
        return [key for key in get_section_keys() if self.section_enabled[key].get()]

    def _generate_current(self) -> None:
        if not self.current_section_key:
            messagebox.showinfo("Choose a section", "Select a section tab before generating a current section.")
            return
        self.section_enabled[self.current_section_key].set(True)
        general = self._collect_general()
        section_data = self._collect_sections()[self.current_section_key]
        narrative = generate_section_narrative(general, self.current_section_key, section_data)
        issues = run_quality_checks(general, self.current_section_key, section_data, narrative)
        self.current_issues = issues
        self._set_preview(narrative, issues)

    def _generate_all(self) -> None:
        selected = self._selected_sections()
        if not selected:
            messagebox.showinfo("No sections selected", "Check at least one section to include.")
            return
        general = self._collect_general()
        sections = self._collect_sections()
        narratives = generate_multiple_narratives(general, sections, selected)
        all_issues = []
        combined = []
        for key, narrative in narratives.items():
            issues = run_quality_checks(general, key, sections[key], narrative)
            all_issues.extend(issues)
            combined.append(f"{get_section_title(key)}\n\n{narrative}")
        self.current_section_key = None
        self.current_issues = all_issues
        self._set_preview("\n\n".join(combined), all_issues)

    def _export_current(self) -> None:
        if not self.current_section_key:
            messagebox.showinfo("Generate one section", "Generate a current section before exporting this preview.")
            return
        narrative = self.preview_text.get("1.0", "end").strip()
        general = self._collect_general()
        section_data = self._collect_sections()[self.current_section_key]
        issues = run_quality_checks(general, self.current_section_key, section_data, narrative)
        if not self._confirm_export(issues):
            return
        try:
            path = export_section_docx(general, self.current_section_key, narrative, issues)
        except PermissionError:
            messagebox.showerror("Could not save", "Close the Word document if it is open, then try again.")
            return
        messagebox.showinfo("Export complete", f"Saved:\n{path}")

    def _export_all(self) -> None:
        selected = self._selected_sections()
        if not selected:
            messagebox.showinfo("No sections selected", "Check at least one section to include.")
            return
        general = self._collect_general()
        sections = self._collect_sections()
        narratives = generate_multiple_narratives(general, sections, selected)
        issues_by_section = {key: run_quality_checks(general, key, sections.get(key, {}), narratives[key]) for key in selected}
        all_issues = [issue for issues in issues_by_section.values() for issue in issues]
        if not self._confirm_export(all_issues):
            return
        try:
            for key, narrative in narratives.items():
                export_section_docx(general, key, narrative, issues_by_section[key])
            path = export_combined_docx(general, narratives, issues_by_section)
        except PermissionError:
            messagebox.showerror("Could not save", "Close any open Word documents from the output folder, then try again.")
            return
        messagebox.showinfo("Export complete", f"Saved individual sections and combined narrative:\n{path}")

    def _confirm_export(self, issues) -> bool:
        self._set_warnings(issues)
        if not issues:
            return True
        text = format_issues(issues) + "\n\nDo you want to export anyway?"
        return messagebox.askyesno("Quality-control warnings", text)

    def _set_preview(self, text: str, issues) -> None:
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", text)
        self._set_warnings(issues)

    def _set_warnings(self, issues) -> None:
        self.warning_text.delete("1.0", "end")
        self.warning_text.insert("1.0", format_issues(issues))

    def _project_data(self) -> dict:
        return {"general": self._collect_general(), "sections": self._collect_sections(), "selected_sections": self._selected_sections()}

    def _save_project(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if path:
            save_project(path, self._project_data())

    def _load_project(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            self._load_data(load_project(path))

    def _load_sample(self) -> None:
        sample = Path(__file__).resolve().parents[1] / "examples" / "sample_farm_input.json"
        self._load_data(json.loads(sample.read_text(encoding="utf-8")))

    def _load_data(self, data: dict) -> None:
        for key, widget in self.general_widgets.items():
            _set_widget_text(widget, data.get("general", {}).get(key, ""))
        sections = data.get("sections", {})
        for section_key, widgets in self.section_widgets.items():
            section_data = sections.get(section_key, {})
            for key, widget in widgets.items():
                _set_widget_text(widget, section_data.get(key, ""))
        selected = set(data.get("selected_sections", []))
        for key, var in self.section_enabled.items():
            var.set(key in selected)


def _widget_text(widget) -> str:
    if isinstance(widget, ScrolledText):
        return widget.get("1.0", "end").strip()
    return widget.get().strip()


def _set_widget_text(widget, value: str) -> None:
    if isinstance(widget, ScrolledText):
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
    else:
        widget.delete(0, "end")
        widget.insert(0, value)


def launch() -> None:
    root = tk.Tk()
    ExistingConditionsApp(root)
    root.mainloop()


def run_from_json(path: Path) -> list[Path]:
    data = json.loads(path.read_text(encoding="utf-8"))
    general = data.get("general", {})
    sections = data.get("sections", {})
    selected = data.get("selected_sections") or list(sections.keys())
    narratives = generate_multiple_narratives(general, sections, selected)
    issues_by_section = {key: run_quality_checks(general, key, sections.get(key, {}), narratives[key]) for key in selected}
    paths = []
    for key, narrative in narratives.items():
        paths.append(export_section_docx(general, key, narrative, issues_by_section[key]))
    paths.append(export_combined_docx(general, narratives, issues_by_section))
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CNMP Existing Conditions Narrative Generator")
    parser.add_argument("--from-json", help="Generate Word output from a saved JSON project.")
    parser.add_argument("--sample", action="store_true", help="Generate Word output from the bundled sample.")
    args = parser.parse_args(argv)
    if args.sample or args.from_json:
        path = Path(args.from_json) if args.from_json else Path(__file__).resolve().parents[1] / "examples" / "sample_farm_input.json"
        paths = run_from_json(path)
        print("Generated:")
        for output in paths:
            print(output)
        return 0
    launch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
