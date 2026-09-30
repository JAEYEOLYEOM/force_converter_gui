import math
import tkinter as tk
from tkinter import ttk


KGF_TO_NEWTON = 9.80665


def convert_force():
	"""입력한 힘을 N, kN, kgf 단위로 변환해 표시한다."""
	value_text = input_entry.get().strip()

	try:
		value = float(value_text)
		if not math.isfinite(value):
			raise ValueError
	except ValueError:
		result_var.set("오류: 숫자 값을 입력해 주세요.")
		return

	selected_unit = unit_var.get()
	if selected_unit == "N":
		newtons = value
	elif selected_unit == "kN":
		newtons = value * 1000
	else:
		newtons = value * KGF_TO_NEWTON

	kilonewtons = newtons / 1000
	kilograms_force = newtons / KGF_TO_NEWTON
	result_var.set(
		f"N: {newtons:.3f}\n"
		f"kN: {kilonewtons:.3f}\n"
		f"kgf: {kilograms_force:.3f}"
	)


def reset_converter():
	"""입력값과 변환 결과를 초기화한다."""
	input_entry.delete(0, tk.END)
	unit_var.set("N")
	result_var.set("")
	input_entry.focus_set()


root = tk.Tk()
root.title("힘 단위 변환기")
root.resizable(False, False)

main_frame = ttk.Frame(root, padding=20)
main_frame.grid()

ttk.Label(main_frame, text="힘 단위 변환기", font=("TkDefaultFont", 16, "bold")).grid(
	row=0, column=0, columnspan=2, pady=(0, 16)
)

ttk.Label(main_frame, text="숫자 입력").grid(row=1, column=0, sticky="w", padx=(0, 10))
input_entry = ttk.Entry(main_frame, width=24)
input_entry.grid(row=1, column=1, pady=4)

ttk.Label(main_frame, text="입력 단위").grid(row=2, column=0, sticky="w", padx=(0, 10))
unit_var = tk.StringVar(value="N")
unit_menu = ttk.Combobox(
	main_frame,
	textvariable=unit_var,
	values=("N", "kN", "kgf"),
	state="readonly",
	width=21,
)
unit_menu.grid(row=2, column=1, pady=4)

button_frame = ttk.Frame(main_frame)
button_frame.grid(row=3, column=0, columnspan=2, pady=(12, 16))
ttk.Button(button_frame, text="변환", command=convert_force).grid(row=0, column=0, padx=4)
ttk.Button(button_frame, text="초기화", command=reset_converter).grid(row=0, column=1, padx=4)

ttk.Label(main_frame, text="변환 결과").grid(row=4, column=0, columnspan=2, sticky="w")
result_var = tk.StringVar()
result_label = ttk.Label(main_frame, textvariable=result_var, justify="left", foreground="#b00020")
result_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))

input_entry.bind("<Return>", lambda event: convert_force())
input_entry.focus_set()
root.mainloop()
