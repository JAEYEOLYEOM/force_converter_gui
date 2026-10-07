"""Load data analyzer for load_data.csv."""

import csv
import math
from pathlib import Path
from typing import TypedDict

import matplotlib.pyplot as plt


DATA_FILE = Path(__file__).with_name("load_data.csv")
RESULT_FILE = Path(__file__).with_name("load_result.csv")
PLOT_FILE = Path(__file__).with_name("stress_plot.png")
EXPECTED_COLUMNS = ("time_s", "force_N")
AREA_MM2 = 200


class LoadRecord(TypedDict):
    time_s: float
    force_N: float


class ResultRecord(LoadRecord):
    stress_MPa: float


def read_load_data(data_file: Path) -> tuple[list[LoadRecord], int]:
    """Read and validate load records from a CSV file."""
    with data_file.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != list(EXPECTED_COLUMNS):
            raise ValueError(
                "CSV 열 이름은 'time_s,force_N'이어야 합니다."
            )

        records: list[LoadRecord] = []
        excluded_count = 0
        for row_number, row in enumerate(reader, start=2):
            time_text = row.get("time_s", "")
            force_text = row.get("force_N", "")
            invalid_values: list[str] = []

            if not time_text:
                invalid_values.append("time_s='' (빈칸)")
            else:
                try:
                    time_s = float(time_text)
                    if not math.isfinite(time_s):
                        invalid_values.append(
                            f"time_s='{time_text}' (유한하지 않은 숫자)"
                        )
                except ValueError:
                    invalid_values.append(
                        f"time_s='{time_text}' (숫자가 아님)"
                    )

            if not force_text:
                invalid_values.append("force_N='' (빈칸)")
            else:
                try:
                    force_N = float(force_text)
                    if not math.isfinite(force_N):
                        invalid_values.append(
                            f"force_N='{force_text}' (유한하지 않은 숫자)"
                        )
                except ValueError:
                    invalid_values.append(
                        f"force_N='{force_text}' (숫자가 아님)"
                    )

            if invalid_values:
                print(f"{row_number}행 제외: {', '.join(invalid_values)}")
                excluded_count += 1
                continue

            records.append({"time_s": time_s, "force_N": force_N})

    return records, excluded_count


def calculate_stress(records: list[LoadRecord]) -> list[ResultRecord]:
    """Calculate stress in MPa from force in N and area in mm²."""
    return [
        {
            "time_s": record["time_s"],
            "force_N": record["force_N"],
            "stress_MPa": record["force_N"] / AREA_MM2,
        }
        for record in records
    ]


def write_load_result(result_file: Path, records: list[ResultRecord]) -> None:
    """Write load and stress data to a separate CSV file."""
    with result_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=("time_s", "force_N", "stress_MPa")
        )
        writer.writeheader()
        writer.writerows(records)


def save_stress_plot(plot_file: Path, records: list[ResultRecord]) -> None:
    """Save a time-stress plot and highlight the maximum stress."""
    times = [record["time_s"] for record in records]
    stresses = [record["stress_MPa"] for record in records]
    maximum_record = max(records, key=lambda record: record["stress_MPa"])

    figure, axes = plt.subplots()
    axes.plot(times, stresses, marker="o")
    axes.scatter(
        maximum_record["time_s"],
        maximum_record["stress_MPa"],
        color="red",
        zorder=3,
    )
    axes.annotate(
        (
            f"Time: {maximum_record['time_s']:g} s\n"
            f"Stress: {maximum_record['stress_MPa']:g} MPa"
        ),
        xy=(maximum_record["time_s"], maximum_record["stress_MPa"]),
        xytext=(10, 10),
        textcoords="offset points",
    )
    axes.set_xlabel("Time (s)")
    axes.set_ylabel("Stress (MPa)")
    figure.tight_layout()
    figure.savefig(plot_file)
    plt.close(figure)


def main() -> int:
    """Analyze load data, save stress results, and print statistics."""
    try:
        records, excluded_count = read_load_data(DATA_FILE)
        print(f"제외한 행 수: {excluded_count}개")
        print(f"유효한 데이터 수: {len(records)}개")
        if not records:
            print("유효한 데이터가 없어 계산을 중단합니다.")
            return 1

        result_records = calculate_stress(records)
        write_load_result(RESULT_FILE, result_records)
        save_stress_plot(PLOT_FILE, result_records)
    except (OSError, ValueError) as error:
        print(f"오류: {error}")
        return 1

    maximum_record = max(records, key=lambda record: record["force_N"])
    maximum_stress_record = max(
        result_records, key=lambda record: record["stress_MPa"]
    )
    print(f"데이터 개수: {len(records)}개")
    print(f"최대 하중: {maximum_record['force_N']:g} N")
    print(f"최대 하중 시간: {maximum_record['time_s']:g} s")
    print(f"최대 응력: {maximum_stress_record['stress_MPa']:g} MPa")
    print(f"최대 응력 시간: {maximum_stress_record['time_s']:g} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
