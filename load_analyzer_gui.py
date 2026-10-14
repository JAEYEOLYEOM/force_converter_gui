"""GUI for selecting load data, calculating stress, and viewing a graph."""

import math
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TypedDict

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from load_analyzer import LoadRecord, read_load_data


class StressRecord(TypedDict):
    time_s: float
    stress_MPa: float


SECTION_FIELDS: dict[str, tuple[tuple[str, str], ...]] = {
    "사각형": (("b", "폭 b"), ("h", "높이 h")),
    "원형봉": (("d", "지름 d"),),
    "원형관": (("D", "외경 D"), ("t", "두께 t")),
    "사각형관": (
        ("B", "외측 폭 B"),
        ("H", "외측 높이 H"),
        ("t", "두께 t"),
    ),
    "H형강": (
        ("H", "전체 높이 H"),
        ("B", "플랜지 폭 B"),
        ("tw", "웹 두께 tw"),
        ("tf", "플랜지 두께 tf"),
    ),
}


class LoadAnalyzerGUI:
    """Display validated load data and calculate stress for selected sections."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Load Analyzer")
        self.root.geometry("900x700")

        self.file_path = tk.StringVar()
        self.valid_count = tk.StringVar(value="유효한 데이터 수: -")
        self.section_type = tk.StringVar(value="사각형")
        self.area = tk.StringVar(value="단면적 A: - mm²")
        self.maximum_stress = tk.StringVar(value="최대 응력: -")
        self.records: list[LoadRecord] = []
        self.dimension_vars: dict[str, tk.StringVar] = {}
        self.dimension_entries: dict[str, ttk.Entry] = {}

        controls = ttk.Frame(root, padding=10)
        controls.pack(fill="x")

        ttk.Button(
            controls,
            text="CSV 찾아보기",
            command=self.select_csv_file,
        ).pack(side="left")
        ttk.Entry(
            controls,
            textvariable=self.file_path,
            state="readonly",
        ).pack(side="left", fill="x", expand=True, padx=(8, 0))

        section_controls = ttk.Frame(root, padding=(10, 0, 10, 10))
        section_controls.pack(fill="x")

        ttk.Label(section_controls, text="단면 종류:").grid(
            row=0, column=0, sticky="w"
        )
        section_type_combo = ttk.Combobox(
            section_controls,
            textvariable=self.section_type,
            values=tuple(SECTION_FIELDS),
            state="readonly",
            width=10,
        )
        section_type_combo.grid(row=0, column=1, padx=(4, 12), sticky="w")
        section_type_combo.bind(
            "<<ComboboxSelected>>", self.on_section_type_changed
        )

        self.dimension_frame = ttk.Frame(section_controls)
        self.dimension_frame.grid(
            row=1, column=0, columnspan=4, pady=(8, 0), sticky="w"
        )
        self.create_dimension_fields()

        ttk.Label(section_controls, textvariable=self.area).grid(
            row=2, column=0, columnspan=2, pady=(8, 0), sticky="w"
        )
        ttk.Button(
            section_controls,
            text="분석",
            command=self.analyze,
        ).grid(row=2, column=2, columnspan=2, pady=(8, 0), sticky="w")

        ttk.Label(
            root,
            textvariable=self.valid_count,
            padding=(10, 0, 10, 10),
        ).pack(anchor="w")
        ttk.Label(
            root,
            textvariable=self.maximum_stress,
            padding=(10, 0, 10, 10),
        ).pack(anchor="w")

        self.figure = Figure(figsize=(8, 5), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=10, pady=(0, 10)
        )
        self.clear_plot()

    def create_dimension_fields(self) -> None:
        """Create only the dimension inputs required by the selected section."""
        for child in self.dimension_frame.winfo_children():
            child.destroy()

        self.dimension_vars = {}
        self.dimension_entries = {}
        for column, (key, label_text) in enumerate(
            SECTION_FIELDS[self.section_type.get()]
        ):
            ttk.Label(self.dimension_frame, text=f"{label_text} (mm):").grid(
                row=0, column=column * 2, padx=(0, 4), sticky="w"
            )
            variable = tk.StringVar()
            variable.trace_add("write", self.on_dimension_changed)
            self.dimension_vars[key] = variable
            entry = ttk.Entry(
                self.dimension_frame,
                textvariable=variable,
                width=10,
            )
            entry.grid(row=0, column=column * 2 + 1, padx=(0, 12))
            self.dimension_entries[key] = entry

        self.update_area()

    def on_section_type_changed(self, _event: tk.Event[tk.Widget]) -> None:
        """Reset analysis state and rebuild inputs after a section change."""
        self.create_dimension_fields()
        self.reset_analysis_result()

    def on_dimension_changed(
        self,
        _name: str,
        _index: str,
        _mode: str,
    ) -> None:
        """Update the displayed area and invalidate old analysis results."""
        self.update_area()
        self.reset_analysis_result()

    def select_csv_file(self) -> None:
        """Open a file chooser and display the selected CSV data."""
        selected_file = filedialog.askopenfilename(
            title="CSV 파일 선택",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if not selected_file:
            return

        data_file = Path(selected_file)
        self.file_path.set(str(data_file))
        self.load_csv(data_file)

    def load_csv(self, data_file: Path) -> None:
        """Read and validate the selected CSV file."""
        try:
            records, excluded_count = read_load_data(data_file)
        except (OSError, ValueError) as error:
            self.records = []
            self.valid_count.set("유효한 데이터 수: -")
            self.reset_analysis_result()
            messagebox.showerror("CSV 읽기 오류", str(error), parent=self.root)
            return

        self.records = records
        self.valid_count.set(
            f"유효한 데이터 수: {len(records)}개"
            f" (제외된 행: {excluded_count}개)"
        )
        self.reset_analysis_result()
        self.update_load_plot(records)

    def parse_dimensions(self) -> dict[str, float]:
        """Parse and validate all dimensions for the selected section."""
        values: dict[str, float] = {}
        for key, variable in self.dimension_vars.items():
            try:
                value = float(variable.get())
            except ValueError as error:
                raise ValueError("모든 치수는 유한한 숫자로 입력하세요.") from error
            if not math.isfinite(value):
                raise ValueError("모든 치수는 유한한 숫자로 입력하세요.")
            values[key] = value

        if any(value <= 0 for value in values.values()):
            raise ValueError("모든 치수는 0보다 큰 값이어야 합니다.")

        section = self.section_type.get()
        if section == "원형관" and 2 * values["t"] >= values["D"]:
            raise ValueError("원형관은 2*t가 외경 D보다 작아야 합니다.")
        if section == "사각형관" and (
            2 * values["t"] >= values["B"]
            or 2 * values["t"] >= values["H"]
        ):
            raise ValueError(
                "사각형관은 2*t가 외측 폭 B와 외측 높이 H보다 작아야 합니다."
            )
        if section == "H형강" and (
            2 * values["tf"] >= values["H"]
            or values["tw"] >= values["B"]
        ):
            raise ValueError(
                "H형강은 2*tf가 H보다 작고 tw가 B보다 작아야 합니다."
            )
        return values

    def calculate_area(self, values: dict[str, float]) -> float:
        """Calculate the unrounded area for the selected idealized section."""
        section = self.section_type.get()
        if section == "사각형":
            area = values["b"] * values["h"]
        elif section == "원형봉":
            area = math.pi * values["d"] ** 2 / 4
        elif section == "원형관":
            area = math.pi * (
                values["D"] ** 2 - (values["D"] - 2 * values["t"]) ** 2
            ) / 4
        elif section == "사각형관":
            area = values["B"] * values["H"] - (
                values["B"] - 2 * values["t"]
            ) * (values["H"] - 2 * values["t"])
        else:
            area = 2 * values["B"] * values["tf"] + (
                values["H"] - 2 * values["tf"]
            ) * values["tw"]

        if not math.isfinite(area) or area <= 0:
            raise ValueError("계산된 단면적이 유효하지 않습니다.")
        return area

    def update_area(self) -> None:
        """Update the displayed area, showing a rounded value only."""
        try:
            area = self.calculate_area(self.parse_dimensions())
        except ValueError:
            self.area.set("단면적 A: - mm²")
            return
        self.area.set(f"단면적 A: {area:g} mm²")

    def analyze(self) -> None:
        """Calculate stress and update the maximum and stress graph."""
        if not self.file_path.get() or not self.records:
            messagebox.showwarning(
                "분석 안내",
                "먼저 유효한 데이터가 있는 CSV 파일을 선택하세요.",
                parent=self.root,
            )
            return

        try:
            area = self.calculate_area(self.parse_dimensions())
        except ValueError as error:
            messagebox.showwarning("입력 안내", str(error), parent=self.root)
            return

        stress_records: list[StressRecord] = [
            {
                "time_s": record["time_s"],
                "stress_MPa": record["force_N"] / area,
            }
            for record in self.records
        ]
        maximum_record = max(
            stress_records, key=lambda record: record["stress_MPa"]
        )
        self.area.set(f"단면적 A: {area:g} mm²")
        self.maximum_stress.set(
            f"최대 응력: {maximum_record['stress_MPa']:g} MPa"
            f" (시간: {maximum_record['time_s']:g} s)"
        )
        self.update_stress_plot(stress_records)

    def reset_analysis_result(self) -> None:
        """Clear results that could be mistaken for the current inputs."""
        self.maximum_stress.set("최대 응력: -")
        self.update_area()
        if hasattr(self, "axes"):
            self.update_load_plot(self.records)

    def clear_plot(self) -> None:
        """Clear the graph and show the default axis labels."""
        self.axes.clear()
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Force (N)")
        self.axes.grid(True)
        self.canvas.draw()

    def update_load_plot(self, records: list[LoadRecord]) -> None:
        """Draw the time-force graph for validated records."""
        self.axes.clear()
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Force (N)")
        self.axes.grid(True)
        if records:
            self.axes.plot(
                [record["time_s"] for record in records],
                [record["force_N"] for record in records],
                marker="o",
            )
        self.figure.tight_layout()
        self.canvas.draw()

    def update_stress_plot(self, records: list[StressRecord]) -> None:
        """Draw the time-stress graph for calculated records."""
        self.axes.clear()
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Stress (MPa)")
        self.axes.grid(True)
        self.axes.plot(
            [record["time_s"] for record in records],
            [record["stress_MPa"] for record in records],
            marker="o",
        )
        self.figure.tight_layout()
        self.canvas.draw()


def main() -> None:
    """Start the load analyzer GUI."""
    root = tk.Tk()
    LoadAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
