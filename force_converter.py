# force_converter.py
"""힘 단위 변환기 (GUI 계산기 버전)

실습 4: 콘솔용 force_converter를 tkinter 창 계산기로 확장한 프로그램이다.
 - 어두운 디스플레이 창에 입력값과 변환 결과가 함께 표시된다.
 - 숫자 키패드 / 단위 버튼 / 변환 버튼만으로 마우스 조작이 가능하다.
 - 키보드 입력과 Enter 키도 그대로 쓸 수 있다.
 - 잘못된 입력은 디스플레이 안에 빨간 안내로 표시된다.
 - 창을 닫지 않고 값을 바꾸어 몇 번이든 다시 계산할 수 있다.

추가 기능: 변환 기록(History)
 - 변환할 때마다 오른쪽 목록에 결과가 최신순으로 쌓인다.
 - 기록을 더블클릭하면 그때의 값과 단위가 다시 불러와진다.
 - [기록 지우기] 버튼으로 목록을 비울 수 있다.
"""

import tkinter as tk
from tkinter import ttk

# 각 단위 1에 해당하는 뉴턴(N) 값
UNIT_TO_NEWTON = {
    "kN": 1000.0,
    "N": 1.0,
    "kgf": 9.80665,  # 표준중력가속도 기준
}
UNITS = list(UNIT_TO_NEWTON)

# 화면 색상
BG = "#e8edf5"          # 창 배경
HEADER = "#1e3a8a"      # 상단 머리말
DISPLAY = "#0f172a"     # 디스플레이 배경
DISPLAY_SUB = "#94a3b8"  # 디스플레이 보조 글씨
ACCENT = "#3b82f6"      # 강조색
CARD = "#ffffff"        # 카드 배경
LINE = "#cbd5e1"        # 테두리
TEXT = "#111827"        # 기본 글씨
DANGER = "#dc2626"      # 오류 색


class InputError(Exception):
    """사용자 입력이 잘못되었을 때 사용하는 예외."""


# ---------------------------------------------------------------- 계산 로직
def convert_to_newtons(value, unit):
    """입력 값을 뉴턴(N) 단위로 변환한다."""
    if unit not in UNIT_TO_NEWTON:
        raise ValueError("지원하지 않는 단위입니다.")
    return value * UNIT_TO_NEWTON[unit]


def convert_from_newtons(value_n, unit):
    """뉴턴 값을 원하는 단위로 변환한다."""
    if unit not in UNIT_TO_NEWTON:
        raise ValueError("지원하지 않는 단위입니다.")
    return value_n / UNIT_TO_NEWTON[unit]


def convert_force(value, from_unit, to_unit):
    """from_unit 기준 값을 to_unit 기준 값으로 변환한다."""
    return convert_from_newtons(convert_to_newtons(value, from_unit), to_unit)


def parse_value(raw_value):
    """입력창 문자열을 실수로 바꾼다. 잘못된 입력이면 InputError를 낸다."""
    text = raw_value.strip()
    if not text:
        raise InputError("값을 입력해주세요.")
    try:
        return float(text)
    except ValueError:
        raise InputError(f"'{text}' 은(는) 숫자가 아닙니다. 예: 12.5")


def format_number(value):
    """결과를 읽기 좋은 문자열로 만든다."""
    if value != 0 and abs(value) < 0.0001:
        return f"{value:.4e}"
    text = f"{value:,.4f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


# ---------------------------------------------------------------- 화면 구성
def setup_styles():
    style = ttk.Style()
    style.theme_use("clam")

    def flat_button(name, bg, fg, active, font, padding):
        style.configure(name, background=bg, foreground=fg, font=font,
                        padding=padding, relief="flat", borderwidth=0,
                        focuscolor=bg, lightcolor=bg, darkcolor=bg, bordercolor=bg)
        style.map(name,
                  background=[("active", active), ("pressed", active)],
                  foreground=[("active", fg), ("pressed", fg)])

    # 숫자 키패드
    flat_button("Key.TButton", CARD, TEXT, "#dbe4f0", ("Arial", 17), (0, 12))
    # 보조 키 (지우기, 부호)
    flat_button("KeyAlt.TButton", "#dfe6f0", "#1f2937", "#c7d2de", ("Arial", 15, "bold"), (0, 12))
    # 변환 버튼
    flat_button("Accent.TButton", ACCENT, "white", "#2563eb", ("Arial", 16, "bold"), (0, 12))
    # 단위 버튼 (꺼짐 / 켜짐)
    flat_button("Unit.TButton", CARD, "#475569", "#dbe4f0", ("Arial", 13, "bold"), (0, 8))
    flat_button("UnitOn.TButton", "#1e3a8a", "white", "#1e3a8a", ("Arial", 13, "bold"), (0, 8))
    # 작은 보조 버튼
    flat_button("Sub.TButton", "#e2e8f0", "#334155", "#cbd5e1", ("Arial", 11), (10, 7))
    flat_button("Swap.TButton", "#fef3c7", "#92400e", "#fde68a", ("Arial", 14, "bold"), (0, 6))

    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("Label.TLabel", font=("Arial", 12), background=BG, foreground="#475569")
    style.configure("CardLabel.TLabel", font=("Arial", 11, "bold"), background=CARD, foreground="#64748b")
    style.configure("Vert.Vertical.TScrollbar", background="#cbd5e1", troughcolor=CARD,
                    bordercolor=CARD, arrowcolor="#64748b")


class UnitSelector:
    """kN / N / kgf 중 하나를 고르는 버튼 묶음."""

    def __init__(self, parent, initial, on_change):
        self.value = initial
        self.on_change = on_change
        self.buttons = {}
        for unit in UNITS:
            button = ttk.Button(parent, text=unit, width=5, style="Unit.TButton",
                                command=lambda u=unit: self.set(u))
            button.pack(side="left", padx=3)
            self.buttons[unit] = button
        self.set(initial, notify=False)

    def get(self):
        return self.value

    def set(self, unit, notify=True):
        self.value = unit
        for name, button in self.buttons.items():
            button.configure(style="UnitOn.TButton" if name == unit else "Unit.TButton")
        if notify:
            self.on_change()


def build_gui():
    root = tk.Tk()
    root.title("힘 단위 변환기")
    root.geometry("880x620")
    root.minsize(880, 620)
    root.configure(bg=BG)
    setup_styles()

    # ---------- 상단 머리말 ----------
    header = tk.Frame(root, bg=HEADER, height=74)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(header, text="⚖  힘 단위 변환기", bg=HEADER, fg="white",
             font=("Arial", 21, "bold")).pack(side="left", padx=26)
    tk.Label(header, text="kN  ·  N  ·  kgf", bg=HEADER, fg="#a5b4fc",
             font=("Arial", 13)).pack(side="right", padx=26)

    body = tk.Frame(root, bg=BG)
    body.pack(fill="both", expand=True, padx=20, pady=18)

    left = tk.Frame(body, bg=BG)
    left.pack(side="left", fill="both", expand=True)

    right = tk.Frame(body, bg=BG, width=300)
    right.pack(side="right", fill="y", padx=(18, 0))
    right.pack_propagate(False)

    # ---------- 디스플레이 ----------
    display = tk.Frame(left, bg=DISPLAY, padx=20, pady=16)
    display.pack(fill="x")

    value_var = tk.StringVar()
    from_unit_var = tk.StringVar(value="kN")
    result_var = tk.StringVar(value="= 변환 버튼을 눌러주세요")
    error_var = tk.StringVar(value="")

    entry_row = tk.Frame(display, bg=DISPLAY)
    entry_row.pack(fill="x")

    tk.Label(entry_row, textvariable=from_unit_var, bg=DISPLAY, fg=DISPLAY_SUB,
             font=("Arial", 17, "bold"), width=4, anchor="e").pack(side="right", padx=(10, 0))
    value_entry = tk.Entry(entry_row, textvariable=value_var, bg=DISPLAY, fg="white",
                           font=("Arial", 32, "bold"), justify="right", relief="flat",
                           insertbackground=ACCENT, highlightthickness=0, borderwidth=0)
    value_entry.pack(side="right", fill="x", expand=True)
    value_entry.focus()

    tk.Frame(display, bg="#1e293b", height=1).pack(fill="x", pady=10)

    tk.Label(display, textvariable=result_var, bg=DISPLAY, fg="#7dd3fc",
             font=("Arial", 19, "bold"), anchor="e").pack(fill="x")

    error_label = tk.Label(display, textvariable=error_var, bg=DISPLAY, fg="#fca5a5",
                           font=("Arial", 12), anchor="e")
    # 오류가 있을 때만 화면에 붙인다.

    def show_error(message):
        error_var.set(f"⚠  {message}")
        if not error_label.winfo_ismapped():
            error_label.pack(fill="x", pady=(8, 0))

    def hide_error():
        error_var.set("")
        if error_label.winfo_ismapped():
            error_label.pack_forget()

    # ---------- 단위 선택 ----------
    unit_card = tk.Frame(left, bg=CARD, padx=16, pady=12,
                         highlightbackground=LINE, highlightthickness=1)
    unit_card.pack(fill="x", pady=(14, 0))

    ttk.Label(unit_card, text="단위 선택", style="CardLabel.TLabel").pack(anchor="w", pady=(0, 8))

    unit_row = tk.Frame(unit_card, bg=CARD)
    unit_row.pack()

    from_box = tk.Frame(unit_row, bg=CARD)
    from_box.pack(side="left")
    to_box = tk.Frame(unit_row, bg=CARD)

    def on_source_change():
        from_unit_var.set(source_unit.get())

    source_unit = UnitSelector(from_box, "kN", on_source_change)

    swap_holder = tk.Frame(unit_row, bg=CARD)
    swap_holder.pack(side="left", padx=14)
    to_box.pack(side="left")
    target_unit = UnitSelector(to_box, "N", lambda: None)

    def handle_swap():
        a, b = source_unit.get(), target_unit.get()
        source_unit.set(b)
        target_unit.set(a)

    ttk.Button(swap_holder, text="⇄", width=3, style="Swap.TButton",
               command=handle_swap).pack()

    # ---------- 키패드 ----------
    keypad = tk.Frame(left, bg=BG)
    keypad.pack(fill="both", expand=True, pady=(14, 0))
    for col in range(4):
        keypad.columnconfigure(col, weight=1, uniform="key")
    for row in range(4):
        keypad.rowconfigure(row, weight=1)

    history_records = []  # (값, 입력단위, 출력단위)

    def append_char(char):
        hide_error()
        current = value_var.get()
        if char == "." and "." in current:
            return
        value_var.set(current + char)
        value_entry.icursor(tk.END)

    def handle_backspace():
        hide_error()
        value_var.set(value_var.get()[:-1])

    def handle_clear_input():
        hide_error()
        value_var.set("")
        result_var.set("= 변환 버튼을 눌러주세요")
        value_entry.focus()

    def handle_sign():
        hide_error()
        text = value_var.get()
        value_var.set(text[1:] if text.startswith("-") else "-" + text)

    def handle_convert():
        try:
            force_value = parse_value(value_var.get())
            from_unit = source_unit.get()
            to_unit = target_unit.get()
            converted = convert_force(force_value, from_unit, to_unit)
        except (InputError, ValueError) as error:
            result_var.set("=  ?")
            show_error(str(error))
            return

        result_var.set(f"=  {format_number(converted)} {to_unit}")
        hide_error()

        line = f"{format_number(force_value)} {from_unit} = {format_number(converted)} {to_unit}"
        history_records.insert(0, (force_value, from_unit, to_unit))
        history_list.insert(0, f" {len(history_records):>2}.  {line}")
        history_list.see(0)

    keys = [
        ("7", 0, 0, "Key.TButton", lambda: append_char("7")),
        ("8", 0, 1, "Key.TButton", lambda: append_char("8")),
        ("9", 0, 2, "Key.TButton", lambda: append_char("9")),
        ("⌫", 0, 3, "KeyAlt.TButton", handle_backspace),
        ("4", 1, 0, "Key.TButton", lambda: append_char("4")),
        ("5", 1, 1, "Key.TButton", lambda: append_char("5")),
        ("6", 1, 2, "Key.TButton", lambda: append_char("6")),
        ("C", 1, 3, "KeyAlt.TButton", handle_clear_input),
        ("1", 2, 0, "Key.TButton", lambda: append_char("1")),
        ("2", 2, 1, "Key.TButton", lambda: append_char("2")),
        ("3", 2, 2, "Key.TButton", lambda: append_char("3")),
        ("±", 2, 3, "KeyAlt.TButton", handle_sign),
        ("0", 3, 0, "Key.TButton", lambda: append_char("0")),
        (".", 3, 1, "Key.TButton", lambda: append_char(".")),
    ]
    for text, row, col, key_style, command in keys:
        ttk.Button(keypad, text=text, style=key_style, command=command).grid(
            row=row, column=col, sticky="nsew", padx=4, pady=4)

    ttk.Button(keypad, text="변환", style="Accent.TButton", command=handle_convert).grid(
        row=3, column=2, columnspan=2, sticky="nsew", padx=4, pady=4)

    # ---------- 오른쪽: 변환 기록 ----------
    history_card = tk.Frame(right, bg=CARD, padx=14, pady=12,
                            highlightbackground=LINE, highlightthickness=1)
    history_card.pack(fill="both", expand=True)

    ttk.Label(history_card, text="변환 기록", style="CardLabel.TLabel").pack(anchor="w")
    tk.Label(history_card, text="더블클릭하면 다시 불러옵니다", bg=CARD, fg="#94a3b8",
             font=("Arial", 10)).pack(anchor="w", pady=(2, 8))

    list_holder = tk.Frame(history_card, bg=CARD)
    list_holder.pack(fill="both", expand=True)

    history_list = tk.Listbox(list_holder, font=("Arial", 11), bg="#f8fafc", fg=TEXT,
                              highlightthickness=0, borderwidth=0, activestyle="none",
                              selectbackground="#dbeafe", selectforeground=TEXT)
    scrollbar = ttk.Scrollbar(list_holder, orient="vertical", style="Vert.Vertical.TScrollbar",
                              command=history_list.yview)
    history_list.configure(yscrollcommand=scrollbar.set)
    history_list.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def handle_history_reuse(event=None):
        selection = history_list.curselection()
        if not selection:
            return
        value, from_unit, to_unit = history_records[selection[0]]
        value_var.set(format_number(value).replace(",", ""))
        source_unit.set(from_unit)
        target_unit.set(to_unit)
        hide_error()
        value_entry.focus()

    def handle_clear_history():
        history_records.clear()
        history_list.delete(0, tk.END)

    def handle_reset():
        handle_clear_input()
        source_unit.set("kN")
        target_unit.set("N")

    bottom = tk.Frame(right, bg=BG)
    bottom.pack(fill="x", pady=(10, 0))
    ttk.Button(bottom, text="기록 지우기", style="Sub.TButton",
               command=handle_clear_history).pack(side="left")
    ttk.Button(bottom, text="초기화", style="Sub.TButton",
               command=handle_reset).pack(side="left", padx=6)
    ttk.Button(bottom, text="종료", style="Sub.TButton",
               command=root.destroy).pack(side="right")

    # ---------- 키보드 단축키 ----------
    value_entry.bind("<Return>", lambda event: handle_convert())
    root.bind("<Escape>", lambda event: handle_clear_input())
    history_list.bind("<Double-Button-1>", handle_history_reuse)

    root.mainloop()


def main():
    build_gui()


if __name__ == "__main__":
    main()
