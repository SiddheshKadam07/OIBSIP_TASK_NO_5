"""
Random Password Generator - GUI Version (Advanced)
AICTE OASIS INFOBYTE SIP - Project 3
Requires: pip install pyperclip
"""

import secrets
import string
import math
import datetime
import tkinter as tk
from tkinter import ttk
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


# ── Core Logic ────────────────────────────────────────────────────────────────

def build_charset(use_upper, use_lower, use_digits, use_symbols):
    charset = ""
    if use_upper:
        charset += string.ascii_uppercase
    if use_lower:
        charset += string.ascii_lowercase
    if use_digits:
        charset += string.digits
    if use_symbols:
        charset += string.punctuation
    return charset


def generate_password(length, charset):
    if not charset:
        return None
    return "".join(secrets.choice(charset) for _ in range(length))


def generate_readable(length):
    """Pronounceable password: alternating consonant/vowel syllables."""
    consonants = "bcdfghjkmnpqrstvwxyz"
    vowels = "aeiou"
    result = []
    use_consonant = True
    while len(result) < length:
        pool = consonants if use_consonant else vowels
        result.append(secrets.choice(pool))
        use_consonant = not use_consonant
    word = "".join(result[:length])
    return word[0].upper() + word[1:] if word else word


def calculate_entropy(length, charset_size):
    if charset_size <= 1:
        return 0
    return round(length * math.log2(charset_size), 1)


def estimate_crack_time(entropy_bits):
    """Assume 10 billion guesses/sec (modern GPU cluster)."""
    guesses_per_sec = 10_000_000_000
    total_combos = 2 ** entropy_bits
    seconds = total_combos / guesses_per_sec / 2  # average case

    if seconds < 1:
        return "Instant"
    years = seconds / 31536000
    if years > 1e12:
        return f"{years:.0e} years"
    if years >= 1:
        return f"{years:,.0f} years" if years < 1e9 else f"{years:.2e} years"
    for name, unit_sec in [("day", 86400), ("hour", 3600), ("min", 60), ("sec", 1)]:
        val = seconds / unit_sec
        if val >= 1:
            return f"{val:.0f} {name}{'s' if val >= 2 else ''}"
    return "Instant"


def get_strength(entropy):
    """
    Strength scale tuned to the realistic entropy range this app produces
    (max length 12, full charset 94 chars -> ~78.7 bits at the top end),
    so the bar reaches near-full width for 'Strong' / 'Very Strong' results
    instead of stalling around 75-80%.
    """
    if entropy < 28:
        return "Very Weak",   "#E74C3C", 15
    elif entropy < 40:
        return "Weak",        "#E67E22", 35
    elif entropy < 55:
        return "Fair",        "#F39C12", 60
    elif entropy < 70:
        return "Strong",      "#27AE60", 85
    else:
        return "Very Strong", "#4F46E5", 100


# ── Theme Definitions ────────────────────────────────────────────────────────

LIGHT_THEME = {
    "BG": "#F4F6FB", "CARD": "#FFFFFF", "BORDER": "#E3E7F1",
    "TEAL": "#0E9F8E", "TEAL_BG": "#E8F7F4", "INDIGO": "#4F46E5",
    "INDIGO_HOVER": "#4338CA", "TEAL_HOVER": "#0C8B7C",
    "TEXT": "#1F2533", "SUBTEXT": "#6B7280", "DANGER": "#E74C3C",
    "ENTRY_BG": "#F4F6FB", "TROUGH": "#E3E7F1", "DOT_OFF": "#D1D5DB",
}

DARK_THEME = {
    "BG": "#10141F", "CARD": "#1A2030", "BORDER": "#2A3142",
    "TEAL": "#2DD4BF", "TEAL_BG": "#15302C", "INDIGO": "#6366F1",
    "INDIGO_HOVER": "#7C7FF5", "TEAL_HOVER": "#26B8A5",
    "TEXT": "#F1F3F9", "SUBTEXT": "#9AA3B5", "DANGER": "#F87171",
    "ENTRY_BG": "#10141F", "TROUGH": "#2A3142", "DOT_OFF": "#4B5266",
}


# ── GUI App ───────────────────────────────────────────────────────────────────

class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔐 Random Password Generator — AICTE OASIS INFOBYTE SIP")
        self.root.state('zoomed')
        self.root.resizable(True, True)
        self.root.attributes('-toolwindow', False)

        self.theme_name = "light"
        self.theme = LIGHT_THEME

        # Variables
        self.mode_var      = tk.StringVar(value="standard")  # standard | readable
        self.length_var    = tk.IntVar(value=12)
        self.use_upper     = tk.BooleanVar(value=True)
        self.use_lower     = tk.BooleanVar(value=True)
        self.use_digits    = tk.BooleanVar(value=True)
        self.use_symbols   = tk.BooleanVar(value=True)
        self.password_var  = tk.StringVar()

        self.history = []   # list of dicts: {pwd, time, entropy}

        # widget registries so theme switching can restyle everything
        self._themed_frames = []   # (widget, role)
        self._themed_labels = []   # (widget, role)
        self._themed_buttons = []  # (widget, role)

        self._build_ui()
        self.generate()

    # ── UI Builder ────────────────────────────────────────────────────────────

    def _build_ui(self):
        t = self.theme
        self.root.configure(bg=t["BG"])

        # ── Header
        self.hdr = tk.Frame(self.root, bg=t["INDIGO"], pady=14)
        self.hdr.pack(fill="x")

        hdr_top = tk.Frame(self.hdr, bg=t["INDIGO"])
        hdr_top.pack(fill="x", padx=20)

        title_box = tk.Frame(hdr_top, bg=t["INDIGO"])
        title_box.pack(side="left", expand=True)
        self.title_lbl = tk.Label(title_box, text="🔐  Random Password Generator",
                                  bg=t["INDIGO"], fg="white",
                                  font=("Segoe UI", 18, "bold"))
        self.title_lbl.pack()

        btn_text = "☀  Light Mode" if self.theme_name == "dark" else "🌙  Dark Mode"
        self.theme_btn = tk.Button(hdr_top, text=btn_text, command=self.toggle_theme,
                                   bg=t["INDIGO_HOVER"], fg="white", relief="flat",
                                   font=("Segoe UI", 9, "bold"), cursor="hand2",
                                   activebackground=t["INDIGO_HOVER"], activeforeground="white",
                                   padx=12, pady=6)
        self.theme_btn.place(relx=1.0, rely=0.5, anchor="e", x=-20)

        # Scrollable outer canvas
        self.outer = tk.Frame(self.root, bg=t["BG"])
        self.outer.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.outer, bg=t["BG"], highlightthickness=0)
        vbar = ttk.Scrollbar(self.outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        scroll_content = tk.Frame(self.canvas, bg=t["BG"])
        body_id = self.canvas.create_window((0, 0), window=scroll_content, anchor="nw")

        def on_content_config(_e=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        scroll_content.bind("<Configure>", on_content_config)

        def on_canvas_config(e):
            self.canvas.itemconfig(body_id, width=e.width)
        self.canvas.bind("<Configure>", on_canvas_config)

        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Centered column wrapper
        content = tk.Frame(scroll_content, bg=t["BG"])
        content.pack(pady=20, anchor="n")
        tk.Frame(content, bg=t["BG"], width=860, height=0).pack()  # enforces min width
        self.content = content
        self._reg_frame(scroll_content, "bg")
        self._reg_frame(content, "bg")

        # ── Password Display Card
        disp = self._card(content)

        lbl_gp = tk.Label(disp, text="Generated Password", bg=t["CARD"], fg=t["SUBTEXT"],
                          font=("Segoe UI", 9, "bold"))
        lbl_gp.pack(anchor="w", padx=20, pady=(16, 4))
        self._reg_label(lbl_gp, "sub")

        row = tk.Frame(disp, bg=t["CARD"])
        row.pack(fill="x", padx=20, pady=(0, 14))
        self._reg_frame(row, "card")

        self.pw_entry = tk.Entry(row, textvariable=self.password_var,
                                 font=("Consolas", 16), bg=t["ENTRY_BG"], fg=t["TEXT"],
                                 insertbackground=t["TEXT"], bd=0, relief="flat",
                                 state="readonly", readonlybackground=t["ENTRY_BG"])
        self.pw_entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))

        self.refresh_btn = tk.Button(row, text="⟳", command=self.generate,
                                     bg=t["INDIGO"], fg="white", relief="flat",
                                     font=("Segoe UI", 13), cursor="hand2",
                                     activebackground=t["INDIGO_HOVER"], activeforeground="white",
                                     padx=10)
        self.refresh_btn.pack(side="left", padx=(0, 6))
        self._themed_buttons.append((self.refresh_btn, "indigo"))

        self.copy_btn = tk.Button(row, text="⎘  Copy", command=self.copy_password,
                                  bg=t["TEAL"], fg="white", relief="flat",
                                  font=("Segoe UI", 10, "bold"), cursor="hand2",
                                  activebackground=t["TEAL_HOVER"], activeforeground="white",
                                  padx=12)
        self.copy_btn.pack(side="left")
        self._themed_buttons.append((self.copy_btn, "teal"))

        # ── Strength section
        str_wrap = tk.Frame(disp, bg=t["CARD"])
        str_wrap.pack(fill="x", padx=20, pady=(0, 16))
        self._reg_frame(str_wrap, "card")

        info_row = tk.Frame(str_wrap, bg=t["CARD"])
        info_row.pack(fill="x")
        self._reg_frame(info_row, "card")
        sl = tk.Label(info_row, text="PASSWORD STRENGTH", bg=t["CARD"], fg=t["SUBTEXT"],
                     font=("Segoe UI", 8, "bold"))
        sl.pack(side="left")
        self._reg_label(sl, "sub")
        self.strength_label = tk.Label(info_row, text="", bg=t["CARD"], fg=t["TEAL"],
                                       font=("Segoe UI", 9, "bold"))
        self.strength_label.pack(side="right")
        self._reg_frame(self.strength_label, "card")  # bg restyle only

        self.strength_bar = ttk.Progressbar(str_wrap, length=600, mode="determinate")
        self.strength_bar.pack(fill="x", pady=(6, 12))

        stat_row = tk.Frame(str_wrap, bg=t["CARD"])
        stat_row.pack(fill="x")
        self._reg_frame(stat_row, "card")
        self.stat_entropy = self._stat_box(stat_row, "ENTROPY", "0 bits", 0)
        self.stat_crack   = self._stat_box(stat_row, "TIME TO CRACK", "—", 1)

        # ── Mode Tabs (Standard + Readable only)
        tabs_card = self._card(content)
        self.tabs_card = tabs_card

        tab_row = tk.Frame(tabs_card, bg=t["CARD"])
        tab_row.pack(fill="x", padx=20, pady=(16, 0))
        self._reg_frame(tab_row, "card")

        self.tab_buttons = {}
        for key, label in [("standard", "STANDARD"), ("readable", "READABLE")]:
            b = tk.Label(tab_row, text=label, bg=t["CARD"], fg=t["SUBTEXT"],
                        font=("Segoe UI", 10, "bold"), cursor="hand2", padx=4)
            b.pack(side="left", padx=(0, 26), pady=(0, 10))
            b.bind("<Button-1>", lambda e, k=key: self._set_mode(k))
            self.tab_buttons[key] = b
            self._reg_frame(b, "card")

        self.tab_underline = tk.Frame(tabs_card, bg=t["BORDER"], height=2)
        self.tab_underline.pack(fill="x", padx=20)
        self._reg_frame(self.tab_underline, "border_line")

        # ── Standard options panel (length + char types)
        self.standard_panel = tk.Frame(tabs_card, bg=t["CARD"])
        self._reg_frame(self.standard_panel, "card")

        len_row = tk.Frame(self.standard_panel, bg=t["CARD"])
        len_row.pack(fill="x", padx=20, pady=(16, 4))
        self._reg_frame(len_row, "card")
        ll = tk.Label(len_row, text="LENGTH", bg=t["CARD"], fg=t["SUBTEXT"],
                     font=("Segoe UI", 8, "bold"))
        ll.pack(side="left")
        self._reg_label(ll, "sub")
        self.len_label = tk.Label(len_row, text="12 chars", bg=t["CARD"], fg=t["TEXT"],
                                  font=("Segoe UI", 10, "bold"))
        self.len_label.pack(side="right")
        self._reg_label(self.len_label, "text")

        self.slider = ttk.Scale(self.standard_panel, from_=6, to=12,
                                variable=self.length_var, orient="horizontal",
                                command=self._on_slider)
        self.slider.pack(fill="x", padx=20, pady=(0, 16))

        co = tk.Label(self.standard_panel, text="CHARACTER OPTIONS", bg=t["CARD"], fg=t["SUBTEXT"],
                     font=("Segoe UI", 8, "bold"))
        co.pack(anchor="w", padx=20, pady=(0, 8))
        self._reg_label(co, "sub")

        chk_grid = tk.Frame(self.standard_panel, bg=t["CARD"])
        chk_grid.pack(fill="x", padx=20, pady=(0, 16))
        chk_grid.columnconfigure(0, weight=1)
        chk_grid.columnconfigure(1, weight=1)
        self._reg_frame(chk_grid, "card")

        self.toggle_boxes = []
        self.toggle_boxes.append(self._toggle_box(chk_grid, "UPPERCASE", "A-Z", self.use_upper, 0, 0))
        self.toggle_boxes.append(self._toggle_box(chk_grid, "LOWERCASE", "a-z", self.use_lower, 0, 1))
        self.toggle_boxes.append(self._toggle_box(chk_grid, "NUMBERS",   "0-9", self.use_digits, 1, 0))
        self.toggle_boxes.append(self._toggle_box(chk_grid, "SYMBOLS",   "!@#$", self.use_symbols, 1, 1))

        # ── Readable panel
        self.readable_panel = tk.Frame(tabs_card, bg=t["CARD"])
        self._reg_frame(self.readable_panel, "card")

        rd_row = tk.Frame(self.readable_panel, bg=t["CARD"])
        rd_row.pack(fill="x", padx=20, pady=(16, 4))
        self._reg_frame(rd_row, "card")
        rl = tk.Label(rd_row, text="LENGTH", bg=t["CARD"], fg=t["SUBTEXT"],
                     font=("Segoe UI", 8, "bold"))
        rl.pack(side="left")
        self._reg_label(rl, "sub")
        self.readable_len_label = tk.Label(rd_row, text="12 chars", bg=t["CARD"], fg=t["TEXT"],
                                           font=("Segoe UI", 10, "bold"))
        self.readable_len_label.pack(side="right")
        self._reg_label(self.readable_len_label, "text")

        self.readable_slider = ttk.Scale(self.readable_panel, from_=6, to=12,
                                         variable=self.length_var, orient="horizontal",
                                         command=self._on_readable_slider)
        self.readable_slider.pack(fill="x", padx=20, pady=(0, 16))

        rd_desc = tk.Label(self.readable_panel,
                 text="Generates pronounceable, easy-to-say passwords using alternating consonants and vowels.",
                 bg=t["CARD"], fg=t["SUBTEXT"], font=("Segoe UI", 9), wraplength=600,
                 justify="left")
        rd_desc.pack(anchor="w", padx=20, pady=(0, 16))
        self._reg_label(rd_desc, "sub")

        bottom_pad = tk.Frame(tabs_card, bg=t["CARD"], height=8)
        bottom_pad.pack(fill="x")
        self._reg_frame(bottom_pad, "card")

        # ── Generate buttons
        btn_card = self._card(content)
        btn_row = tk.Frame(btn_card, bg=t["CARD"])
        btn_row.pack(padx=20, pady=18)
        self._reg_frame(btn_row, "card")

        self.gen_btn = tk.Button(btn_row, text="⟳  Generate Password",
                                 command=self.generate,
                                 bg=t["INDIGO"], fg="white", relief="flat",
                                 font=("Segoe UI", 10, "bold"), cursor="hand2",
                                 activebackground=t["INDIGO_HOVER"], activeforeground="white",
                                 padx=16, pady=9)
        self.gen_btn.pack(side="left")
        self._themed_buttons.append((self.gen_btn, "indigo"))

        self.batch_btn = tk.Button(btn_row, text="📋  Generate Batch (5)",
                                   command=self.generate_batch,
                                   bg=t["TEAL"], fg="white", relief="flat",
                                   font=("Segoe UI", 10, "bold"), cursor="hand2",
                                   activebackground=t["TEAL_HOVER"], activeforeground="white",
                                   padx=16, pady=9)
        self.batch_btn.pack(side="left", padx=(10, 0))
        self._themed_buttons.append((self.batch_btn, "teal"))

        self.batch_frame = tk.Frame(btn_card, bg=t["CARD"])
        self.batch_frame.pack(fill="x", padx=20, pady=(0, 16))
        self._reg_frame(self.batch_frame, "card")

        # ── History Log
        hist_card = self._card(content)

        hist_hdr = tk.Frame(hist_card, bg=t["CARD"])
        hist_hdr.pack(fill="x", padx=20, pady=(16, 8))
        self._reg_frame(hist_hdr, "card")
        hh = tk.Label(hist_hdr, text="HISTORY LOG (LAST 5)", bg=t["CARD"], fg=t["SUBTEXT"],
                     font=("Segoe UI", 8, "bold"))
        hh.pack(side="left")
        self._reg_label(hh, "sub")
        self.clear_lbl = tk.Label(hist_hdr, text="CLEAR LOG", bg=t["CARD"], fg=t["DANGER"],
                                  font=("Segoe UI", 8, "bold"), cursor="hand2")
        self.clear_lbl.pack(side="right")
        self.clear_lbl.bind("<Button-1>", lambda e: self.clear_history())
        self._reg_frame(self.clear_lbl, "card")

        self.history_frame = tk.Frame(hist_card, bg=t["CARD"])
        self.history_frame.pack(fill="x", padx=20, pady=(0, 16))
        self._reg_frame(self.history_frame, "card")

        # ── Footer
        self.foot = tk.Frame(self.root, bg=t["CARD"], pady=8)
        self.foot.pack(fill="x", side="bottom")
        self._reg_frame(self.foot, "card")
        self.foot_lbl = tk.Label(self.foot,
                 text="Powered by Python secrets module  |  Cryptographically Secure",
                 bg=t["CARD"], fg=t["SUBTEXT"],
                 font=("Segoe UI", 8))
        self.foot_lbl.pack()
        self._reg_label(self.foot_lbl, "sub")

        self._set_mode("standard")
        self._apply_progressbar_style()

    # ── small UI registries / helpers ───────────────────────────────────────

    def _reg_frame(self, widget, role):
        self._themed_frames.append((widget, role))

    def _reg_label(self, widget, role):
        self._themed_labels.append((widget, role))
        return widget

    def _card(self, parent):
        t = self.theme
        wrap = tk.Frame(parent, bg=t["BORDER"])
        wrap.pack(fill="x", pady=(0, 14))
        inner = tk.Frame(wrap, bg=t["CARD"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        self._reg_frame(wrap, "border_line")
        self._reg_frame(inner, "card")
        return inner

    def _stat_box(self, parent, label, value, col):
        t = self.theme
        parent.columnconfigure(col, weight=1)
        box = tk.Frame(parent, bg=t["ENTRY_BG"], padx=14, pady=10,
                       highlightbackground=t["BORDER"], highlightthickness=1)
        box.grid(row=0, column=col, sticky="ew", padx=(0, 10) if col == 0 else 0)
        self._reg_frame(box, "stat")
        lbl = tk.Label(box, text=label, bg=t["ENTRY_BG"], fg=t["SUBTEXT"],
                       font=("Segoe UI", 8, "bold"))
        lbl.pack()
        self._reg_frame(lbl, "stat")
        val = tk.Label(box, text=value, bg=t["ENTRY_BG"], fg=t["TEXT"],
                       font=("Segoe UI", 13, "bold"))
        val.pack(pady=(2, 0))
        self._reg_frame(val, "stat_value")
        return val

    def _toggle_box(self, parent, title, sub, var, row, col):
        t = self.theme
        box = tk.Frame(parent, bg=t["CARD"], highlightthickness=1,
                       highlightbackground=t["BORDER"], cursor="hand2")
        box.grid(row=row, column=col, sticky="ew", padx=4, pady=4, ipady=4)

        inner = tk.Frame(box, bg=t["CARD"])
        inner.pack(fill="x", padx=12, pady=8)

        left = tk.Frame(inner, bg=t["CARD"])
        left.pack(side="left", fill="x", expand=True)
        title_lbl = tk.Label(left, text=title, bg=t["CARD"], fg=t["TEXT"],
                 font=("Segoe UI", 9, "bold"))
        title_lbl.pack(anchor="w")
        sub_lbl = tk.Label(left, text=sub, bg=t["CARD"], fg=t["SUBTEXT"],
                 font=("Segoe UI", 8))
        sub_lbl.pack(anchor="w")

        dot = tk.Label(inner, text="●", bg=t["CARD"],
                       fg=t["TEAL"] if var.get() else t["DOT_OFF"],
                       font=("Segoe UI", 13))
        dot.pack(side="right")

        meta = {
            "box": box, "inner": inner, "left": left, "dot": dot,
            "title_lbl": title_lbl, "sub_lbl": sub_lbl, "var": var
        }

        def refresh():
            tt = self.theme
            on = var.get()
            box_bg = tt["TEAL_BG"] if on else tt["CARD"]
            box.configure(highlightbackground=tt["TEAL"] if on else tt["BORDER"], bg=box_bg)
            inner.configure(bg=box_bg)
            left.configure(bg=box_bg)
            title_lbl.configure(bg=box_bg, fg=tt["TEXT"])
            sub_lbl.configure(bg=box_bg, fg=tt["SUBTEXT"])
            dot.configure(bg=box_bg, fg=tt["TEAL"] if on else tt["DOT_OFF"])

        def toggle(_e=None):
            var.set(not var.get())
            refresh()
            self.generate()

        for w in (box, inner, left, dot, title_lbl, sub_lbl):
            w.bind("<Button-1>", toggle)

        meta["refresh"] = refresh
        refresh()
        return meta

    def _apply_progressbar_style(self):
        t = self.theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure("custom.Horizontal.TProgressbar",
                        troughcolor=t["TROUGH"], thickness=10)

    # ── Mode switching ───────────────────────────────────────────────────────

    def _set_mode(self, mode):
        t = self.theme
        self.mode_var.set(mode)
        for key, btn in self.tab_buttons.items():
            if key == mode:
                btn.configure(fg=t["TEAL"])
            else:
                btn.configure(fg=t["SUBTEXT"])

        for panel in (self.standard_panel, self.readable_panel):
            panel.pack_forget()

        if mode == "standard":
            self.standard_panel.pack(fill="x")
        elif mode == "readable":
            self.readable_panel.pack(fill="x")

        self.generate()

    # ── Slider callbacks ─────────────────────────────────────────────────────

    def _on_slider(self, val):
        v = int(float(val))
        self.len_label.config(text=f"{v} chars")
        self.generate()

    def _on_readable_slider(self, val):
        v = int(float(val))
        self.readable_len_label.config(text=f"{v} chars")
        self.generate()

    # ── Core logic ───────────────────────────────────────────────────────────

    def _get_charset(self):
        return build_charset(
            self.use_upper.get(), self.use_lower.get(),
            self.use_digits.get(), self.use_symbols.get()
        )

    def _make_one_password(self):
        mode = self.mode_var.get()

        if mode == "standard":
            charset = self._get_charset()
            length = int(self.length_var.get())
            if not charset:
                return None, 0
            pwd = generate_password(length, charset)
            entropy = calculate_entropy(length, len(charset))
            return pwd, entropy

        elif mode == "readable":
            length = int(self.length_var.get())
            pwd = generate_readable(length)
            entropy = calculate_entropy(length, 31)
            return pwd, entropy

        return None, 0

    def generate(self, *_):
        t = self.theme
        pwd, entropy = self._make_one_password()

        if not pwd:
            self.password_var.set("⚠  Select at least one character type")
            self.strength_label.config(text="No charset!", fg=t["DANGER"])
            self.strength_bar["value"] = 0
            self.stat_entropy.config(text="0 bits")
            self.stat_crack.config(text="—")
            return

        self.password_var.set(pwd)

        label, color, pct = get_strength(entropy)
        crack_time = estimate_crack_time(entropy)

        style = ttk.Style()
        style.configure("custom.Horizontal.TProgressbar",
                        troughcolor=t["TROUGH"], background=color, thickness=10)
        self.strength_bar.config(style="custom.Horizontal.TProgressbar", value=pct)
        self.strength_label.config(text=label.upper(), fg=color)

        self.stat_entropy.config(text=f"{entropy} bits")
        self.stat_crack.config(text=crack_time)

        self._add_history(pwd, entropy)

        for w in self.batch_frame.winfo_children():
            w.destroy()

    def copy_password(self):
        pwd = self.password_var.get()
        if not pwd or pwd.startswith("⚠"):
            return
        if CLIPBOARD_AVAILABLE:
            pyperclip.copy(pwd)
        else:
            self.root.clipboard_clear()
            self.root.clipboard_append(pwd)

    def generate_batch(self, qty=5):
        t = self.theme
        for w in self.batch_frame.winfo_children():
            w.destroy()

        results = []
        for _ in range(qty):
            pwd, entropy = self._make_one_password()
            if pwd:
                results.append((pwd, entropy))

        if not results:
            lbl = tk.Label(self.batch_frame, text="⚠  No characters selected.",
                     bg=t["CARD"], fg=t["DANGER"])
            lbl.pack(anchor="w", pady=(8, 0))
            return

        hdr = tk.Label(self.batch_frame, text=f"Generated {len(results)} password(s) — click to copy:",
                 bg=t["CARD"], fg=t["SUBTEXT"],
                 font=("Segoe UI", 9))
        hdr.pack(anchor="w", pady=(8, 6))

        for i, (pwd, entropy) in enumerate(results):
            row = tk.Frame(self.batch_frame, bg=t["ENTRY_BG"], pady=6, padx=10,
                           highlightbackground=t["BORDER"], highlightthickness=1)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{i+1}.", bg=t["ENTRY_BG"], fg=t["SUBTEXT"],
                     font=("Segoe UI", 9), width=3).pack(side="left")
            lbl = tk.Label(row, text=pwd, bg=t["ENTRY_BG"], fg=t["TEXT"],
                           font=("Consolas", 11), cursor="hand2")
            lbl.pack(side="left", padx=6)

            def on_click(p=pwd, r=row):
                if CLIPBOARD_AVAILABLE:
                    pyperclip.copy(p)
                else:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(p)
                r.config(bg=self.theme["TEAL_BG"])
                self.root.after(700, lambda: r.config(bg=self.theme["ENTRY_BG"]))

            row.bind("<Button-1>", lambda e, fn=on_click: fn())
            lbl.bind("<Button-1>", lambda e, fn=on_click: fn())
            self._add_history(pwd, entropy)

    # ── History log ──────────────────────────────────────────────────────────

    def _add_history(self, pwd, entropy):
        timestamp = datetime.datetime.now().strftime("%I:%M:%S %p").lstrip("0")
        self.history.insert(0, {"pwd": pwd, "time": timestamp, "entropy": entropy})
        self.history = self.history[:5]
        self._render_history()

    def _render_history(self):
        t = self.theme
        for w in self.history_frame.winfo_children():
            w.destroy()

        if not self.history:
            tk.Label(self.history_frame, text="No passwords generated yet.",
                     bg=t["CARD"], fg=t["SUBTEXT"],
                     font=("Segoe UI", 9)).pack(anchor="w")
            return

        for entry in self.history:
            row = tk.Frame(self.history_frame, bg=t["ENTRY_BG"], padx=14, pady=8,
                           highlightbackground=t["BORDER"], highlightthickness=1)
            row.pack(fill="x", pady=3)

            left = tk.Frame(row, bg=t["ENTRY_BG"])
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text=entry["pwd"], bg=t["ENTRY_BG"], fg=t["TEXT"],
                     font=("Consolas", 11)).pack(anchor="w")
            tk.Label(left, text=f"{entry['time']}  •  {entry['entropy']} bits entropy",
                     bg=t["ENTRY_BG"], fg=t["SUBTEXT"],
                     font=("Segoe UI", 8)).pack(anchor="w")

            copy_btn = tk.Label(row, text="⎘", bg=t["ENTRY_BG"], fg=t["TEAL"],
                                font=("Segoe UI", 13), cursor="hand2")
            copy_btn.pack(side="right")

            def on_copy(p=entry["pwd"], r=row):
                if CLIPBOARD_AVAILABLE:
                    pyperclip.copy(p)
                else:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(p)
                r.config(bg=self.theme["TEAL_BG"])
                self.root.after(700, lambda: r.config(bg=self.theme["ENTRY_BG"]))

            copy_btn.bind("<Button-1>", lambda e, fn=on_copy: fn())

    def clear_history(self):
        self.history = []
        self._render_history()

    # ── Theme switching ──────────────────────────────────────────────────────

    def toggle_theme(self):
        # Flip theme
        if self.theme_name == "light":
            self.theme_name = "dark"
            self.theme = DARK_THEME
        else:
            self.theme_name = "light"
            self.theme = LIGHT_THEME

        # Preserve state that should survive a theme switch
        saved_history = self.history
        saved_mode = self.mode_var.get()
        saved_length = self.length_var.get()
        saved_upper = self.use_upper.get()
        saved_lower = self.use_lower.get()
        saved_digits = self.use_digits.get()
        saved_symbols = self.use_symbols.get()

        # Destroy everything and rebuild the whole UI fresh with the new theme.
        # This is far more reliable than manually re-coloring dozens of widgets,
        # since nothing can be "missed" — every widget is simply recreated.
        for child in self.root.winfo_children():
            child.destroy()

        # Restore state onto (fresh) variables
        self.mode_var.set(saved_mode)
        self.length_var.set(saved_length)
        self.use_upper.set(saved_upper)
        self.use_lower.set(saved_lower)
        self.use_digits.set(saved_digits)
        self.use_symbols.set(saved_symbols)
        self.history = saved_history

        # Reset registries (old widgets are gone)
        self._themed_frames = []
        self._themed_labels = []
        self._themed_buttons = []

        self._build_ui()
        self.generate()


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
